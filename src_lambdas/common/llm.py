import re
import json
from botocore import retries
import retry
import logging
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def format_result(content, type='json'):
    if type == 'json':
        pattern = r'(?P<quote>["\'`]{3})json\s*(?P<json>(\{.*?\}|\[.*?\]))\s*(?P=quote)'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        if matches:
            json_str = matches[-1].group("json")
            return json.loads(json_str)
        else:
            return json.loads(content)
    elif type == 'markdown':
        pattern = r'(?P<quote>["\'`]{3})markdown\s+(.*?)(?P=quote)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(2)
        else:
            return content


@retry.retry(tries=3)
def invoke_model(client, model_id, prompt, max_tokens=20000, attachment=None, temperature=0.9, format=''):
    if model_id.find('mistral') != -1:
        payload = {
            "messages" : [
                {
                    "role" : "user",
                    "content" : [
                        {
                            "text": prompt,
                            "type": "text"
                        }
                    ]
                }
            ],
            "max_tokens" : max_tokens,
            "temperature": temperature
        }
        if attachment:
            payload['messages'][0]['content'].append({
                "type" : "image_url",
                "image_url" : {
                    "url" : f"data:image/png;base64,{attachment}"
                }
            })
        body = json.dumps(payload)
        response = client.invoke_model(
            modelId=model_id,
            body=body
        )
        response_body = json.loads(response['body'].read())
        result_text = response_body['choices'][0]['message']['content']
        LOGGER.info(f"result_text: {result_text}")
        if format:
            return format_result(result_text, format)
        else:
            return result_text
    elif model_id.find('claude') != -1:
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        if attachment:
            payload['messages'][0]['content'].insert(0, {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": attachment
                }
            })
        response = client.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(payload)
        )

        response_body = json.loads(response['body'].read())
        response_content = response_body.pop('content')
        result_text = response_content[0]['text']
        LOGGER.info(f"result_text: {result_text}")
        if format:
            return format_result(result_text, format)
        else:
            return result_text
    elif model_id.find('deepseek') != -1:
        # DEEPSEEK invoke_model does not return the text response and reasoning process in one block text!!!
        # # Embed the prompt in DeepSeek-R1's instruction format.
        # formatted_prompt = f"""
        # <｜begin▁of▁sentence｜><｜User｜>{prompt}<｜Assistant｜><think>\n
        # """

        # if attachment:
        #     raise Exception('deepseek R1 is none multi-model, could not input attachment.')

        # body = json.dumps({
        #     "prompt": formatted_prompt,
        #     "max_tokens": max_tokens,
        #     "temperature": 0.5,
        #     "top_p": 0.9,
        # })
        # response = client.invoke_model(modelId=model_id, body=body)
        # model_response = json.loads(response["body"].read())
        # choices = model_response["choices"]
        # return choices[0]['text']

        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": 'user',
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                'maxTokens': max_tokens,
                'temperature': temperature
            }
        )
        response_content = response['output']['message'].pop('content')
        result_text = response_content[0]['text']
        LOGGER.info(f"result_text: {result_text}")
        if format:
            return format_result(result_text, format)
        else:
            return result_text
    elif model_id.find('llama') != -1:
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        if attachment:
            payload['messages'][0]['content'].insert(0, {
                "image": {
                    "format": attachment[1],
                    "source": {
                        "bytes": attachment[0]
                    }
                }
            })

        response = client.converse(
            modelId=model_id,
            messages=payload["messages"],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text


def classify_rfp_requirement(client, model_id, chunk: str) -> dict:
    """
    Uses a Bedrock LLM to analyze a text chunk and classify it as a requirement.

    Args:
        client: The boto3 bedrock-runtime client.
        model_id: The ID of the model to use (e.g., Claude 3 Sonnet).
        chunk: The text chunk to analyze.

    Returns:
        A dictionary containing the classification.
    """
    prompt = f"""
Human: You are a compliance analyst. Your task is to analyze the following text from a Request for Proposal (RFP) and determine two things:
1.  Is this text a requirement that a vendor must fulfill?
2.  If it is a requirement, classify its type. The classification should be based on how a vendor must demonstrate compliance.

The classifications are:
- 'Response-Based': The requirement explicitly asks the vendor to provide a written response, description, plan, or proposal within their RFP submission. Keywords often include "describe", "propose", "provide a plan", "explain".
- 'Action-Based': The requirement obligates the vendor to perform an action, adhere to a standard, or possess a capability. Compliance is demonstrated by doing something, not just writing about it. Keywords often include "shall", "must", "will provide".

Analyze the following text:
<text>
{chunk}
</text>

Respond *only* with a valid JSON object with two keys: "is_requirement" (boolean) and "classification" (string, which must be one of "Response-Based", "Action-Based", or "N/A").
Assistant:
"""
    try:
        # We expect the model to return a JSON string.
        response_text = invoke_model(client, model_id, prompt, max_tokens=1000, temperature=0.1)
        return format_result(response_text)
    except Exception as e:
        print(f"Error during requirement classification: {e}")
        # In case of model error or malformed JSON, return a default error state.
        return {
            "is_requirement": False,
            "classification": "Error"
        }

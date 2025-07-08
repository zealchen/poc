import logging
import gradio as gr
import boto3
import base64
import json
import time
from mangum import Mangum
from fastapi import FastAPI
from PIL import Image
import pandas as pd
import uuid
import os
import sys
import re
from threading import Thread

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

JOB_STATUS_TABLE = os.environ.get("JOB_STATUS_TABLE", 'TimecardStack-JobStatusTable044F2BF7-3P8MQT4XW1RX')
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(JOB_STATUS_TABLE) if JOB_STATUS_TABLE else None


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

def analyze_image_background(image_path, job_id):
    LOGGER.info(f"Starting analyze_image for: {image_path}")
    
    if table:
        table.put_item(Item={"job_id": job_id, "status": "running"})

    try:
        with Image.open(image_path) as img:
            image_format = img.format.lower()
            if image_format not in ['jpeg', 'png', 'gif', 'webp']:
                raise ValueError(f"Unsupported image format: {image_format}")

            media_type = f"image/{image_format}"

            with open(image_path, "rb") as image_file:
                # encoded_string = base64.b64encode(image_file.read()).decode()
                encoded_string = image_file.read()
        LOGGER.info("Image processed and encoded successfully.")
    except Exception as e:
        LOGGER.error(f"Error processing image: {e}")
        if table:
            table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Error processing image: {e}"})
        return

    prompt = f"""Please extract all records and total amount from the attached timecard image. For each record, provide the following fields firstly:
    - ACCT NO
    - JOB NO
    - QUANTITY
    - RATE
    - HOURS
    - AMOUNT
    - DESCRIPTION OF WORK
    - EMPLOYEE NAME
    - HIRE DATE
    - SHIFT
    - MO_DAY_YR
    - COST CENTER
    - CLOCK

    If a field is not present, leave it blank.
    Then double check the correctness of the hours and amount field with the total hours and amount data you extract from the image.
    Make sure the data in each column could sum up to the total hours and amount.
    
    Finally, format the output as a JSON object with two keys: "records" and "totals".
    The "records" key should contain a JSON array of objects, where each object represents a single record.
    The "totals" key should contain a JSON object with the following keys: "Total Hours", "Total Amount", "Corrections".
    *BE SURE* all the values you output is extracted from the image, not by your assumption.
    For example:
    ```json
    {{
        "records": [
            {{
                "ACCT NO": "123",
                "JOB NO": "456",
                ...
            }},
            {{
                "ACCT NO": "789",
                "JOB NO": "101",
                ...
            }}
        ],
        "totals": {{
            "Total Hours": "",
            "Total Amount": "",
            "Corrections": ""
        }}
    }}
    ```
    """

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_string
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        result = invoke_llama4_scout(encoded_string, prompt)
        data = format_result(result)
        records = data.get("records", [])
        totals = data.get("totals", {})
        
        df = pd.DataFrame(records)
        totals_df = pd.DataFrame([totals])

        LOGGER.info(f"DataFrame created: {df}")
        LOGGER.info(f"Totals DataFrame created: {totals_df}")

        if table:
            table.put_item(Item={"job_id": job_id, "status": "success", "result": df.to_json(), "totals_result": totals_df.to_json()})
    except json.JSONDecodeError as e:
        LOGGER.error(f"Error decoding JSON from extracted text: {e}")
        if table:
            table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Error decoding JSON from extracted text: {e}"})
     
     
    # bedrock = get_bedrock_client()
    # try:
    #     response = bedrock.invoke_model(
    #         body=json.dumps(request_body),
    #         modelId="arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0",
    #         accept="application/json",
    #         contentType="application/json"
    #     )

    #     response_body = json.loads(response.get("body").read())
    #     LOGGER.info(f"Bedrock Response Body: {response_body}")
        
    #     if 'error' in response_body:
    #         error_message = response_body['error']
    #         LOGGER.error(f"Bedrock API Error: {error_message}")
    #         if table:
    #             table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Bedrock API Error: {error_message}"})
    #         return

    #     try:
    #         data = format_result(response_body['content'][0]['text'])
    #         df = pd.DataFrame(data)
    #         LOGGER.info(f"DataFrame created: {df}")
    #         if table:
    #             table.put_item(Item={"job_id": job_id, "status": "success", "result": df.to_json()})
    #     except json.JSONDecodeError as e:
    #         LOGGER.error(f"Error decoding JSON from extracted text: {e}")
    #         if table:
    #             table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Error decoding JSON from extracted text: {e}"})

    # except (json.JSONDecodeError, IndexError, KeyError) as e:
    #     LOGGER.error(f"Error parsing Bedrock response: {e}")
    #     if table:
    #         table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Error parsing Bedrock response: {e}"})
    # except Exception as e:
    #     LOGGER.error(f"An unexpected error occurred: {e}")
    #     if table:
    #         table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"An unexpected error occurred: {e}"})


def invoke_llama4_scout(image_data, prompt):

    # Construct the request body
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": "png",
                            "source": {
                                "bytes": image_data
                            }
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        # Invoke the model using the Converse API
        bedrock = get_bedrock_client()
        response = bedrock.converse(
            modelId="arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.meta.llama4-scout-17b-instruct-v1:0",
            messages=request_body["messages"],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.6,
                "topP": 0.9
            }
        )

        # Extract and print the response text
        response_text = response["output"]["message"]["content"][0]["text"]
        print("Model response:")
        print(response_text)
        return response_text
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        exit(1)


def start_analysis(image_path, job_id):
    LOGGER.info(f"Starting analysis for image_path: {image_path}")
    if image_path is None:
        return None, None, None, None, False, ''
    
    if job_id:
        return gr.update(), gr.update(), gr.update(), job_id, True, ''

    job_id = str(uuid.uuid4())
    thread = Thread(target=analyze_image_background, args=(image_path, job_id))
    thread.start()
    if not os.environ.get('RUN_IN_LAMBDA'):
        while True:
            time.sleep(1)
            o1, o2, o3, is_running, job_id = get_analysis_status(job_id, True)
            if not is_running:
                return o1, o2, o3, job_id, is_running, ''
    else:
        return None, None, None, job_id, True, ''

def get_analysis_status(job_id, is_running):
    LOGGER.info(f"Getting analysis status for job_id: {job_id}, is_running: {is_running}")
    if not is_running or job_id is None or not table:
        return gr.update(), gr.update(), gr.update(), False, job_id

    try:
        response = table.get_item(Key={"job_id": job_id})
        item = response.get("Item")
    except Exception as e:
        LOGGER.error(f"Error getting item from DynamoDB: {e}")
        item = None

    if not item:
        return gr.update(), gr.update(), gr.update(), True, job_id

    status = item.get("status")
    LOGGER.info(f"Analysis status for job_id: {job_id}, status: {status}")

    if status == "running":
        return gr.update(), gr.update(), gr.update(), True, job_id
    elif status == "success":
        df = pd.read_json(item.get("result"))
        totals_df = pd.read_json(item.get("totals_result"))
        LOGGER.info(f"return success, job_id: {job_id}, result: {item.get('result')}")
        job_id = ''
        return df, pd.DataFrame(columns=df.columns), totals_df, False, job_id
    elif status == "failed":
        failed_reason = item.get("failed_reason", "Analysis Failed")
        job_id = ''
        return gr.update(), gr.update(), gr.update(), False, job_id

def stage_selected_record(staging_df, extracted_df, index):
    LOGGER.info(f'On stage_selected_record!!!\n {staging_df}\n{extracted_df} \n{index}')
    if not index:
        return staging_df
    record = extracted_df.iloc[index[0]]
    staging_df.loc[len(staging_df)] = record
    LOGGER.info(f'staging_df: {staging_df}')
    return staging_df

def delete_from_staging(df, index):
    if not index:
        return df
    df = df.drop(index=index[0]).reset_index(drop=True)
    return df

def submit_all(df):
    return "Submission successful!"

def get_bedrock_client():
    return boto3.client(service_name="bedrock-runtime")

def create_gradio_app():
    with gr.Blocks() as demo:
        gr.Markdown("## Timecard Submission")
        
        job_id = gr.State(None)
        is_running = gr.State(False)
        selected_extracted_index = gr.State(None)
        selected_staging_index = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(type="filepath", label="Upload Timecard")
                analyze_button = gr.Button("Analyze")
        
        gr.Markdown("### Extracted Data (Select a record to stage)")
        extracted_table = gr.Dataframe(
            headers=["ACCT NO", "JOB NO", "QUANTITY", "RATE", "HOURS", "AMOUNT", "DESCRIPTION OF WORK", "EMPLOYEE NAME", "HIRE DATE", "SHIFT", "MO_DAY_YR", "COST CENTER", "CLOCK"],
            datatype=["str" for _ in range(13)],
            interactive=True
        )
        gr.Markdown("### Totals")
        totals_table = gr.Dataframe(
            headers=["Total Hours", "Total Amount", "Corrections"],
            datatype=["str", "str", "str"],
            interactive=False
        )
        with gr.Row():
            stage_selected_button = gr.Button("Stage Selected Record")

        gr.Markdown("### Staging for Submission")
        staging_table = gr.Dataframe(
            headers=["ACCT NO", "JOB NO", "QUANTITY", "RATE", "HOURS", "AMOUNT", "DESCRIPTION OF WORK", "EMPLOYEE NAME", "HIRE DATE", "SHIFT", "MO_DAY_YR", "COST CENTER", "CLOCK"],
            datatype=["str" for _ in range(13)],
            interactive=True
        )
        with gr.Row():
            delete_from_staging_button = gr.Button("Delete from Staging")
            submit_all_button = gr.Button("Submit All")
        submission_status = gr.Label()
        
        analyze_button.click(start_analysis, inputs=[image_input, job_id], outputs=[extracted_table, staging_table, totals_table, job_id, is_running, submission_status])
        if os.environ.get('RUN_IN_LAMBDA'):
            demo.load(get_analysis_status, inputs=[job_id, is_running], outputs=[extracted_table, staging_table, totals_table, is_running, job_id], every=1)

        def on_select(evt: gr.SelectData):
            LOGGER.info(f'evt: {evt}')
            return evt.index

        # Event handlers for row selection
        extracted_table.select(on_select, inputs=[], outputs=selected_extracted_index)
        staging_table.select(on_select, inputs=[], outputs=selected_staging_index)

        # Button click handlers
        stage_selected_button.click(stage_selected_record, inputs=[staging_table, extracted_table, selected_extracted_index], outputs=staging_table)
        delete_from_staging_button.click(delete_from_staging, inputs=[staging_table, selected_staging_index], outputs=staging_table)
        submit_all_button.click(submit_all, inputs=staging_table, outputs=submission_status)
    return demo

gradio_app = create_gradio_app()
gradio_app.queue(default_concurrency_limit=1)  # 限制并发
gradio_app.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
    share=False,
    debug=False,
    show_error=True,
    quiet=False,
    prevent_thread_lock=True,  # 防止线程锁定
    inbrowser=False,
    max_threads=1  # 限制线程数
)
app = gr.mount_gradio_app(FastAPI(), gradio_app, path="/")
handler = Mangum(
    app, 
    lifespan="off",
    api_gateway_base_path="/",
    text_mime_types=[
        "application/json",
        "application/javascript",
        "application/xml",
        "application/vnd.api+json",
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "text/xml"
    ]
)

if __name__ == "__main__":
    gradio_app.launch(quiet=False, debug=True)

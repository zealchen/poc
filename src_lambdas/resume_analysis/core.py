import re
import time
import boto3
import json
import logging
from typing import Optional, Tuple
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


PROMPT_JD = """Human: You are a Job Description Summarizer. Your task is to analyze a job posting and extract requirements based on the following categories:

## Technical Requirements
# RequiredCriteria
These are the must-have qualifications. Candidates must meet all of these to be considered. Failing to meet even one likely means disqualification.

## NiceToHave
These are preferred but not mandatory. They describe what an ideal candidate might bring beyond the basics.

## Bonus
These are extra qualifications or traits that are not expected but can help a candidate stand out. Often reflects alignment with the company’s mission, values, or future initiatives.

List each item as a bullet point.

# Non-Technical Requirements
Included but limited to the following items.

1. Work location (e.g., New York, Remote, etc.)
2. Work type (e.g., Onsite, Remote, Hybrid)
3. Legal status (e.g., US Citizen, Green Card holder, Work Authorization required)
4. Certification (e.g., AWS Certified Solutions Architect, PMP)
5. Minimum education level (e.g., Bachelor’s degree in Computer Science)

Output Rules:
1. Output is in JSON format.
2. Be specific and concise.
3. If a category has no relevant information, you may omit it.

Output Example:
{
    "Technical_Requirements": {
        "Required_Criteria": [],
        "NiceToHave": [],
        "Bonus": []
    },
    "Non_Technical_Requirements": {
        "Work_Location": "",
        "Work_Type": "",
        "Legal_Status": "",
        "Certification": "",
        "Minimum_Education_Level", "",
        "...", ""
    }
}


The input job description is:
{{job_description}}

Assistant:
"""

PROMPT_RESUME = """Human: Evaluate the degree of match between the resume and a given job description. 
Your response shall be yes, no, partial against each item of the Technical Requirements part. 
Your response shall be yes, no, not_mention against each item of the Non-Technical Requirements part. 
You shall include a To_Clarify that list all the requirements job seeker didn't mention regarding the RequiredCriteria and Non-Technical Requirements.

Output Rules:
1. Output is in JSON format.
2. Be specific and concise.

Output Example:
{
    "Technical_Requirements": {
        "Required_Criteria": [
            {
                "desc": "requirement description",
                "result": {
                    "match": "yes, or no, or partial",
                    "rationale": ""
                }
            }
        ],
        "NiceToHave": [
            {
                "desc": "requirement description",
                "result": {
                    "match": "yes, or no, or partial",
                    "rationale": ""
                }
            }
        ],
        "Bonus": [
            {
                "desc": "requirement description",
                "result": {
                    "match": "yes, or no, or partial",
                    "rationale": ""
                }
            }
        ]
    },
    "Non_Technical_Requirements": {
        "Work_Location": {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        },
        "Work_Type": {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        },
        "Legal_Status": {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        },
        "Certification": {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        },
        "Minimum_Education_Level", {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        },
        "...":  {
            "desc": "requirement description",
            "result": {
                "match": "yes, or no, or not_mention",
                "rationale": ""
            }
        }
    }
}


Job Description is:
{{job_description}}

My resume is:
{{resume}}

ASSISTANT:
"""


class LlmChatManager():
    def __init__(self):
        pass
    
    def build_jd_analysis_prompt(self, job_description):
        return PROMPT_JD.replace('{{job_description}}', job_description)
    
    def build_resume_analysis_prompt(self, job_description, resume):
        return PROMPT_RESUME.replace('{{job_description}}', job_description).replace('{{resume}}', resume)
    
    
    def extract_json_response(self, text_response):
        match = re.search(r'```json\s*(.*?)\s*```', text_response, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return text_response


def claude_37(prompt, client):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 20000,
        "temperature": 0.5,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    modelARN_Claude35 = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0'
    modelARN = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    response = client.invoke_model(
        modelId=modelARN,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


def deepseek(prompt, client):
    modelARN = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.deepseek.r1-v1:0'
    response = client.converse(
        modelId=modelARN,
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
            'maxTokens': 20480
        }
    )
    return response['output']['message']['content'][0]['text']


def calc_score(jd_summary, resume_summary) -> Optional[Tuple[int, int, int]]:
    jd_req_required = jd_summary.get('Technical_Requirements', {}).get('Required_Criteria', [])
    resume_req_required = resume_summary.get('Technical_Requirements', {}).get('Required_Criteria', [])
    if len(jd_req_required) == 0 or len(resume_req_required) == 0 or len(jd_req_required) != len(resume_req_required):
        LOGGER.error('invalid llm response: jd_summary: %s \n resume_summary: %s', jd_summary, resume_summary)
        return None
    
    jd_req_nth = jd_summary.get('Technical_Requirements', {}).get('NiceToHave', [])
    resume_req_nth = resume_summary.get('Technical_Requirements', {}).get('NiceToHave', [])
    if len(jd_req_nth) != len(resume_req_nth):
        LOGGER.error('invalid llm response: jd_summary: %s \n resume_summary: %s', jd_summary, resume_summary)
        return None
    
    jd_req_bonus = jd_summary.get('Technical_Requirements', {}).get('Bonus', [])
    resume_req_bonus = resume_summary.get('Technical_Requirements', {}).get('Bonus', [])
    if len(jd_req_bonus) != len(resume_req_bonus):
        LOGGER.error('invalid llm response: jd_summary: %s \n resume_summary: %s', jd_summary, resume_summary)
        return None

    def calc_each(reqs, each_score):
        final_score = 0
        for item in reqs:
            match = item.get('result', {}).get('match')
            item_score = 0
            if match == 'yes':
                item_score = 1.0
            elif match == 'partial':
                item_score = 0.5
            else:
                item_score = 0
            final_score += item_score * each_score
        return int(final_score)
      

    # Required_Criteria: 80%, NiceToHave: 20%, Bonus: 10%
    each_required = 100.0 / len(resume_req_required)    
    required_score = calc_each(resume_req_required, each_required)
    if len(resume_req_nth) != 0:
        each_nth = 100.0 / len(resume_req_nth)
        nth_score = calc_each(resume_req_nth, each_nth)
    else:
        nth_score = -1
    if len(resume_req_bonus) != 0:
        each_bonus = 100.0 / len(resume_req_bonus)
        bonus_score = calc_each(resume_req_bonus, each_bonus)
    else:
        bonus_score = -1
    return (required_score, nth_score, bonus_score)


def invoke_model(prompt, model_type='claude'):
    region_name = 'us-east-1'
    session = boto3.Session(region_name=region_name)
    client = session.client('bedrock-runtime')


    while True:
        try:
            if model_type == 'claude':
                return claude_37(prompt, client)
            elif model_type == 'deepseek':
                return deepseek(prompt, client)
        except Exception as e:
            LOGGER.error('call llm failed:%s', e)
            time.sleep(30)


def resume_analyse(job_description, resume):
    chat_manager = LlmChatManager()
    # 1. Get job description analysis
    prompt_jd = chat_manager.build_jd_analysis_prompt(job_description)
    response = invoke_model(prompt_jd)
    jd_summary = json.loads(chat_manager.extract_json_response(response))
    # print(json.dumps(jd_summary, indent=4))

    # 2. Get the resume analysis
    prompt_resume = chat_manager.build_resume_analysis_prompt(json.dumps(jd_summary), resume)
    response = invoke_model(prompt_resume)
    resume_summary = json.loads(chat_manager.extract_json_response(response))
    # print(json.dumps(resume_summary, indent=4))

    result = calc_score(jd_summary, resume_summary)
    if not result:
        raise Exception('invalid score')
    else:
        required_score, nth_score, bonus_score = result
    
    resume_summary['Score'] = {
        'Required': required_score,
        'NiceToHave': nth_score,
        'Bonus': bonus_score,
    }
    return resume_summary, jd_summary
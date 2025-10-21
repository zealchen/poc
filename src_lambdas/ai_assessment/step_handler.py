import json
import os
import boto3
import requests
import logging
from common.llm import invoke_model, format_result
from common.utils import get_bedrock_client
from prompt import TEST_GENERATION, TEST_VERIFICATION
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")
SF_CLIENT = boto3.client("stepfunctions")
CLIENT = get_bedrock_client()
modelARN_DEEPSEEK_R1_V1 = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.deepseek.r1-v1:0'
modelARN_Claude37_v1 = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0'


def handler(event, context):
    LOGGER.info(f"Received event: {json.dumps(event)}")
    step_name = event.get("step_name")
    if not step_name:
        step_name = 'start_execution'

    if step_name == "start_execution":
        LOGGER.info("Starting Step Function execution")
        """
        {
            "item_id": "string",          // Unique identifier from frontend
            "subject": "string",          // One of: ["English Language Arts (ELA)", "Mathematics"]
            "grade_level": "integer",     // Grade range: 0–12
            "item_type": "string",        // One of: ["Multiple Choice", "Multiple Selec
            "callback": "string"          // callback url
        }
        """
        item_id = event.get('item_id', '')
        subject = event.get('subject', '')
        grade_level = event.get('grade_level', '')
        item_type = event.get('item_type', '')
        callback = event.get('callback', '')

        if not item_id or not subject or not grade_level or not item_type or not callable:
            msg = "Missing: " + ", ".join(k for k, v in {
                "item_id": item_id,
                "subject": subject,
                "grade_level": grade_level,
                "item_type": item_type,
                "callback": callback
            }.items() if v == '') + ' parameter.'
            return {
                "status": "failed",
                "msg": msg,
                "result": {}
            }
        try:
            response = SF_CLIENT.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps({
                    "step_name": "create_test",
                    "item_id": item_id,
                    "subject": subject,
                    "grade_level": grade_level,
                    "item_type": item_type,
                    "callback": callback
                })
            )
            return {
                "status": "running",
                "msg": 'job is running',
                "result": {
                    "job_id": response["executionArn"]
                }
            }
        except Exception as e:
            LOGGER.error(f"Error starting execution: {e}")
            return {
                "status": "failed",
                "msg": f"trigger step function failed: {e}",
                "result": {}
            }
    elif step_name == "create_test":
        LOGGER.info(f"create_test: {event}")
        try:
            subject = event.get('execution_input', {}).get('subject')
            grade_level = event.get('execution_input', {}).get('grade_level')
            item_type = event.get('execution_input', {}).get('item_type')
            prompt = TEST_GENERATION.replace('{subject}', subject).replace('{grade_level}', str(grade_level)).replace('{item_type}', item_type)
            result = format_result(invoke_model(CLIENT, modelARN_Claude37_v1, prompt))
            LOGGER.info(f'create test item: {json.dumps(result)}')
            return {
                "create_result": result
            }
        except Exception as e:
            err_msg = f'create test failed: {e}'
            LOGGER.error(err_msg)
            final_result = {
                'job_id': event.get('execution_arn'),
                'status': 'failed',
                'message': err_msg,
                'result': {}
            }
            callback = event.get('execution_input', {}).get('callback', '')
            if callback:
                do_callback(callback, final_result)
            else:
                LOGGER.warning('callback is null')
            raise e
    elif step_name == "verify_test":
        LOGGER.info(f"Verifying the test: {event}")
        err_msg = ''
        try:
            test_content = json.dumps(event.get('create_test_task_result'))
            prompt = TEST_VERIFICATION.replace('{test_content}', test_content)
            result = format_result(invoke_model(CLIENT, modelARN_DEEPSEEK_R1_V1, prompt))
            verify_result = event.get('create_test_task_result')
            verify_result.update(result)
            verify_result['item_id'] = event.get('execution_input', {}).get('item_id')
            LOGGER.info(f'verify test item: {json.dumps(verify_result)}')
            final_result = {
                'job_id': event.get('execution_arn'),
                'status': 'success',
                'message': 'success',
                'result': verify_result
            }
        except Exception as e:
            err_msg = f'verify test failed: {e}'
            LOGGER.error(err_msg)
            final_result = {
                'job_id': event.get('execution_arn'),
                'status': 'failed',
                'message': err_msg,
                'result': {}
            }
        callback = event.get('execution_input', {}).get('callback', '')
        if callback:
            do_callback(callback, final_result)
        else:
            LOGGER.warning('callback is null')


def do_callback(url, payload):
    LOGGER.info(f'do callback: {url}, payload: {json.dumps(payload)}')
    if url:
        try:
            requests.post(url, json=payload)
            LOGGER.info(f"callback({url}) succeed")
        except Exception as e:
            LOGGER.error(f"callback({url}) failed, error: {e}")

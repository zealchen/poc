import json
import os
import re
import boto3
import random
import requests
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from common.llm import invoke_model
from common.utils import get_bedrock_client
from xml_example import XML_EXAMPLE_MAP
from prompt import (
    TEST_GENERATION,
    TEST_VERIFICATION,
    PSYCHOMETRIC_VERIFICATION,
    CURRICULUM_GENERATION,
    CURRICULUM_VERIFICATION
)

# Configure logging
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Environment variables
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")
MODEL_ARN_DEEPSEEK = os.environ.get(
    "MODEL_ARN_DEEPSEEK",
    "arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.deepseek.r1-v1:0"
)
MODEL_ARN_CLAUDE = os.environ.get(
    "MODEL_ARN_CLAUDE",
    "arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
)
MAX_QUESTIONS = int(os.environ.get("MAX_QUESTIONS", "36"))
CALLBACK_TIMEOUT = int(os.environ.get("CALLBACK_TIMEOUT", "30"))

# Constants
QTI_TYPES = ['choice', 'text', 'gap_match']
VALID_SUBJECTS = ['English Language Arts (ELA)', 'Mathematics']
MIN_GRADE = 1
MAX_GRADE = 6


def get_clients():
    """Initialize AWS clients (call within handler for Lambda best practices)"""
    return {
        'sf': boto3.client('stepfunctions'),
        's3': boto3.client('s3'),
        'bedrock': get_bedrock_client()
    }


def expand_self_closing_tags(xml_str):
    """
    Replace all self-closing XML tags like:
      <tag attr="value" />
    with:
      <tag attr="value"></tag>
    """
    # 用正则匹配 <tag ... /> 的形式
    pattern = re.compile(r'<(\w[\w:-]*)([^>]*)/>')

    def replacer(match):
        tag = match.group(1)
        attrs = match.group(2).strip()
        # 保留属性并生成开闭标签
        if attrs:
            return f'<{tag} {attrs}></{tag}>'
        else:
            return f'<{tag}></{tag}>'

    return pattern.sub(replacer, xml_str)


def validate_s3_uri(uri: str) -> bool:
    """Validate S3 URI format and prevent path traversal"""
    try:
        if not uri.startswith('s3://'):
            return False
        parts = uri.replace('s3://', '').split('/', 1)
        if len(parts) != 2:
            return False
        bucket, key = parts
        # Prevent path traversal
        if '..' in key or key.startswith('/'):
            return False
        return True
    except Exception:
        return False


def validate_callback_url(url: str) -> bool:
    """Validate callback URL"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False


def handle_start_execution(event: Dict[str, Any], clients: Dict) -> Dict[str, Any]:
    """
    Start Step Functions execution for test generation.

    Expected event structure:
    {
        "item_id": str,
        "subject": str,
        "grade_level": int,
        "qti_format": str (optional),
        "curriculum_uri": str (optional),
        "number_of_questions": int (optional),
        "callback": str
    }
    """
    LOGGER.info("Starting Step Function execution")

    # Extract and validate required parameters
    item_id = event.get('item_id', '').strip()
    subject = event.get('subject', '').strip()
    grade_level = event.get('grade_level')
    callback = event.get('callback', '').strip()

    # Validate required fields
    missing_fields = []
    if not item_id:
        missing_fields.append('item_id')
    if not subject:
        missing_fields.append('subject')
    if grade_level is None:
        missing_fields.append('grade_level')
    if not callback:
        missing_fields.append('callback')

    if missing_fields:
        return {
            "status": "failed",
            "msg": f"Missing required parameters: {', '.join(missing_fields)}",
            "result": {}
        }

    # Validate subject
    if subject not in VALID_SUBJECTS:
        return {
            "status": "failed",
            "msg": f"Invalid subject. Must be one of: {', '.join(VALID_SUBJECTS)}",
            "result": {}
        }

    # Validate grade level
    try:
        grade_level = int(grade_level)
        if not (MIN_GRADE <= grade_level <= MAX_GRADE):
            return {
                "status": "failed",
                "msg": f"Grade level must be between {MIN_GRADE} and {MAX_GRADE}",
                "result": {}
            }
    except (ValueError, TypeError):
        return {
            "status": "failed",
            "msg": "Grade level must be a valid integer",
            "result": {}
        }

    # Validate callback URL
    if not validate_callback_url(callback):
        return {
            "status": "failed",
            "msg": "Invalid callback URL format",
            "result": {}
        }

    # Validate optional parameters
    qti_format = event.get('qti_format', '').strip().lower()
    if qti_format and qti_format not in QTI_TYPES:
        return {
            "status": "failed",
            "msg": f"Invalid qti_format. Must be one of: {', '.join(QTI_TYPES)}",
            "result": {}
        }

    curriculum_uri = event.get('curriculum_uri', '').strip()
    if curriculum_uri and not validate_s3_uri(curriculum_uri):
        return {
            "status": "failed",
            "msg": "Invalid curriculum_uri format. Must be a valid S3 URI (s3://bucket/key)",
            "result": {}
        }

    number_of_questions = event.get('number_of_questions')
    if number_of_questions is not None:
        try:
            number_of_questions = int(number_of_questions)
            if number_of_questions > MAX_QUESTIONS or number_of_questions < 1:
                return {
                    "status": "failed",
                    "msg": f"Number of questions must be between 1 and {MAX_QUESTIONS}",
                    "result": {}
                }
        except (ValueError, TypeError):
            return {
                "status": "failed",
                "msg": "number_of_questions must be a valid integer",
                "result": {}
            }

    # Build Step Functions input
    sf_input = {
        "step_name": "create_test",
        "item_id": item_id,
        "subject": subject,
        "grade_level": grade_level,
        "callback": callback
    }

    if curriculum_uri:
        sf_input['curriculum_uri'] = curriculum_uri
    if qti_format:
        sf_input['qti_format'] = qti_format
    if number_of_questions:
        sf_input['number_of_questions'] = number_of_questions

    # Start execution
    try:
        if not STATE_MACHINE_ARN:
            raise ValueError("STATE_MACHINE_ARN environment variable not set")

        LOGGER.info(f'Starting execution with STATE_MACHINE_ARN: {STATE_MACHINE_ARN}')
        response = clients['sf'].start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(sf_input)
        )

        return {
            "status": "running",
            "msg": "Job started successfully",
            "result": {
                "job_id": response["executionArn"]
            }
        }
    except Exception as e:
        error_msg = f"Failed to start Step Functions execution: {str(e)}"
        LOGGER.error(error_msg, exc_info=True)
        return {
            "status": "failed",
            "msg": error_msg,
            "result": {}
        }


def read_s3_object(s3_client, bucket_name: str, key: str) -> str:
    """Read object from S3 bucket"""
    try:
        LOGGER.info(f"Reading S3 object: s3://{bucket_name}/{key}")
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response["Body"].read().decode("utf-8")
        LOGGER.info(f"Successfully read {len(content)} characters from S3")
        return content
    except Exception as e:
        LOGGER.error(f"Failed to read S3 object: {str(e)}", exc_info=True)
        raise


def handle_parse_curriculum(event: Dict[str, Any], clients: Dict) -> Dict[str, Any]:
    """Parse curriculum from S3 and extract requirements"""
    LOGGER.info("Parsing curriculum")

    try:
        curriculum_uri = event.get('execution_input', {}).get('curriculum_uri')
        if not curriculum_uri:
            raise ValueError("curriculum_uri not provided")

        number_of_questions = event.get('execution_input', {}).get('number_of_questions', -1)

        LOGGER.info(f'Curriculum URI: {curriculum_uri}')

        # Convert PDF to MD if needed
        if curriculum_uri.endswith('.pdf'):
            curriculum_uri = curriculum_uri.replace('.pdf', '.md')

        # Parse S3 URI
        bucket_name, key = curriculum_uri.split('s3://', 1)[1].split('/', 1)

        # Read curriculum content
        content = read_s3_object(clients['s3'], bucket_name, key)

        # Generate curriculum structure using LLM
        prompt = CURRICULUM_GENERATION.replace('{content}', content)
        result = invoke_model(clients['bedrock'], MODEL_ARN_CLAUDE, prompt, format='json')

        # Process requirements
        requirements = []
        all_requirements = []

        for category_idx, category_item in enumerate(result):
            for req_idx, requirement_text in enumerate(category_item.get('requirements', [])):
                requirement_obj = {
                    "category_id": str(category_idx + 1),
                    "category": category_item.get('category', ''),
                    "requirement_id": f'{category_idx + 1}.{req_idx + 1}',
                    "requirement": requirement_text
                }
                all_requirements.append(requirement_obj)

                # Add to requirements list if within limit
                if number_of_questions == -1 or len(requirements) < number_of_questions:
                    requirements.append(requirement_obj)

        LOGGER.info(f"Parsed {len(all_requirements)} total requirements, "
                    f"selected {len(requirements)} for generation")

        return {
            "all_requirements": all_requirements,
            "requirements": requirements
        }
    except Exception as e:
        error_msg = f"Failed to parse curriculum: {str(e)}"
        LOGGER.error(error_msg, exc_info=True)
        raise


def handle_create_test(event: Dict[str, Any], clients: Dict) -> Dict[str, Any]:
    """Create a test item using LLM"""
    LOGGER.info("Creating test item")

    requirement = event.get('requirement', {})
    execution_input = event.get('execution_input', {})

    # Determine parameters based on whether requirement is provided
    if requirement:
        category = requirement.get('category', '')
        requirement_text = requirement.get('requirement', '')
        # Randomly select QTI format for curriculum-based generation
        qti_format = QTI_TYPES[random.randint(0, len(QTI_TYPES) - 1)]
    else:
        category = ''
        requirement_text = ''
        qti_format = execution_input.get('qti_format', '')

    subject = execution_input.get('subject', '')
    grade_level = execution_input.get('grade_level', '')

    # Build prompt with proper placeholder replacement
    prompt = TEST_GENERATION.replace('{subject}', subject)\
        .replace('{grade_level}', str(grade_level))\
        .replace('{qti_format}', qti_format)\
        .replace('{category}', category)\
        .replace('{requirement}', requirement_text)\
        .replace('{example_xlm}', XML_EXAMPLE_MAP[qti_format])

    # LOGGER.info(f'test generate prompt: {prompt}')

    # Generate test item
    LOGGER.info(f"Generating test for subject={subject}, grade={grade_level}, format={qti_format}")
    result = invoke_model(clients['bedrock'], MODEL_ARN_CLAUDE, prompt, format='json')
    result['qti_format'] = qti_format
    result['qti_xml'] = expand_self_closing_tags(result['qti_xml'])

    LOGGER.info(f'Successfully created test item: {json.dumps(result)}')

    return result


def handle_verify_test(event: Dict[str, Any], clients: Dict) -> Optional[Dict[str, Any]]:
    """Verify generated test item"""
    LOGGER.info("Verifying test item")

    test_content = event.get('create_test_task_result', {})
    requirement = event.get('requirement')
    execution_input = event.get('execution_input', {})
    subject = execution_input.get('subject', '')
    grade_level = execution_input.get('grade_level', '')

    # Verify test content
    prompt = TEST_VERIFICATION.replace('{test_content}', json.dumps(test_content))
    result = invoke_model(clients['bedrock'], MODEL_ARN_DEEPSEEK, prompt, format='json')

    # Build verification result
    verify_result = event.get('create_test_task_result', {}).copy()
    verify_result.update(result)

    prompt = PSYCHOMETRIC_VERIFICATION.replace('{subject}', subject).replace(
        "{grade_level}", str(grade_level)).replace("{qti_xml}", test_content['qti_xml'])
    result = invoke_model(clients['bedrock'], MODEL_ARN_DEEPSEEK, prompt, format='json')
    verify_result.update(result)

    LOGGER.info(f'Test verification result: {json.dumps(verify_result)}')

    # If requirement provided, verify curriculum alignment
    if requirement:
        category = requirement.get('category', '')
        requirement_text = requirement.get('requirement', '')

        prompt = CURRICULUM_VERIFICATION.replace('{test_content}', test_content['qti_xml'])\
            .replace('{category}', category)\
            .replace('{requirement}', requirement_text)

        curriculum_result = invoke_model(clients['bedrock'], MODEL_ARN_DEEPSEEK, prompt, format='json')
        verify_result.update(curriculum_result)
        verify_result['requirement'] = requirement

        return verify_result
    else:
        # No requirement - this is a standalone test, send callback
        verify_result.pop('qti_format', None)
        verify_result['item_id'] = event.get('execution_input', {}).get('item_id')

        final_result = {
            'job_id': event.get('execution_arn', ''),
            'status': 'success',
            'message': 'Test created and verified successfully',
            'result': verify_result
        }

        callback = event.get('execution_input', {}).get('callback', '')
        if callback:
            do_callback(callback, final_result)
            return final_result
        else:
            LOGGER.warning('Callback URL not provided')
            return final_result


def handle_aggregate_results(event: Dict[str, Any], clients: Dict) -> Dict[str, Any]:
    """Aggregate results from multiple test generations"""
    LOGGER.info('Aggregating results from curriculum-based generation')

    map_results = event.get('map_results', [])
    all_requirements = event.get('all_requirements', [])

    result = {
        "questions": [],
        "curriculum": []
    }

    # Build curriculum map
    curriculum_map = {}
    for item in all_requirements:
        category_id = item.get('category_id')
        requirement_id = item.get('requirement_id')

        if category_id not in curriculum_map:
            curriculum_map[category_id] = {
                'category': item.get('category', ''),
                'requirements': {}
            }

        curriculum_map[category_id]['requirements'][requirement_id] = item.get('requirement', '')

    # Process questions
    questions = []
    for map_result in map_results:
        requirement = map_result.pop('requirement', {})
        map_result['category_id'] = requirement.get('category_id')
        map_result['requirement_id'] = requirement.get('req_id', requirement.get('requirement_id'))
        questions.append(map_result)
    questions = sorted(questions, key=lambda x: x['psychology_score'])
    result['questions'] = questions

    # Build curriculum structure
    for category_id, detail in curriculum_map.items():
        curriculum_item = {
            'category_id': category_id,
            'category_name': detail['category'],
            'requirements': []
        }

        for req_id, req_text in detail['requirements'].items():
            curriculum_item['requirements'].append({
                'requirement_id': req_id,
                'desc': req_text
            })

        result['curriculum'].append(curriculum_item)
    result['item_id'] = event.get('execution_input', {}).get('item_id')

    LOGGER.info(f"Aggregated {len(result['questions'])} questions across "
                f"{len(result['curriculum'])} curriculum categories")

    # Send success callback
    final_result = {
        'job_id': event.get('execution_arn', ''),
        'status': 'success',
        'message': 'All tests created and verified successfully',
        'result': result
    }

    callback = event.get('execution_input', {}).get('callback', '')
    if callback:
        do_callback(callback, final_result)

    return result


def do_callback(url: str, payload: Dict[str, Any]) -> None:
    """Send callback to specified URL"""
    LOGGER.info(f'Sending callback to: {url}, {json.dumps(payload)}')

    if not url:
        LOGGER.warning('Callback URL is empty')
        return

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=CALLBACK_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        LOGGER.info(f"Callback to {url} succeeded with status {response.status_code}")
    except requests.exceptions.Timeout:
        LOGGER.error(f"Callback to {url} timed out after {CALLBACK_TIMEOUT}s")
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Callback to {url} failed: {str(e)}", exc_info=True)
    except Exception as e:
        LOGGER.error(f"Unexpected error during callback to {url}: {str(e)}", exc_info=True)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler"""
    LOGGER.info(f"Received event: {json.dumps(event)}")

    # Initialize clients
    clients = get_clients()

    # Determine step
    step_name = event.get("step_name", "start_execution")
    LOGGER.info(f"Processing step: {step_name}")
    if step_name == "start_execution":
        result = handle_start_execution(event, clients)
        if result.get('status') == 'failed':
            LOGGER.error(f'trigger failed: {result}')
        return result

    # Route to appropriate handler
    try:
        if step_name == 'parse_curriculum':
            return handle_parse_curriculum(event, clients)
        elif step_name == "create_test":
            return handle_create_test(event, clients)
        elif step_name == "verify_test":
            return handle_verify_test(event, clients)
        elif step_name == "aggregate_results":
            return handle_aggregate_results(event, clients)
        else:
            error_msg = f"Unknown step_name: {step_name}"
            LOGGER.error(error_msg)
            return {
                "status": "failed",
                "msg": error_msg,
                "result": {}
            }
    except Exception as e:
        error_msg = f'Failed to aggregate results: {str(e)}'
        LOGGER.error(error_msg, exc_info=True)

        # Send failure callback
        final_result = {
            'job_id': event.get('execution_arn', ''),
            'status': 'failed',
            'message': error_msg,
            'result': {}
        }

        callback = event.get('execution_input', {}).get('callback', '')
        if callback:
            do_callback(callback, final_result)
        raise e

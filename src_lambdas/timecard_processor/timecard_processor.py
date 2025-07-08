import logging
import gradio as gr
import boto3
import time
from mangum import Mangum
from fastapi import FastAPI
from PIL import Image
import pandas as pd
import uuid
import os
import sys
from threading import Thread

# Add the parent directory to the Python path for local execution
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.llm import format_result, invoke_model
from common.utils import get_bedrock_client
from prompt import TIMECARD


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
MODEL_ID = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.meta.llama4-scout-17b-instruct-v1:0'


def analyze_image_background(image_path, job_id):
    LOGGER.info(f"Starting analyze_image for: {image_path}")
    
    if table:
        table.put_item(Item={"job_id": job_id, "status": "running"})

    try:
        with Image.open(image_path) as img:
            image_format = img.format.lower()
            if image_format not in ['jpeg', 'png', 'gif', 'webp']:
                raise ValueError(f"Unsupported image format: {image_format}")

            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()
        LOGGER.info("Image processed and encoded successfully.")
    except Exception as e:
        LOGGER.error(f"Error processing image: {e}")
        if table:
            table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"Error processing image: {e}"})
        return

    try:
        result = invoke_model(get_bedrock_client(), MODEL_ID, TIMECARD, max_tokens=1024, attachment=(image_bytes, image_format), temperature=0.5)
        data = format_result(result)
        records = data.get("records", [])
        totals = data.get("totals", {})
        
        df = pd.DataFrame(records)
        totals_df = pd.DataFrame([totals])

        LOGGER.info(f"DataFrame created: {df}")
        LOGGER.info(f"Totals DataFrame created: {totals_df}")

        if table:
            table.put_item(Item={"job_id": job_id, "status": "success", "result": df.to_json(), "totals_result": totals_df.to_json()})
    except Exception as e:
        LOGGER.error(f"process timecard failed: {e}")
        if table:
            table.put_item(Item={"job_id": job_id, "status": "failed", "failed_reason": f"process timecard failed: {e}"})


def start_analysis(image_path, job_id):
    LOGGER.info(f"Starting analysis for image_path: {image_path}")
    if image_path is None:
        return None, None, None, None, False, ''
    
    if job_id:
        return gr.update(), gr.update(), gr.update(), job_id, True, ''

    job_id = str(uuid.uuid4())
    thread = Thread(target=analyze_image_background, args=(image_path, job_id))
    thread.start()
    if not os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
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
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
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
gradio_app.queue(default_concurrency_limit=1)
gradio_app.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
    share=False,
    debug=False,
    show_error=True,
    quiet=False,
    prevent_thread_lock=True,
    inbrowser=False,
    max_threads=1
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

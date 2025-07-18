import logging
import gradio as gr
import boto3
import time
import json
from mangum import Mangum
from fastapi import FastAPI
from PIL import Image
import pandas as pd
import uuid
import os
import sys
from threading import Thread
from common.llm import format_result, invoke_model
from common.utils import get_bedrock_client
from prompt import *


# Add the parent directory to the Python path for local execution
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

#JOB_STATUS_TABLE = os.environ.get("JOB_STATUS_TABLE", 'TimecardStack-JobStatusTable044F2BF7-3P8MQT4XW1RX')
#dynamodb = boto3.resource("dynamodb")
#table = dynamodb.Table(JOB_STATUS_TABLE) if JOB_STATUS_TABLE else None
#MODEL_ID = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.meta.llama4-scout-17b-instruct-v1:0'

CLIENT = get_bedrock_client()
modelARN_DEEPSEEK_R1_V1 = 'arn:aws:bedrock:us-east-1:471112955155:inference-profile/us.deepseek.r1-v1:0'


PREDEFINED_BENEFITS = []
PREDEFINED_ANALYZE = ''
PREDEFINED_TEST = ''


def extract_benefits(md_file, regenerate):
    global PREDEFINED_BENEFITS
    with open(md_file) as fp:
        content = fp.read()
        
    with open('benefits.json') as fp:
        benefits = json.load(fp)


    if not PREDEFINED_BENEFITS or regenerate:
        if regenerate or not benefits:
            t1 = time.time()
            prompt = BENEFITS_EXTRACT.replace("{content}", content)
            result = invoke_model(CLIENT, modelARN_DEEPSEEK_R1_V1, prompt, max_tokens=20000, attachment=None, temperature=0.1)
            json_result = format_result(result)
            t2 = time.time()
            print(f'benefit extract time: {int(t2 - t1)}')
            PREDEFINED_BENEFITS = json_result
        else:
            PREDEFINED_BENEFITS = benefits
    return gr.update(choices=PREDEFINED_BENEFITS, value=PREDEFINED_BENEFITS[0] if PREDEFINED_BENEFITS else None)

def analyze_benefit(md_file, selected_benefit, regenerate):
    global PREDEFINED_ANALYZE
    with open(md_file) as fp:
        content = fp.read()
        
    with open('analyze.md') as fp:
        predefined_result = fp.read()

    if not PREDEFINED_ANALYZE or regenerate:
        if regenerate or not predefined_result:
            t1 = time.time()
            prompt = ANALYZE2.replace("{content}", content).replace("{benefit}", selected_benefit)
            print(prompt)
            result = invoke_model(CLIENT, modelARN_DEEPSEEK_R1_V1, prompt, max_tokens=20000, attachment=None, temperature=0.1)
            md_result = format_result(result, type='markdown')
            t2 = time.time()
            print(f'benefit analyze time: {int(t2 - t1)}')
            PREDEFINED_ANALYZE = md_result
        else:
            PREDEFINED_ANALYZE = predefined_result
    return '', PREDEFINED_ANALYZE


def test_benefit(regenerate_test, analysis_output):
    global PREDEFINED_TEST
    # with open(md_file) as fp:
    #     content = fp.read()
        
    with open('test.md') as fp:
        predefined_result = fp.read()

    if not PREDEFINED_TEST or regenerate_test:
        if regenerate_test or not predefined_result:
            t1 = time.time()
            prompt = TEST.replace("{content}", analysis_output)
            print(prompt)
            result = invoke_model(CLIENT, modelARN_DEEPSEEK_R1_V1, prompt, max_tokens=20000, attachment=None, temperature=0.1)
            t2 = time.time()
            print(f'benefit test time: {int(t2 - t1)}')
            md_result = format_result(result, type='markdown')
            PREDEFINED_TEST = md_result
        else:
            PREDEFINED_TEST = predefined_result
    return '', PREDEFINED_TEST


def create_gradio_app():
    with gr.Blocks() as demo:
        gr.HTML("""
                <style>
                    #md-box {
                        background-color: #232326;
                        color: #f0f0f0;
                        border: 2px solid #555;
                        border-radius: 8px;
                        padding: 15px;
                        font-family: sans-serif;
                    }
                    #md-box2 {
                        background-color: #232326;
                        color: #f0f0f0;
                        border: 2px solid #555;
                        border-radius: 8px;
                        padding: 15px;
                        font-family: sans-serif;
                    }
                </style>
            """)
        md_file = gr.File(label="Upload Markdown File")
        regenerate_benefit = gr.Checkbox(label="Regenerate on Extract")
        extract_btn = gr.Button("Extract Benefit")
        benefit_choice = gr.Dropdown(label="Choose Benefit")
        regenerate_analyze = gr.Checkbox(label="Regenerate on Analyze")
        analyze_btn = gr.Button("Analyze Benefit")
        
        
        extract_btn.click(
                extract_benefits, 
                inputs=[md_file, regenerate_benefit], 
                outputs=[benefit_choice]
            )

        fake_text = gr.Text(label='')
        analysis_output = gr.Markdown(elem_id="md-box")
        analyze_btn.click(
            analyze_benefit,
            inputs=[md_file, benefit_choice, regenerate_analyze],
            outputs=[fake_text, analysis_output]
        )
        
        regenerate_test = gr.Checkbox(label="Regenerate on Test")
        test_btn = gr.Button("Test Benefit")
        fake_text2 = gr.Text(label='')
        test_output = gr.Markdown(elem_id="md-box2")
        
        test_btn.click(
            test_benefit,
            inputs=[regenerate_test, analysis_output],
            outputs=[fake_text2, test_output]
        )
    return demo


gradio_app = create_gradio_app()
gradio_app.queue(default_concurrency_limit=1)
gradio_app.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7789)),
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
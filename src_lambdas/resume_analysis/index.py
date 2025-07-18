import logging
import gradio as gr
from mangum import Mangum
from fastapi import FastAPI
from PIL import Image
import pandas as pd
import uuid
import os
import sys
from threading import Thread
import json
import gradio as gr
from core import resume_analyse

# Add the parent directory to the Python path for local execution
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.llm import format_result, invoke_model
from common.utils import get_bedrock_client


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
def load_job_description(file):
    """Load job description from uploaded file"""
    if file is None:
        return "No file uploaded"
    
    try:
        with open(file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def load_resume(file):
    """Load resume from uploaded file"""
    if file is None:
        return "No file uploaded"
    
    try:
        with open(file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def analyze_job_resume(job_description, resume):
    """
    Analyze job description and resume
    TODO: Implement your analysis logic here
    """
    # Placeholder function - replace with your analysis logic
    if not job_description.strip() or not resume.strip():
        return "Please provide both job description and resume content", "", ""
    
    # Example placeholder results - replace with your actual analysis
    resume_summary, jd_summary = resume_analyse(job_description, resume)
    score = resume_summary.pop("Score")
    score_result = json.dumps(score, indent=4)
    analysis_result = json.dumps(resume_summary, indent=4)
    
    not_fit = False
    for item in resume_summary['Non_Technical_Requirements'].values():
        if item['result']['match'] == 'no':
            not_fit = True
            break
        
    if not_fit or score['Required'] < 60:
        conclusion = "Not a fit!"
    elif score['Required'] >= 80:
        conclusion = "A good fit!"
    else:
        conclusion = "Maybe a fit!"
    
    if resume_summary.get('To_Clarify'):
        conclusion += "\n\nTo clarify items:\n"
        for item in resume_summary['To_Clarify']:
            conclusion += item + '\n'

    return json.dumps(jd_summary, indent=4), analysis_result, score_result, conclusion

def create_gradio_app():
    with gr.Blocks(title="Job Description & Resume Analyzer") as demo:
        gr.Markdown("# Job Description & Resume Analyzer")
        gr.Markdown("Upload your job description and resume files to analyze compatibility")
        
        with gr.Row():
            with gr.Column():
                # Job Description Section
                gr.Markdown("## Job Description")
                job_file = gr.File(
                    label="Upload Job Description File",
                    file_types=[".txt", ".docx", ".pdf"],
                    type="filepath"
                )
                job_description = gr.Textbox(
                    label="Job Description Content",
                    placeholder="Job description will appear here after file upload...",
                    lines=10,
                    max_lines=15
                )
                
            with gr.Column():
                # Resume Section
                gr.Markdown("## Resume")
                resume_file = gr.File(
                    label="Upload Resume File",
                    file_types=[".md", ".pdf"],
                    type="filepath"
                )
                resume_content = gr.Textbox(
                    label="Resume Content",
                    placeholder="Resume content will appear here after file upload...",
                    lines=10,
                    max_lines=15
                )
        
        # Analysis Button
        with gr.Row():
            analyze_btn = gr.Button(
                "Analyze",
                variant="primary",
                size="lg"
            )
        
        # Results Section
        gr.Markdown("## Analysis Results")

        with gr.Row():
            with gr.Column():
                jd_summary = gr.Textbox(
                    label="Job Description Summary",
                    placeholder="JD summary will appear here...",
                    lines=8,
                    max_lines=12
                )
                
            with gr.Column():
                analysis_result = gr.Textbox(
                    label="Match Summary",
                    placeholder="Analysis results will appear here...",
                    lines=8,
                    max_lines=12
                )
                
        with gr.Row():
            with gr.Column():
                score_result = gr.Textbox(
                    label="Score Result",
                    placeholder="Score results will appear here...",
                    lines=8,
                    max_lines=12
                )
                
            with gr.Column():
                conclusion_result = gr.Textbox(
                    label="Conclusion",
                    placeholder="Final conclusion will appear here...",
                    lines=8,
                    max_lines=12
                )

        # Event handlers
        job_file.change(
            fn=load_job_description,
            inputs=[job_file],
            outputs=[job_description]
        )
        
        resume_file.change(
            fn=load_resume,
            inputs=[resume_file],
            outputs=[resume_content]
        )
        
        analyze_btn.click(
            fn=analyze_job_resume,
            inputs=[job_description, resume_content],
            outputs=[jd_summary, analysis_result, score_result, conclusion_result]
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
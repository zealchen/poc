import json
import pytest
from src_lambdas.timecard_processor.timecard_processor import app, start_analysis, get_analysis_status
from mangum import Mangum
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import gradio as gr

@pytest.fixture
def client():
    return TestClient(app)

def test_timecard_processor_handler():
    event = {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": "/",
        "rawQueryString": "",
        "headers": {
            "accept": "*/*",
            "host": "example.com",
            "user-agent": "curl/7.64.1",
            "x-amzn-trace-id": "Root=1-60a0f0a0-0a0a0a0a0a0a0a0a0a0a0a0a",
            "x-forwarded-for": "127.0.0.1",
            "x-forwarded-port": "443",
            "x-forwarded-proto": "https"
        },
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "1234567890",
            "domainName": "example.com",
            "domainPrefix": "example",
            "http": {
                "method": "GET",
                "path": "/",
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "curl/7.64.1"
            },
            "requestId": "12345678-1234-1234-1234-123456789012",
            "routeKey": "$default",
            "stage": "$default",
            "time": "12/May/2021:12:00:00 +0000",
            "timeEpoch": 1620816000000
        },
        "isBase64Encoded": False
    }
    context = {}

    handler = Mangum(app)
    response = handler(event, context)

    assert response["statusCode"] == 200
    assert "text/html" in response["headers"]["content-type"]

@patch('src_lambdas.timecard_processor.timecard_processor.Thread')
@patch('src_lambdas.timecard_processor.timecard_processor.table')
def test_start_analysis(mock_table, mock_thread):
    image_path = "dummy_path"
    _, _, job_id = start_analysis(image_path)
    
    assert job_id is not None
    mock_thread.assert_called_once()

@patch('src_lambdas.timecard_processor.timecard_processor.table')
def test_get_analysis_status_running(mock_table):
    mock_table.get_item.return_value = {"Item": {"status": "running"}}
    
    _, _, status = get_analysis_status("some_job_id")
    
    assert status['value'] == "Analyzing..."

@patch('src_lambdas.timecard_processor.timecard_processor.table')
def test_get_analysis_status_success(mock_table):
    mock_df = pd.DataFrame({'col1': [1, 2]})
    mock_table.get_item.return_value = {"Item": {"status": "success", "result": mock_df.to_json()}}
    
    df, _, status = get_analysis_status("some_job_id")
    
    assert status['visible'] == False
    assert not df.empty


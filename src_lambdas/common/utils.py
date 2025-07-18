import boto3
from botocore.client import Config


def get_bedrock_client():
    custom_config = Config(connect_timeout=840, read_timeout=840)
    return boto3.client(service_name="bedrock-runtime", config=custom_config)
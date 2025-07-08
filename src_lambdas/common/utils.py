import boto3


def get_bedrock_client():
    return boto3.client(service_name="bedrock-runtime")
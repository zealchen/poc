from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_dynamodb as ddb,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct
import os
from aws_cdk.aws_lambda import Architecture
from aws_cdk.aws_ecr_assets import Platform

class BenefitAnalysisStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table for job status
        # job_status_table = ddb.Table(
        #     self, "JobStatusTable",
        #     partition_key=ddb.Attribute(name="job_id", type=ddb.AttributeType.STRING),
        #     billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        #     removal_policy=RemovalPolicy.DESTROY
        # )

        # Define Lambda from Docker image
        handler = _lambda.DockerImageFunction(
            self, "BenefitAnalysisLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="src_lambdas",
                file="benefit_analysis/Dockerfile",
                platform=Platform.LINUX_AMD64
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            architecture=Architecture.X86_64,
            environment={
                "GRADIO_SERVER_NAME": "0.0.0.0",
                "GRADIO_SERVER_PORT": "7860",
                # "JOB_STATUS_TABLE": job_status_table.table_name,
            }
        )

        alias = handler.add_alias("live")

        alias.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))

        # Grant Lambda permissions to access DynamoDB table
        # job_status_table.grant_read_write_data(alias)

        # Create HTTP API Gateway with proxy integration
        http_api = apigwv2.HttpApi(self, "BenefitAnalysisHttpApi",
            api_name="BenefitAnalysisHttpApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_origins=["*"],
                allow_headers=["*"],
                max_age=Duration.days(1)
            )
        )

        lambda_integration = integrations.HttpLambdaIntegration(
            "BenefitAnalysisRootIntegration", 
            handler=alias,
            timeout=Duration.seconds(29)
        )
        
        proxy_integration = integrations.HttpLambdaIntegration(
            "BenefitAnalysisProxyIntegration", 
            handler=alias,
            timeout=Duration.seconds(29)
        )

        http_api.add_routes(
            path="/",
            methods=[apigwv2.HttpMethod.ANY],
            integration=lambda_integration
        )

        http_api.add_routes(
            path="/{proxy+}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=proxy_integration
        )

        CfnOutput(self, "BenefitAnalysisApiUrl", value=http_api.api_endpoint)
        CfnOutput(self, "LambdaFunctionName", value=handler.function_name)
        # CfnOutput(self, "JobStatusTableName", value=job_status_table.table_name)
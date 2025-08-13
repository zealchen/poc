from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_s3 as s3,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct
from aws_cdk.aws_lambda import Architecture
from aws_cdk.aws_ecr_assets import Platform

class AIAssessmentStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        trigger_lambda = _lambda.DockerImageFunction(
            self, "TriggerLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="src_lambdas",
                file="ai_assessment/Dockerfile",
                platform=Platform.LINUX_AMD64
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            architecture=Architecture.X86_64,
        )

        step_handler_lambda = _lambda.DockerImageFunction(
            self, "StepHandlerLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                directory="src_lambdas",
                file="ai_assessment/Dockerfile",
                platform=Platform.LINUX_AMD64
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            architecture=Architecture.X86_64,
        )

        # Step Function definition
        create_test_task = sfn_tasks.LambdaInvoke(
            self, "CreateTest",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "create_test",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            }),
        )

        verify_test_task = sfn_tasks.LambdaInvoke(
            self, "VerifyTest",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "verify_test",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "create_test_task_result": sfn.JsonPath.object_at("$.Payload.create_result"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            })
        )
        
        step_handler_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))
        definition = sfn.Chain.start(create_test_task).next(verify_test_task)

        state_machine = sfn.StateMachine(
            self, "AIAssessmentStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(15)
        )

        trigger_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=[state_machine.state_machine_arn]
        ))
        
        trigger_lambda.add_environment("STATE_MACHINE_ARN", state_machine.state_machine_arn)

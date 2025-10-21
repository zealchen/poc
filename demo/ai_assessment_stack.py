from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
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
                file="ai_assessment_v2/Dockerfile",
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
                file="ai_assessment_v2/Dockerfile",
                platform=Platform.LINUX_AMD64
            ),
            timeout=Duration.minutes(15),
            memory_size=1024,
            architecture=Architecture.X86_64,
        )

        # Lambda for parsing curriculum
        parse_curriculum_task = sfn_tasks.LambdaInvoke(
            self, "ParseCurriculum",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "parse_curriculum",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            }),
            result_path="$.parse_result"
        )

        # Map state for processing each requirement
        create_test_for_requirement = sfn_tasks.LambdaInvoke(
            self, "CreateTestForRequirement",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "create_test",
                "requirement": sfn.JsonPath.string_at("$"),
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            }),
            result_path="$.create_result"
        )

        verify_test_for_requirement = sfn_tasks.LambdaInvoke(
            self, "VerifyTestForRequirement",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "verify_test",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "create_test_task_result": sfn.JsonPath.object_at("$.create_result.Payload"),
                "requirement": sfn.JsonPath.string_at("$"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            }),
            output_path="$.Payload"
        )

        # Chain for each requirement in the map
        requirement_chain = sfn.Chain.start(create_test_for_requirement).next(verify_test_for_requirement)

        # Map state to process all requirements
        process_requirements_map = sfn.Map(
            self, "ProcessRequirementsMap",
            items_path="$.parse_result.Payload.requirements",
            max_concurrency=10,
            result_path="$.map_results"
        )
        process_requirements_map.iterator(requirement_chain)

        # Aggregate results
        aggregate_results_task = sfn_tasks.LambdaInvoke(
            self, "AggregateResults",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "aggregate_results",
                "all_requirements": sfn.JsonPath.object_at("$.parse_result.Payload.all_requirements"),
                "map_results": sfn.JsonPath.object_at("$.map_results"),
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            })
        )

        # Curriculum flow: parse -> map -> aggregate
        curriculum_flow = sfn.Chain.start(parse_curriculum_task)\
            .next(process_requirements_map)\
            .next(aggregate_results_task)

        # Single test flow (no curriculum)
        create_test_task = sfn_tasks.LambdaInvoke(
            self, "CreateTest",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "create_test",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            }),
            result_path="$.create_result"
        )

        verify_test_task = sfn_tasks.LambdaInvoke(
            self, "VerifyTest",
            lambda_function=step_handler_lambda,
            payload=sfn.TaskInput.from_object({
                "step_name": "verify_test",
                "execution_input": sfn.JsonPath.object_at("$$.Execution.Input"),
                "create_test_task_result": sfn.JsonPath.object_at("$.create_result.Payload"),
                "execution_arn": sfn.JsonPath.string_at("$$.Execution.Id")
            })
        )

        single_test_flow = sfn.Chain.start(create_test_task).next(verify_test_task)

        # Choice state to check for curriculum_uri
        check_curriculum = sfn.Choice(self, "CheckCurriculumUri")
        check_curriculum.when(
            sfn.Condition.is_present("$.curriculum_uri"),
            curriculum_flow
        ).otherwise(single_test_flow)

        # Start with the choice
        definition = sfn.Chain.start(check_curriculum)

        step_handler_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))

        state_machine = sfn.StateMachine(
            self, "AIAssessmentStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(30)
        )

        trigger_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=[state_machine.state_machine_arn]
        ))

        trigger_lambda.add_environment("STATE_MACHINE_ARN", state_machine.state_machine_arn)
        step_handler_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[
                "arn:aws:s3:::nc-dev-001/*"
            ]
        ))

        step_handler_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["s3:ListBucket"],
            resources=[
                "arn:aws:s3:::nc-dev-001"
            ]
        ))

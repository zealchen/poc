import aws_cdk as core
import aws_cdk.assertions as assertions

from demo.timecard_stack import TimecardStack

def test_lambda_function_created():
    app = core.App()
    stack = TimecardStack(app, "demo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Lambda::Function", {
        "PackageType": "Image"
    })

def test_api_gateway_created():
    app = core.App()
    stack = TimecardStack(app, "demo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::ApiGatewayV2::Api", {
        "ProtocolType": "HTTP"
    })

def test_dynamodb_table_created():
    app = core.App()
    stack = TimecardStack(app, "demo")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::DynamoDB::Table", {
        "KeySchema": [
            {
                "AttributeName": "job_id",
                "KeyType": "HASH"
            }
        ]
    })

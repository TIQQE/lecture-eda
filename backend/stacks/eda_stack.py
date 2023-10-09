from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_sns as sns,

)
from constructs import Construct

class EdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_table = dynamodb.Table(
            self, "UserTable",
            table_name="eda-user-table",
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        event_bus = events.EventBus(
            self, "EventBus",
            event_bus_name="eda-lecture-event-bus",
        )

        new_user_handler = _lambda.Function(
            self, "NewUserLambda",
            function_name="NewUser",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="new_user.lambda_handler",
            code=_lambda.Code.from_asset("./backend/lambda"),
            timeout=Duration.seconds(10),
            environment={
                "TABLE_NAME": user_table.table_name,
                "EVENT_BUS_NAME": event_bus.event_bus_name,
            },
            description="Example Lambda function to create a new user for EDA lecture",
        )

        user_table.grant_write_data(new_user_handler)
        event_bus.grant_put_events_to(new_user_handler)

        notify_user_topic = sns.Topic(
            self, "NotifyNewUserSNS",
            display_name="Notify New User SNS, EDA lecture",
        )

        notify_user_handler = _lambda.Function(
            self, "NotifyUserLambda",
            function_name="NotifyUser",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="notify_user.lambda_handler",
            code=_lambda.Code.from_asset("./backend/lambda"),
            timeout=Duration.seconds(10),
            environment={
                "TOPIC_ARN": notify_user_topic.topic_arn,
            },
            description="Example Lambda function to notify user for EDA lecture",
        )

        # route events user_created to notify_user_handler
        user_created_rule = events.Rule(
            self, 
            "UserCreatedRule",
            event_bus=event_bus,
            description="Rule for forwarding user_created events",
            enabled=True,
            event_pattern=events.EventPattern(
                source=["eda_lecture"],
                detail_type=["user_created"],
            )
        )

        user_created_rule.add_target(
            events_targets.LambdaFunction(
                notify_user_handler
            )
        )

        notify_user_topic.grant_publish(notify_user_handler)

        customer_api = apigateway.RestApi(
            self, "CustomerApi",
            rest_api_name="Customer Service",
            description="Example API for EDA lecture",
            default_method_options=apigateway.MethodOptions(
                api_key_required=True,
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="v1",
                logging_level=apigateway.MethodLoggingLevel.INFO,
            ),
        )

        customer_request_validator = apigateway.RequestValidator(
            self, "CustomerRequestValidator",
            rest_api=customer_api,
            request_validator_name="CustomerRequestValidator",
            validate_request_body=True,
        )

        add_user_model = customer_api.add_model(
            "AddUserModel",
            content_type="application/json",
            description="Add User Model",
            schema={
                "type": apigateway.JsonSchemaType.OBJECT,
                "properties": {
                    "username": 
                    {
                        "pattern": '^.+',
                        "type": apigateway.JsonSchemaType.STRING
                    },
                    "email":
                    {
                        "pattern": '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                        "type": apigateway.JsonSchemaType.STRING
                    }
                },
                "required": ["username", "email"],
            }
        )

        customer_api.add_gateway_response(
            "GatewayResponse400",
            status_code="400",
            type=apigateway.ResponseType.BAD_REQUEST_BODY,
            templates={"application/json": '{ "massage": "$context.error.validationErrorString" }'},
        )

        new_user_integration = apigateway.LambdaIntegration(new_user_handler)

        new_user_resource = customer_api.root.add_resource("new-user")

        new_user_resource.add_method(
            http_method="POST",
            integration=new_user_integration,
            operation_name="new-user",
            request_models={"application/json": add_user_model},
            request_validator=customer_request_validator
        )

        api_key = customer_api.add_api_key(
            "ApiKey",
            api_key_name="eda-lecture-api-key",
            description="API Key for EDA lecture"
        )

        usage_plan = customer_api.add_usage_plan(
            "UsagePlan",
            name="eda-lecture-usage-plan",
            description="Usage plan for EDA lecture",
            api_stages=[
                {
                    "api": customer_api,
                    "stage": customer_api.deployment_stage,
                }
            ],
            throttle=apigateway.ThrottleSettings(
                burst_limit=1,
                rate_limit=1,
            ),
        )

        usage_plan.add_api_key(api_key)
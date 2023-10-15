import os
import json
import boto3
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
events = boto3.client('events')
dynamodb = boto3.resource('dynamodb')
SOURCE = "eda_lecture"
EVENTDETAILTYPE = "user_created"

def lambda_handler(event, context):
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    # Deserialize request body
    request_body = json.loads(event["body"])

    # Fetch username and email from request body
    username = request_body["username"]
    email = request_body["email"]

    # Create item to be stored in DynamoDB where PK is email and SK is username
    created_at = datetime.datetime.now().isoformat()
    db_item = {
        "PK": email,
        "SK": username,
        "created_at": created_at,
    }

    # Store item in DynamoDB
    try:
        table.put_item(Item=db_item)
    except Exception as e:
        logger.error(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "result": f"failed to store item in DynamoDB: {e}"
            }),
        }
    

    # Send event to EventBridge
    event_item = {
        "username": username,
        "email": email,
        "created_at": created_at,
    }

    try:
        response = events.put_events(
            Entries=[
                {
                    "Source": SOURCE,
                    "DetailType": EVENTDETAILTYPE,
                    "Detail": json.dumps(event_item),
                    "EventBusName": os.environ["EVENT_BUS_NAME"]
                }
            ]
        )
    except Exception as e:
        logger.error(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "result": f"failed to send event to EventBridge: {e}"
            }),
        }

    # Returns success reponse to API Gateway
    return { "statusCode": 200 }

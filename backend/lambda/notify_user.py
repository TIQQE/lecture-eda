import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Extract the message from the EventBridge event
        email = event['detail']['email']
    except Exception as e:
        logger.error(e)
        return

    try:
        # Publish the message to an SNS topic
        sns = boto3.client('sns')
        response = sns.publish(
            TopicArn=os.environ['TOPIC_ARN'],
            Message=f"User successfully created with email: {email}",
            Subject='User Created',
            MessageStructure='string'
        )
    except Exception as e:
        logger.error(e)
        return

    print(response)

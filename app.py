#!/usr/bin/env python3
import os

import aws_cdk as cdk
from dotenv import load_dotenv

from backend.stacks.eda_stack import EdaStack

direnv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(direnv_path):
    load_dotenv(direnv_path)

stage = os.environ.get('STAGE') or 'dev'
account = os.environ.get('AWSACCOUNT')
region = os.environ.get('AWSREGION')

context = {
    "STAGE": stage,
    "AWS_ACCOUNT": account,
    "REGION": region
}

env = cdk.Environment(
    account=account,
    region=region
)

app = cdk.App(context=context)
EdaStack(
    app, 
    "EdaStack",
    env=cdk.Environment(
    account=account,
    region=region
))

print("The following paramets have been set:")
print(f"* {stage}")
print(f"* {account}")
print(f"* {region}")

app.synth()

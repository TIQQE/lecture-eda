import aws_cdk as core
import aws_cdk.assertions as assertions

from lecture_eda.lecture_eda_stack import LectureEdaStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lecture_eda/lecture_eda_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LectureEdaStack(app, "lecture-eda")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

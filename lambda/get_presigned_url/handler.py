from aws_lambda_powertools import Tracer
from domain.get_presigned_url import get_presigned_url

tracer = Tracer()

@tracer.capture_lambda_handler
def handler(event, context):
    try:
        response = get_presigned_url()

        return {
            "statusCode": 200,
            "body": response,
        }
    except Exception as e:
        print(f"Error generating signed url: {e}")
        return {"statusCode": 500, "body": "Internal server error"}

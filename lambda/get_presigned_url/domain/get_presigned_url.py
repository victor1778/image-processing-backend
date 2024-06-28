import json
import os

import boto3
import nanoid
from botocore.exceptions import ClientError

bucket_name = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")


def get_presigned_url():
    object_name = f"{nanoid.generate(alphabet='0123456789abcdefghijklmnopqrstuvwxyz', size=12)}.jpg"

    try:
        response = s3.generate_presigned_post(
            Bucket=bucket_name,
            Key=object_name,
            Fields={"Content-Type": "image/jpeg"},
            Conditions=[{"Content-Type": "image/jpeg"}],
            ExpiresIn=3600,
        )

        return json.dumps(response)
    except ClientError as e:
        return json.dumps({"error": str(e)})

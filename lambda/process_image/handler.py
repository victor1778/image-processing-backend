import json

from domain.process_image import process_image


def handler(event, context):
    body = json.loads(event.get("body", "{}"))

    key = body.get("key")
    blur_radius = body.get("blur_radius")

    if key is None or blur_radius is None:
        raise ValueError("Missing required parameters: 'key' and 'blur_radius'")

    response = process_image(key, blur_radius)

    return {
        "statusCode": 200,
        "body": response,
    }

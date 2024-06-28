import io
import json
import os

import boto3
import botocore
from PIL import Image, ImageFilter

initial_factor = 2
r_1 = 1.089 / 100
bucket = os.environ["BUCKET_NAME"]
config = botocore.config.Config(
    max_pool_connections=20, s3={"use_accelerate_endpoint": True}
)
s3 = boto3.client("s3", config=config)
preallocated_buffer = io.BytesIO()


def process_image(key: str, blur_radius: str):
    blur_radius = int(blur_radius)
    downscale_factor = initial_factor * (1 + r_1) ** blur_radius

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        object_content = response["Body"].read()

        # Load the image
        image = Image.open(io.BytesIO(object_content))

        # Downscale the image
        downscaled_image = image.resize(
            (int(image.width / downscale_factor), int(image.height / downscale_factor)),
            Image.LANCZOS,
        )

        # Apply the unsharp mask
        unsharp_image = downscaled_image.filter(
            ImageFilter.UnsharpMask(radius=2, percent=20, threshold=3)
        )

        # Apply the Gaussian blur if the blur radius is not 0
        if blur_radius != 0:
            unsharp_image = unsharp_image.filter(ImageFilter.GaussianBlur(blur_radius))

        # Upscale the image
        upscaled_image = unsharp_image.resize(
            (
                int(unsharp_image.width * downscale_factor),
                int(unsharp_image.height * downscale_factor),
            ),
            Image.BICUBIC,
        )

        # Save the processed image to a BytesIO object
        upscaled_image.save(preallocated_buffer, format="JPEG")
        preallocated_buffer.seek(0)

        processed_key = f"processed/{blur_radius}px-{key}"

        s3.put_object(
            Bucket=bucket,
            Key=processed_key,
            Body=preallocated_buffer,
            ContentType="image/jpeg",
        )

        return json.dumps({"key": processed_key})
    except Exception as e:
        return json.dumps({"error": "Internal server error"})

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_lambda
from aws_cdk import aws_s3 as s3
from cdk_lambda_layer_builder.constructs import BuildPyLayerAsset
from constructs import Construct


class ImageProcessingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "ImageBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            transfer_acceleration=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            public_read_access=False,
            server_access_logs_bucket=s3.Bucket(
                self,
                "AccessLogsBucket",
                removal_policy=RemovalPolicy.DESTROY,
                auto_delete_objects=True,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                enforce_ssl=True,
                public_read_access=False,
                lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.hours(24),
                )
            ],
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.hours(24),
                )
            ],
        )

        pypi_layer_asset = BuildPyLayerAsset.from_pypi(
            self,
            "PyPiLayerAsset",
            pypi_requirements=["pillow", "nanoid"],
            py_runtime=aws_lambda.Runtime.PYTHON_3_9,
        )

        pypi_layer = aws_lambda.LayerVersion(
            self,
            id="PyPiLayer",
            code=aws_lambda.Code.from_bucket(
                pypi_layer_asset.asset_bucket, pypi_layer_asset.asset_key
            ),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],
            description="PyPi python modules",
        )

        get_presigned_url_handler = aws_lambda.Function(
            self,
            "GetSignedUrl",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            code=aws_lambda.Code.from_asset("./lambda/get_presigned_url"),
            handler="handler.handler",
            environment={
                "BUCKET_NAME": bucket.bucket_name,
            },
            memory_size=1024,
            timeout=Duration.seconds(29),
            layers=[pypi_layer],
        )

        process_image_handler = aws_lambda.Function(
            self,
            "ProcessImage",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            code=aws_lambda.Code.from_asset("./lambda/process_image"),
            handler="handler.handler",
            environment={
                "BUCKET_NAME": bucket.bucket_name,
            },
            memory_size=3008,
            timeout=Duration.seconds(29),
            layers=[pypi_layer],
        )

        bucket.grant_read_write(process_image_handler)
        bucket.grant_read_write(get_presigned_url_handler)

        api = apigateway.RestApi(
            self,
            "ImageProcessingApi",
            rest_api_name="Image Processing Service",
            description="This service generates signed URLs for image uploads and processes images",
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
            },
        )

        get_presigned_url_integration = apigateway.LambdaIntegration(
            get_presigned_url_handler,
        )

        get_presigned_url_resource = api.root.add_resource("presigned-url")

        get_presigned_url_resource.add_method(
            "GET",
            get_presigned_url_integration,
        )

        process_image_resource = api.root.add_resource("blur")

        process_image_integration = apigateway.LambdaIntegration(
            process_image_handler,
        )
        process_image_resource.add_method(
            "POST",
            process_image_integration,
        )

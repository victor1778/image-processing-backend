#!/usr/bin/env python3
import os

import aws_cdk as cdk

from image_processing.image_processing_stack import ImageProcessingStack

app = cdk.App()
ImageProcessingStack(app, "ImageProcessingStack")

app.synth()

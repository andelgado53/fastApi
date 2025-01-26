#!/usr/bin/env python3
import aws_cdk as cdk
from fast_api_prototype.pipeline_stack import PipelineStack

app = cdk.App()
env = cdk.Environment(account='385249579775', region='us-west-2')
PipelineStack(app, "FastApiPipelineStack", env=env)

app.synth()


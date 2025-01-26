from aws_cdk import (
    pipelines as pipelines,
    Stack, Stage
)
from constructs import Construct
from .ecs_stack import ECSStack

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        source = pipelines.CodePipelineSource.connection(
            "andelgado53/fastApi",
            "master",
            connection_arn="arn:aws:codeconnections:us-west-2:385249579775:connection/acd4b90d-7dfa-4f19-aad5-b68d9b524840"
        )

        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=source,
                commands=[
                    "pip install -r requirements.txt",
                    "npm install -g aws-cdk",
                    "which cdk",
                    "cdk --version",
                    "cdk synth"
                ],
            ),
        )

        pipeline.add_stage(ECSDeploymentStage(self, "DeployECS", **kwargs))

class ECSDeploymentStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        ECSStack(self, "ECSStack")

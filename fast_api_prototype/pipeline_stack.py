from aws_cdk import (
    pipelines as pipelines,
    Stack, Stage
)
from constructs import Construct
from .ecs_stack import ECSStack

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define GitHub source connection
        source = pipelines.CodePipelineSource.connection(
            "andelgado53/fastApi",  # Replace with your repo
            "master",
            connection_arn="arn:aws:codeconnections:us-west-2:385249579775:connection/acd4b90d-7dfa-4f19-aad5-b68d9b524840"
        )

        # Create the pipeline
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=source,
                commands=[
                    "pip install -r requirements.txt",
                    "npm install -g aws-cdk",  # Install CDK CLI
                    "which cdk",  # Verify that cdk is installed
                    "cdk --version",  # Verify CDK version
                    "cdk synth"  # Generate CloudFormation templates
                ],
            ),
        )

        # Add the ECS deployment stage
        pipeline.add_stage(ECSDeploymentStage(self, "DeployECS", env))

class ECSDeploymentStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        ECSStack(self, "ECSStack", env)

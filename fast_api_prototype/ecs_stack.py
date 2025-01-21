from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    Stack,
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "FastApiVpc", max_azs=2)

        # ECS Cluster
        cluster = ecs.Cluster(self, "FastApiCluster", vpc=vpc)

        # Fargate Service with Load Balancer
        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FastApiFargateService",
            cluster=cluster,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./app")  # Path to Dockerfile
            ),
            public_load_balancer=True,
        )

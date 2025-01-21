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

        task_definition = ecs.FargateTaskDefinition(self, "FastApiTaskDefinition")

        container = task_definition.add_container(
            "FastApiContainer",
            image=ecs.ContainerImage.from_asset("./app"),
            memory_limit_mib=512,
            cpu=256,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="MyFastApiApp")
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8000))

        # ECS Cluster
        cluster = ecs.Cluster(self, "FastApiCluster", vpc=vpc)

        # Fargate Service with Load Balancer
        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FastApiFargateService",
            cluster=cluster,
            task_definition=task_definition,
            public_load_balancer=True,
            health_check={
                "port": "8000",  # Make sure the health check is on port 8000
                "path": "/",  # Your health check path, if you have one
            }
        )

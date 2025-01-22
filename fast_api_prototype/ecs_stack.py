from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    Stack, Duration, aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name="emisofia.com")

        certificate = acm.Certificate(self, "Certificate",
            domain_name="emisofia.com",
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

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

        cluster = ecs.Cluster(self, "FastApiCluster", vpc=vpc)

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FastApiFargateService",
            cluster=cluster,
            task_definition=task_definition,
            public_load_balancer=True,
            certificate=certificate,
            domain_name="emisofia.com",
            domain_zone=hosted_zone
        )

        service.target_group.configure_health_check(
        path="/healthy",  # Health check path
        port="8000",     # The container port for the health check
        interval=Duration.seconds(30),  # Optional: health check interval
        timeout=Duration.seconds(5),    # Optional: timeout for health check
        ) 

        # Route 53 Record
        route53.ARecord(self, "AliasRecord",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(service.load_balancer))
        )

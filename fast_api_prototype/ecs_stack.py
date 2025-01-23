from aws_cdk import (
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    Stack, Duration, aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_apigateway as apigw,
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name="emisofia.com")

        alb_certificate = acm.Certificate(
            self, "AlbCertificate",
            domain_name="emisofia.com",
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        api_certificate = acm.Certificate(
            self, "ApiGatewayCertificate",
            domain_name="api.emisofia.com",
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
            public_load_balancer=False,
            certificate=alb_certificate
        )

        # Restrict ALB Access with Security Group
        service.load_balancer.connections.allow_from(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(443),  # Only allow HTTPS traffic
            "Allow traffic from API Gateway"
        )

         # API Gateway with Custom Domain Name
        api = apigw.RestApi(
            self,
            "FastApiGateway",
            domain_name=apigw.DomainNameOptions(
                domain_name="api.emisofia.com",
                certificate=api_certificate
            )
        )

         # Proxy API Gateway requests to ALB
        integration = apigw.HttpIntegration(
            f"https://{service.load_balancer.load_balancer_dns_name}",
            http_method="ANY",
            options=apigw.IntegrationOptions(
                connection_type=apigw.ConnectionType.VPC_LINK,
                vpc_link=apigw.VpcLink(self, "VpcLink", targets=[service.load_balancer])
            )
        )

        # Add API Resource
        api.root.add_method("ANY", integration)

        service.target_group.configure_health_check(
        path="/healthy",
        port="8000",
        interval=Duration.seconds(30),
        timeout=Duration.seconds(5),
        ) 


from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as integrations,
    aws_route53 as route53,
    Duration,
    Stack,
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Hosted Zone for Domain
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name="emisofia.com"
        )

        # API Gateway Certificate
        api_certificate = acm.Certificate(
            self,
            "ApiGatewayCertificate",
            domain_name="api.emisofia.com",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # VPC
        vpc = ec2.Vpc(self, "FastApiVpc", max_azs=2)

        # ECS Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "FastApiTaskDefinition")
        container = task_definition.add_container(
            "FastApiContainer",
            image=ecs.ContainerImage.from_asset("./app"),
            memory_limit_mib=512,
            cpu=256,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="MyFastApiApp"),
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8000))

        # ECS Cluster and Service
        cluster = ecs.Cluster(self, "FastApiCluster", vpc=vpc)
        service = ecs.FargateService(
            self, "MyFargateService", cluster=cluster, task_definition=task_definition
        )

        # Network Load Balancer
        nlb = elbv2.NetworkLoadBalancer(
            self, "MyNLB", vpc=vpc, internet_facing=False
        )

        listener = nlb.add_listener(
            "Listener",
            port=80,
            default_target_groups=[
                elbv2.NetworkTargetGroup(
                    self,
                    "EcsTargetGroup",
                    vpc=vpc,
                    port=8000,
                    targets=[service],
                    health_check=elbv2.HealthCheck(
                        path="/healthy",
                        interval=Duration.seconds(30),
                        timeout=Duration.seconds(5),
                    ),
                )
            ],
        )

        domain_name = apigateway.CfnDomainName(
            self,
            "ApiGatewayDomain",
            domain_name="api.emisofia.com",
            domain_name_configurations=[
                apigateway.CfnDomainName.DomainNameConfigurationProperty(
                    certificate_arn=api_certificate.certificate_arn,
                    endpoint_type="REGIONAL",
                )
            ],
        )

        # API Gateway HTTP API
        http_api = apigateway.CfnApi(
            self,
            "MyHttpApi",
            name="MyHttpApi",
            protocol_type="HTTP",
            cors_configuration={
                "allowOrigins": ["*"],
                "allowMethods": ["GET", "POST", "OPTIONS"],
            },
        )

        # Route linking API Gateway to NLB
        apigateway.CfnIntegration(
            self,
            "NLBIntegration",
            api_id=http_api.ref,
            integration_type="HTTP_PROXY",
            integration_uri=f"http://{nlb.load_balancer_dns_name}",
            payload_format_version="1.0",
        )

        # Add Default Stage
        apigateway.CfnStage(
            self,
            "HttpApiStage",
            api_id=http_api.ref,
            stage_name="$default",
            auto_deploy=True,
        )

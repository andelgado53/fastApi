from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_apigatewayv2 as apigateway,
    aws_apigatewayv2_integrations as apigateway_integrations,
    aws_route53 as route53,
    aws_route53_targets as targets,
    Duration,
    Stack,
    aws_cognito as cognito,
    aws_apigatewayv2_authorizers as apigateway_authorizers,
    CfnOutput, aws_lambda
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # VPC Configuration
        vpc = ec2.Vpc(
            self, "FastApiVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Lookup the hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name="emisofia.com"
        )

        # Certificate for API Gateway
        api_certificate = acm.Certificate(
            self, "ApiGatewayCertificate",
            domain_name="api.emisofia.com",
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # ECS Task Definition with container health check
        task_definition = ecs.FargateTaskDefinition(
            self, "FastApiTaskDefinition",
            memory_limit_mib=512,
            cpu=256
        )

        container = task_definition.add_container(
            "FastApiContainer",
            image=ecs.ContainerImage.from_asset("./app"),
            memory_limit_mib=512,
            cpu=256,
            logging=ecs.LogDrivers.aws_logs(stream_prefix="MyFastApiApp"),
            health_check={
                "command": ["CMD-SHELL", "curl -f http://localhost:8000/healthy || exit 1"],
                "interval": Duration.seconds(30),
                "timeout": Duration.seconds(5),
                "retries": 3
            }
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8000))

        # ECS Cluster and Service
        cluster = ecs.Cluster(self, "FastApiCluster", vpc=vpc)

        # ECS service security group
        service_security_group = ec2.SecurityGroup(
            self, "ServiceSecurityGroup",
            vpc=vpc,
            description="Security group for Fargate service"
        )

        service_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8000),
            description="Allow TCP traffic on port 8000"
        )

        service = ecs.FargateService(
            self, "MyFargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,  
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[service_security_group]
        )

        # NLB Configuration
        nlb = elbv2.NetworkLoadBalancer(
            self, "FastApiNLB",
            vpc=vpc,
            internet_facing=False,
            cross_zone_enabled=True
        )

        # Target Group
        target_group = elbv2.NetworkTargetGroup(
            self, "EcsTargetGroup",
            vpc=vpc,
            port=8000,
            protocol=elbv2.Protocol.TCP,  # Use TCP for health check and communication
            targets=[service],
            health_check=elbv2.HealthCheck(
                port="8000",  # Ensure it's the right port your app is running on
                protocol=elbv2.Protocol.TCP,  # TCP health check
                interval=Duration.seconds(30),
                healthy_threshold_count=2,
                unhealthy_threshold_count=2
            )
        )

        # Create VPC Link
        vpc_link = apigateway.VpcLink(self, "VpcLink", vpc=vpc)

        pre_token_generation_lambda = aws_lambda.Function(
            self, "PreTokenGenerationLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=aws_lambda.Code.from_asset("./lambda"),  # Directory containing your lambda code
        )

        user_pool = cognito.UserPool(
            self, "FastApiUserPool",
            user_pool_name="FastApiUserPool",
            self_sign_up_enabled=True,  # Enable user sign-up
            sign_in_aliases=cognito.SignInAliases(email=True, username=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),  # Auto-verify email
            standard_attributes={
                "email": cognito.StandardAttribute(required=True, mutable=False),
            },
            custom_attributes={
                "role": cognito.StringAttribute(
                    mutable=False,
                    max_len=25
                ),
                "org": cognito.StringAttribute(
                    mutable=False,
                    max_len=50
                )
            },
            lambda_triggers=cognito.UserPoolTriggers(
                pre_token_generation=pre_token_generation_lambda
            )
        )



        # Create User Pool Client
        
        user_pool_client = user_pool.add_client(
            "FastApiUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Enable user-password flow
                user_srp=True       # Enable SRP (Secure Remote Password) protocol
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=False
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE]
                    # callback_urls=["http://localhost:3000"],  # Add your callback URLs
                    # logout_urls=["http://localhost:3000"]     # Add your logout URLs
            ),
            access_token_validity=Duration.minutes(60),  # Set Access Token validity
            id_token_validity=Duration.hours(1),         # Set ID Token validity
            refresh_token_validity=Duration.days(30),  
            read_attributes=cognito.ClientAttributes()
                .with_standard_attributes(email=True)
                .with_custom_attributes("role", "org")
        )

        # Create Cognito Authorizer
        cognito_authorizer = apigateway_authorizers.HttpJwtAuthorizer(
            "FastApiCognitoAuthorizer",
            jwt_issuer=f"https://cognito-idp.{Stack.of(self).region}.amazonaws.com/{user_pool.user_pool_id}",
            jwt_audience=[user_pool_client.user_pool_client_id], 
            identity_source=["$request.header.Authorization"]  # Authorization header
        )   

        # Create HTTP API
        http_api = apigateway.HttpApi(self, "FastApiHttpApi", api_name="FastApiHttpApi")

        # NLB Listener
        nlb_listener = nlb.add_listener(
            "Listener",
            port=80,
            protocol=elbv2.Protocol.TCP,
            default_target_groups=[target_group]
        )

        # Integration
        integration = apigateway_integrations.HttpNlbIntegration(
            "NlbIntegration",
            listener=nlb_listener,
            vpc_link=vpc_link
        )

        # Routes
        http_api.add_routes(
            path="/{proxy+}",
            methods=[apigateway.HttpMethod.ANY],
            integration=integration,
            authorizer=cognito_authorizer
        )

        # Custom domain configuration
        domain_name = apigateway.DomainName(
            self, "ApiDomain",
            domain_name="api.emisofia.com",
            certificate=api_certificate
        )

        # API mapping
        apigateway.ApiMapping(
            self, "ApiMapping",
            api=http_api,
            domain_name=domain_name,
            stage=http_api.default_stage
        )

        # DNS record
        route53.ARecord(
            self, "ApiARecord",
            zone=hosted_zone,
            record_name="api",
            target=route53.RecordTarget.from_alias(
                targets.ApiGatewayv2DomainProperties(
                    domain_name.regional_domain_name,
                    domain_name.regional_hosted_zone_id
                )
            )
        )

        # Outputs
        CfnOutput(
            self, "ApiGatewayUrl",
            value=http_api.url or "undefined",
            description="API Gateway URL"
        )

        CfnOutput(
            self, "CustomDomainUrl",
            value=f"https://api.emisofia.com",
            description="Custom Domain URL"
        )

        CfnOutput(
            self, "NlbDnsName",
            value=nlb.load_balancer_dns_name,
            description="Network Load Balancer DNS Name"
        )

        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        CfnOutput(
            self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

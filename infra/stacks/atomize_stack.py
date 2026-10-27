from typing import Any

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_apigatewayv2 as apigwv2,
)
from aws_cdk import (
    aws_apigatewayv2_integrations as apigwv2_integrations,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as events_targets,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_rds as rds,
)
from aws_cdk import (
    aws_s3 as s3,
)
from constructs import Construct


class AtomizeStack(Stack):
    """Atomize's AWS infrastructure, per docs/TECH_STACK.md.

    Scaffold only: the API Lambda currently points at a placeholder handler.
    Packaging the real FastAPI app (apps/api) as the Lambda deployment
    artifact is a follow-up build step, not solved here.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Networking ---------------------------------------------------
        # No NAT gateway: NAT isn't in the AWS free tier and nothing here
        # needs outbound internet from inside the VPC. RDS lives in an
        # isolated subnet; the API Lambda is NOT VPC-attached for now, which
        # is a gap to close before this talks to RDS directly (see README
        # "Known gaps" — options are VPC-attaching the Lambda with VPC
        # endpoints for S3/Bedrock/Textract, or a Data API / proxy in front
        # of RDS).
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        # --- Database (SPEC/DATA_MODEL: Postgres, RDS free tier) ----------
        database = rds.DatabaseInstance(
            self,
            "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            database_name="atomize",
            credentials=rds.Credentials.from_generated_secret("atomize_admin"),
            allocated_storage=20,
            max_allocated_storage=20,
            storage_encrypted=True,
            multi_az=False,
            removal_policy=RemovalPolicy.SNAPSHOT,
            deletion_protection=False,
        )

        # --- Receipt image storage (SPEC §19: delete after 6 months) ------
        receipts_bucket = s3.Bucket(
            self,
            "ReceiptsBucket",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-receipt-images-after-6-months",
                    expiration=Duration.days(180),
                ),
            ],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # --- Auth (SPEC §2: household invite-based membership) ------------
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            removal_policy=RemovalPolicy.RETAIN,
        )
        user_pool_client = user_pool.add_client(
            "WebClient",
            auth_flows=cognito.AuthFlow(user_srp=True),
        )

        # --- API (FastAPI on Lambda, per docs/TECH_STACK.md) ---------------
        # Placeholder inline handler — replace with a packaged build of
        # apps/api (e.g. via a Docker-bundled PythonFunction) once the app
        # has real endpoints worth deploying.
        api_handler = lambda_.Function(
            self,
            "ApiHandler",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    return {'statusCode': 200, 'body': 'Atomize API placeholder'}\n"
            ),
            timeout=Duration.seconds(10),
            environment={
                "RECEIPTS_BUCKET_NAME": receipts_bucket.bucket_name,
                "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                "COGNITO_APP_CLIENT_ID": user_pool_client.user_pool_client_id,
            },
        )
        receipts_bucket.grant_read_write(api_handler)

        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            default_integration=apigwv2_integrations.HttpLambdaIntegration(
                "ApiIntegration", api_handler
            ),
        )

        # --- Scheduled jobs (SPEC §7 month-close ledger, §19 image purge) -
        month_close_handler = lambda_.Function(
            self,
            "MonthCloseLedgerHandler",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="index.handler",
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    pass  # TODO: compute budget_period_ledger rows for the closed month\n"
            ),
            timeout=Duration.minutes(5),
        )
        events.Rule(
            self,
            "MonthCloseLedgerSchedule",
            schedule=events.Schedule.cron(minute="0", hour="6", day="1"),
            targets=[events_targets.LambdaFunction(month_close_handler)],
        )

        CfnOutput(self, "ApiUrl", value=http_api.api_endpoint)
        CfnOutput(self, "ReceiptsBucketName", value=receipts_bucket.bucket_name)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "DatabaseSecretArn", value=database.secret.secret_arn if database.secret else "")

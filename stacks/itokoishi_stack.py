from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam
)
from constructs import Construct
import os


class ItokoishiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # dynamoDBの作成
        itokoishi_table = dynamodb.Table(
            self, 'itokoishi',
            table_name='itokoishi',
            partition_key=dynamodb.Attribute(name='pk', type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name='sk', type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            stream=dynamodb.StreamViewType.NEW_IMAGE

        )

        # ロールの追加
        iam_role = iam.Role(
            self, 'itokoishi_role',
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name='itokoishi_role',
            path='/',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonDynamoDBFullAccess'
                )
            ]
        )

        path = os.path
        cwd = os.getcwd()
        # lambdaの作成
        itokoishi_lambda = lambda_.Function(
            self, 'itokoishi',
            function_name='itokoishi',
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(path.join(cwd, 'app')),
            handler='index.lambda_handler',
            allow_public_subnet=True,
            timeout=Duration.seconds(360),
            role=iam_role,
            environment={
                'TEST': 'テストの環境変数'
            }
        )

        # dynamodb stream をトリガーに
        itokoishi_lambda.add_event_source_mapping(
            'itokoishi_table_stream_trigger',
            event_source_arn=itokoishi_table.table_stream_arn,
            max_record_age=Duration.seconds(180),
            starting_position=lambda_.StartingPosition.LATEST
        )

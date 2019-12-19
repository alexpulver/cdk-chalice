# cdk-chalice
**AWS CDK construct for AWS Chalice**

Adds the provided stage configuration to SOURCE_DIR/.chalice/config.json.
Stage name will be the string representation of current CDK scope.

Packages the application into AWS SAM format and imports the resulting template
into the construct tree under the provided scope.

At this time, only API handler Lambda function is supported for deployment.
Further work is required to automatically generate CDK assets for additional
Lambda functions (e.g. triggered on SQS message).

The following Python versions are currently supported for Chalice app:
`2`, `2.7`, `3`, `3.6`, `3.7`, `3.8`

#### Usage example
```python
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    core as cdk
)
from cdk_chalice import Chalice


class WebApiError(Exception):
    pass


class WebApi(cdk.Stack):

    _API_HANDLER_LAMBDA_MEMORY_SIZE = 128
    _API_HANDLER_LAMBDA_TIMEOUT = 10

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        partition_key = dynamodb.Attribute(name='username',
                                           type=dynamodb.AttributeType.STRING)
        self.dynamodb_table = dynamodb.Table(
            self, 'UsersTable', partition_key=partition_key,
            removal_policy=cdk.RemovalPolicy.DESTROY)
        cdk.CfnOutput(self, 'UsersTableName', value=self.dynamodb_table.table_name)

        lambda_service_principal = iam.ServicePrincipal('lambda.amazonaws.com')
        self.api_handler_iam_role = iam.Role(self, 'ApiHandlerLambdaRole',
                                             assumed_by=lambda_service_principal)

        self.dynamodb_table.grant_read_write_data(self.api_handler_iam_role)

        web_api_source_dir = self.node.try_get_context('web_api_source_dir')
        if not web_api_source_dir:
            raise WebApiError(
                'Path to web API source directory is missing. Please provide it '
                'using CDK context: cdk synth -c web_api_source_dir=PATH')
        chalice_stage_config = self._create_chalice_stage_config()
        self.chalice = Chalice(
            self, 'WebApi', source_dir=web_api_source_dir, python_version='3.6',
            stage_config=chalice_stage_config)

    def _create_chalice_stage_config(self):
        chalice_stage_config = {
            'api_gateway_stage': 'v1',
            'lambda_functions': {
                'api_handler': {
                    'manage_iam_role': False,
                    'iam_role_arn': self.api_handler_iam_role.role_arn,
                    'environment_variables': {
                        'DYNAMODB_TABLE_NAME': self.dynamodb_table.table_name
                    },
                    'lambda_memory_size': WebApi._API_HANDLER_LAMBDA_MEMORY_SIZE,
                    'lambda_timeout': WebApi._API_HANDLER_LAMBDA_TIMEOUT
                }
            }
        }

        return chalice_stage_config
```

# cdk-chalice
**AWS CDK construct for AWS Chalice**

Packages AWS Chalice application into AWS SAM format and enriches the resulting
SAM template with additional configuration values. The construct currently 
supports only API handler Lambda functions. It is possible to specify
IAM role for API handler Lambda function or let `cdk-chalice` create one.
Additional environment variables can be passed to the application. 

#### AWS Chalice application requirements
It is recommended that AWS Chalice application will have a CDK-specific
stage with settings to be used by the accompanying CDK stack. 

Chalice application must have a `Dockerfile.cdk` file, that should package the 
application to `/chalice.out`. The last line should be:
```dockerfile
RUN chalice package --stage cdk /chalice.out
```
`cdk-chalice` will use `Dockerfile.cdk` to package the application in a clean environment
and retrieve the resulting `deployment.zip` and `sam.json` files for further
processing.

#### Dockerfile.cdk example
```dockerfile
FROM python:3.7.5

WORKDIR /app

ENV AWS_DEFAULT_REGION eu-west-1

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN chalice package --stage cdk /chalice.out
```

#### Usage example
```python
from aws_cdk import (
    aws_dynamodb as dynamodb,
    core as cdk
)
from cdk_chalice import Chalice


class WebApiError(Exception):
    pass


class WebApi(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        partition_key = dynamodb.Attribute(name='username',
                                           type=dynamodb.AttributeType.STRING)
        dynamodb_table = dynamodb.Table(
            self, 'UsersTable', partition_key=partition_key,
            removal_policy=cdk.RemovalPolicy.DESTROY)
        cdk.CfnOutput(self, 'UsersTableName', value=dynamodb_table.table_name)

        web_api_source_dir = self.node.try_get_context('web_api_source_dir')
        if not web_api_source_dir:
            raise WebApiError('Please provide path to web API source directory '
                              'using "web_api_source_dir" context entry. For '
                              'example: cdk synth -c web_api_source_dir=PATH')
        chalice_app = Chalice(
            self, 'WebApi', source_dir=web_api_source_dir,
            api_handler_env_vars={'DYNAMODB_TABLE_NAME': dynamodb_table.table_name},
            cache_build=True)
        dynamodb_table.grant_read_write_data(chalice_app.api_handler_role)
```

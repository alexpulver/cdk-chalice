.. cdk-chalice documentation master file, created by
   sphinx-quickstart on Mon Dec 23 08:39:05 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to cdk-chalice's documentation!
=======================================

If you are looking for information on a specific class or method, this documentation is for you.

.. contents:: Table of Contents
    :local:
    :depth: 3

Chalice
~~~~~~~

.. autoclass:: cdk_chalice.Chalice
   :members:

   .. automethod:: __init__

PackageConfig
~~~~~~~~~~~~~
.. autoclass:: cdk_chalice.PackageConfig
   :members:

   .. automethod:: __init__

.. automodule:: cdk_chalice

Usage Example
~~~~~~~~~~~~~

Example of using Chalice class in a stack that creates a basic web API.

Note the customization of Chalice-generated resources using ``self.chalice.sam_template`` attribute. `cdk-chalice` uses
`aws_cdk.cloudformation_include <https://docs.aws.amazon.com/cdk/api/latest/docs/cloudformation-include-readme.html>`_
module to expose resources in the SAM template as native CDK objects. For example, ``rest_api`` variable below is an
instance of ``aws_cdk.aws_sam.CfnApi`` class. This capability allows to reference or customize Chalice application
resources within the broader CDK application.

The workflow for customization would be as follows:

* Implement the initial Chalice application using stage configuration (``stage_config``)
* Run ``cdk synth``
* Open the generated ``chalice.out/<package ID>/sam.json`` file, and find the logical ID of the relevant resource
* Retrieve the CDK object for the resource using ``self.chalice.sam_template.get_resource('<logical ID>')`` method

Any modifications made to the resource will be reflected in the resulting CDK template. ::

    import os

    from aws_cdk import (
        aws_dynamodb as dynamodb,
        aws_iam as iam,
        core as cdk
    )
    from cdk_chalice import Chalice


    class WebApi(cdk.Stack):

        _API_HANDLER_LAMBDA_MEMORY_SIZE = 128
        _API_HANDLER_LAMBDA_TIMEOUT = 10

        def __init__(self, scope: cdk.Construct, id: str, **kwargs)
                -> None:
            super().__init__(scope, id, **kwargs)

            partition_key = dynamodb.Attribute(
                name='username', type=dynamodb.AttributeType.STRING)
            self.dynamodb_table = dynamodb.Table(
                self, 'UsersTable', partition_key=partition_key,
                removal_policy=cdk.RemovalPolicy.DESTROY)
            cdk.CfnOutput(self, 'UsersTableName',
                          value=self.dynamodb_table.table_name)

            lambda_service_principal = iam.ServicePrincipal(
                'lambda.amazonaws.com')
            self.api_handler_iam_role = iam.Role(
                self, 'ApiHandlerLambdaRole',
                assumed_by=lambda_service_principal)

            self.dynamodb_table.grant_read_write_data(
                self.api_handler_iam_role)

            # Assuming 'web-api' is a relative directory in the same
            # project/repository
            web_api_source_dir = os.path.join(
                os.path.dirname(__file__), os.pardir, 'web-api')
            chalice_stage_config = self._create_chalice_stage_config()
            self.chalice = Chalice(
                self, 'WebApi', source_dir=web_api_source_dir,
                stage_config=chalice_stage_config)
            rest_api = self.chalice.sam_template.get_resource('RestAPI')
            rest_api.tracing_enabled = True

        def _create_chalice_stage_config(self):
            chalice_stage_config = {
                'api_gateway_stage': 'v1',
                'lambda_functions': {
                    'api_handler': {
                        'manage_iam_role': False,
                        'iam_role_arn':
                            self.api_handler_iam_role.role_arn,
                        'environment_variables': {
                            'DYNAMODB_TABLE_NAME':
                                self.dynamodb_table.table_name
                        },
                        'lambda_memory_size':
                            WebApi._API_HANDLER_LAMBDA_MEMORY_SIZE,
                        'lambda_timeout':
                            WebApi._API_HANDLER_LAMBDA_TIMEOUT
                    }
                }
            }

            return chalice_stage_config


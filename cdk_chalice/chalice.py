import json
import os
import tarfile
import tempfile
import uuid
from typing import Dict, Any

import docker
from aws_cdk import (
    aws_s3_assets as assets,
    aws_iam as iam,
    core as cdk
)


class Chalice(cdk.Construct):
    """
    Packages AWS Chalice application into AWS SAM format and enriches the resulting
    SAM template with additional configuration values.

    Currently supports only API handler Lambda functions. The construct requires
    Chalice application to have Dockerfile.cdk that should package the application
    to /chalice.out. I.e. the last line should be:

    ``RUN chalice package --stage cdk /chalice.out``
    """

    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str,
                 api_handler_env_vars: Dict[str, Any] = None,
                 api_handler_role: iam.IRole = None,
                 cache_build: bool = False, **kwargs) -> None:
        """
        :param str source_dir: Location of Chalice source code with Dockerfile.cdk
            Dockerfile.cdk should end with 'RUN chalice package --stage STAGE /chalice.out'
        :param Dict[str, Any] api_handler_env_vars: Environment variables to set for
            api_handler Lambda function
        :param iam.IRole api_handler_role: Existing IAM role for api_handler
            Lambda function. Will create a new IAM role if not specified
        :param bool cache_build: If set to True, will not cleanup Docker images
            created as part of Chalice package process, to speedup consequent builds
        """
        super().__init__(scope, id, **kwargs)

        self.source_dir = source_dir
        self.api_handler_env_vars = api_handler_env_vars
        if api_handler_role:
            self.api_handler_role = api_handler_role
        else:
            self.api_handler_role = self._create_iam_role()
        self.cache_build = cache_build

        chalice_out_dir = os.path.join(os.getcwd(), 'chalice.out')
        sam_package_dir = self._package_app(chalice_out_dir)
        sam_template = self._update_sam_template(sam_package_dir)

        cdk.CfnInclude(self, 'ChaliceApp', template=sam_template)

    def _package_app(self, chalice_out_dir: str) -> str:
        source_dir_realpath = os.path.realpath(self.source_dir)
        dockerfile_path = os.path.join(source_dir_realpath, 'Dockerfile.cdk')
        sam_package_dir = os.path.join(chalice_out_dir, uuid.uuid4().hex)

        client = docker.from_env()
        print('Building Chalice app')
        image, _ = client.images.build(path=source_dir_realpath, rm=True,
                                       dockerfile=dockerfile_path)
        print('Getting Chalice app build artifacts')
        container = client.containers.create(image)
        Chalice.get_dir_from_container(container, '/chalice.out', sam_package_dir)
        container.remove()
        if not self.cache_build:
            client.images.remove(image.id)

        return os.path.join(sam_package_dir, 'chalice.out')

    def _update_sam_template(self, sam_package_dir):
        deployment_zip_path = os.path.join(sam_package_dir, 'deployment.zip')
        sam_deployment_asset = assets.Asset(
            self, 'ChaliceAppCode', path=deployment_zip_path)
        sam_template_path = os.path.join(sam_package_dir, 'sam.json')

        with open(sam_template_path) as sam_template_file:
            sam_template = json.load(sam_template_file)
            properties = sam_template['Resources']['APIHandler']['Properties']
            properties['CodeUri'] = {
                'Bucket': sam_deployment_asset.s3_bucket_name,
                'Key': sam_deployment_asset.s3_object_key
            }
            properties['Role'] = self.api_handler_role.role_arn
            if self.api_handler_env_vars:
                properties['Environment']['Variables'] = self.api_handler_env_vars

        return sam_template

    def _create_iam_role(self):
        lambda_service_principal = iam.ServicePrincipal('lambda.amazonaws.com')

        return iam.Role(self, 'LambdaRole', assumed_by=lambda_service_principal)

    @staticmethod
    def get_dir_from_container(container, dir_path, target_path):
        with tempfile.NamedTemporaryFile() as temporary_file:
            stream, stat = container.get_archive(dir_path)
            for data in stream:
                temporary_file.write(data)
            temporary_file.seek(0)
            with tarfile.open(mode='r', fileobj=temporary_file) as tarobj:
                tarobj.extractall(path=target_path)

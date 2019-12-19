import json
import os
import uuid
from typing import Dict, Any

import docker
from aws_cdk import (
    aws_s3_assets as assets,
    core as cdk
)


class ChaliceError(Exception):
    pass


class Chalice(cdk.Construct):
    """
    Adds the provided stage configuration to SOURCE_DIR/.chalice/config.json.
    Stage name will be the string representation of current CDK scope.

    Packages the application into AWS SAM format and imports the resulting template
    into the construct tree under the provided scope.

    At this time, only API handler Lambda function is supported for deployment.
    Further work is required to automatically generate CDK assets for additional
    Lambda functions (e.g. triggered on SQS message).
    """

    _SUPPORTED_PYTHON_VERSIONS = ['2', '2.7', '3', '3.6', '3.7', '3.8']

    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str,
                 python_version: str, stage_config: Dict[str, Any],
                 **kwargs) -> None:
        """
        :param str source_dir: Location of Chalice source code with Dockerfile.cdk
            Dockerfile.cdk should end with 'RUN chalice package --stage STAGE /chalice.out'
        :param str python_version: Python version of the Chalice application
            Supported versions are 2, 2.7, 3, 3.6, 3.7, 3.8
        :param Dict[str, Any] stage_config: Chalice stage configuration.
            The configuration object should have the same structure as Chalice JSON
            stage configuration.
        """
        super().__init__(scope, id, **kwargs)

        self.source_dir = source_dir
        self.stage_name = scope.to_string()
        self.stage_config = stage_config
        if python_version not in Chalice._SUPPORTED_PYTHON_VERSIONS:
            raise ChaliceError(
                'Unsupported Python version. Supported versions are: '
                ', '.join(Chalice._SUPPORTED_PYTHON_VERSIONS)
            )
        else:
            self.python_version = python_version

        self._create_stage_with_config()

        chalice_out_dir = os.path.join(os.getcwd(), 'chalice.out')
        sam_package_dir = self._package_app(chalice_out_dir)
        sam_template = self._update_sam_template(sam_package_dir)

        cdk.CfnInclude(self, 'ChaliceApp', template=sam_template)

    def _create_stage_with_config(self):
        config_path = os.path.join(self.source_dir, '.chalice/config.json')
        with open(config_path, 'r+') as config_file:
            config = json.load(config_file)
            config['stages'][self.stage_name] = self.stage_config
            config_file.seek(0)
            config_file.write(json.dumps(config, indent=2))
            config_file.truncate()

    def _package_app(self, chalice_out_dir: str) -> str:
        source_dir_realpath = os.path.realpath(self.source_dir)
        sam_package_dir = os.path.join(chalice_out_dir, uuid.uuid4().hex)

        docker_image = f'python:{self.python_version}'
        docker_volumes = {
            source_dir_realpath: {'bind': '/app', 'mode': 'rw'},
            sam_package_dir: {'bind': '/chalice.out', 'mode': 'rw'}
        }
        docker_command = (
            'bash -c "pip install --no-cache-dir -r requirements.txt; '
            f'chalice package --stage {self.stage_name} /chalice.out"'
        )
        # Chalice requires AWS_DEFAULT_REGION to be set for package command.
        docker_environment = {'AWS_DEFAULT_REGION': 'us-east-1'}

        client = docker.from_env()
        print(f'Packaging Chalice app for {self.stage_name}')
        client.containers.run(
            docker_image, command=docker_command, environment=docker_environment,
            remove=True, volumes=docker_volumes, working_dir='/app')

        return sam_package_dir

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

        return sam_template

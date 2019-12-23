import json
import os
import shutil
import subprocess
import sys
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

    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str,
                 stage_config: Dict, use_container: bool = False, **kwargs) -> None:
        """
        :param str source_dir: Path to Chalice application source code
        :param Dict stage_config: Chalice stage configuration.
            The configuration object should have the same structure as Chalice JSON
            stage configuration.
        :param bool use_container: If your functions depend on packages that have
            natively compiled dependencies, use this flag to build the Chalice app
            inside an AWS Lambda-like Docker container
        :raises ChaliceError: Raised when an unsupported Python version is used
        """
        super().__init__(scope, id, **kwargs)

        self.source_dir = source_dir
        self.stage_name = scope.to_string()
        self.stage_config = stage_config
        self.use_container = use_container

        self._create_stage_with_config()
        sam_package_dir = self._package_app()
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

    def _package_app(self) -> str:
        chalice_out_dir = os.path.join(os.getcwd(), 'chalice.out')
        sam_package_dir = os.path.join(chalice_out_dir, uuid.uuid4().hex)
        # Chalice requires AWS_DEFAULT_REGION to be set for 'package' sub-command.
        env = {'AWS_DEFAULT_REGION': 'us-east-1'}

        if self.use_container:
            self._package_app_container(env, sam_package_dir)
        else:
            self._package_app_subprocess(env, sam_package_dir)

        return sam_package_dir

    def _package_app_container(self, env, sam_package_dir):
        python_version = f'{sys.version_info.major}.{sys.version_info.minor}'
        docker_image = f'lambci/lambda:build-python{python_version}'
        docker_volumes = {
            self.source_dir: {'bind': '/app', 'mode': 'rw'},
            sam_package_dir: {'bind': '/chalice.out', 'mode': 'rw'}
        }
        docker_command = (
            'bash -c "pip install --no-cache-dir -r requirements.txt; '
            f'chalice package --stage {self.stage_name} /chalice.out"'
        )

        client = docker.from_env()
        print(f'Packaging Chalice app for {self.stage_name}')
        try:
            client.containers.run(
                docker_image, command=docker_command, environment=env,
                remove=True, volumes=docker_volumes, working_dir='/app')
        except docker.errors.NotFound:
            message = (
                f'Unsupported Python version: {python_version}. See AWS Lambda '
                'Runtimes documentation for supported versions: '
                'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html'
            )
            raise ChaliceError(message)

    def _package_app_subprocess(self, env, sam_package_dir):
        chalice_exe = shutil.which('chalice')
        command = [chalice_exe, 'package', '--stage', self.stage_name, sam_package_dir]

        print(f'Packaging Chalice app for {self.stage_name}')
        subprocess.run(command, cwd=self.source_dir, env=env)

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

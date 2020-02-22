import json
import os
import shutil
import subprocess
import sys
import uuid
from typing import Dict

import docker
from aws_cdk import (
    aws_s3_assets as assets,
    core as cdk
)


_AWS_DEFAULT_REGION = 'us-east-1'


class DockerConfig:
    """Docker configuration for packaging Chalice app in a container environment.

    The default image closely mimics AWS Lambda execution environment, but you can
    also specify your own. If a custom container image is used, it is the owner
    responsibility to make sure it mimics Lambda execution environment.
    """

    def __init__(self, image: str = None, env: dict = None) -> None:
        """
        :param str image: Docker image name.
            Defaults to image that closely mimics AWS Lambda execution environment.
        :param Dict[str,str] env: Environment variables to set inside the container.
            AWS_DEFAULT_REGION is set to 'us-east-1' unless explicitly specified.
        """
        if image is None:
            python_version = f'{sys.version_info.major}.{sys.version_info.minor}'
            self.image = f'lambci/lambda:build-python{python_version}'
        else:
            self.image = image

        self.env = env if env is not None else {}
        # Chalice requires AWS_DEFAULT_REGION to be set for 'package' sub-command.
        self.env.setdefault('AWS_DEFAULT_REGION', _AWS_DEFAULT_REGION)


class ChaliceError(Exception):
    pass


class Chalice(cdk.Construct):
    """
    Adds the provided stage configuration to SOURCE_DIR/.chalice/config.json.
    Stage name will be the string representation of current CDK scope.

    Packages the application into AWS SAM format and imports the resulting template
    into the construct tree under the provided scope.
    """

    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str,
                 stage_config: Dict, docker_config: DockerConfig = None,
                 **kwargs) -> None:
        """
        :param str source_dir: Path to Chalice application source code
        :param Dict stage_config: Chalice stage configuration.
            The configuration object should have the same structure as Chalice JSON
            stage configuration.
        :param DockerConfig docker_config: If your functions depend on packages
            that have natively compiled dependencies, build your functions inside
            an AWS Lambda-like Docker container (or your own container).
        :raises ChaliceError: Error packaging the application.
        """
        super().__init__(scope, id, **kwargs)

        self.source_dir = source_dir
        self.stage_name = scope.to_string()
        self.stage_config = stage_config
        self.docker_config = docker_config

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

        if self.docker_config is not None:
            self._package_app_container(sam_package_dir)
        else:
            self._package_app_subprocess(sam_package_dir)

        return sam_package_dir

    def _package_app_container(self, sam_package_dir):
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
                self.docker_config.image, command=docker_command,
                environment=self.docker_config.env, remove=True,
                volumes=docker_volumes, working_dir='/app')
        except docker.errors.NotFound:
            message = (
                f'Could not find the specified Docker image: {self.docker_config.image}. '
                'When using the default lambci/lambda images, make sure your Python '
                'version is supported. See AWS Lambda Runtimes documentation for '
                'supported versions: '
                'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html'
            )
            raise ChaliceError(message)

    def _package_app_subprocess(self, sam_package_dir):
        chalice_exe = shutil.which('chalice')
        command = [chalice_exe, 'package', '--stage', self.stage_name, sam_package_dir]
        # Chalice requires AWS_DEFAULT_REGION to be set for 'package' sub-command.
        env = {'AWS_DEFAULT_REGION': _AWS_DEFAULT_REGION}

        print(f'Packaging Chalice app for {self.stage_name}')
        subprocess.run(command, cwd=self.source_dir, env=env)

    def _update_sam_template(self, sam_package_dir):
        deployment_zip_path = os.path.join(sam_package_dir, 'deployment.zip')
        sam_deployment_asset = assets.Asset(
            self, 'ChaliceAppCode', path=deployment_zip_path)
        sam_template_path = os.path.join(sam_package_dir, 'sam.json')

        with open(sam_template_path) as sam_template_file:
            sam_template = json.load(sam_template_file)
            functions = filter(
                lambda resource: resource['Type'] == 'AWS::Serverless::Function',
                sam_template['Resources'].values()
            )
            for function in functions:
                function['Properties']['CodeUri'] = {
                    'Bucket': sam_deployment_asset.s3_bucket_name,
                    'Key': sam_deployment_asset.s3_object_key
                }

        return sam_template

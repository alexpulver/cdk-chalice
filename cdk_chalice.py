# pylint: disable=missing-module-docstring

import json
import os
import shutil
import subprocess  # nosec
import sys
import uuid
from typing import Dict

import docker
from aws_cdk import (
    aws_s3_assets as assets,
    core as cdk
)


_AWS_DEFAULT_REGION = 'us-east-1'


# pylint: disable=too-few-public-methods
# Using a class and not a dictionary/namedtuple to provide a default behavior object
# and ease of configuration for Chalice class consumers.
class PackageConfig:
    """Configuration for packaging Chalice app.

    If your functions depend on packages that have natively compiled dependencies,
    build your functions inside a Docker container. In order to instruct
    :class:`Chalice` class to do so, set :attr:`use_container` to ``True``.

    When packaging the Chalice app in Docker container, the default image closely
    mimics AWS Lambda execution environment. If a custom container image is used,
    it is the owner responsibility to make sure it mimics Lambda execution environment.
    """

    # pylint: disable=bad-whitespace
    # Dict[str,str] with spaces is not parsed correctly by Sphinx.
    def __init__(self, use_container: bool = False, image: str = None,
                 env: Dict[str,str] = None) -> None:  # noqa: E231
        """
        :param bool use_container: Package the Chalice app in Docker container.
        :param str image: Docker image name.
            Defaults to image that closely mimics AWS Lambda execution environment.
        :param Dict[str,str] env: Environment variables to set for packaging.
            ``AWS_DEFAULT_REGION`` is set to ``us-east-1`` unless explicitly
            specified otherwise.
        """
        python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

        #: If ``True``, package the Chalice app in Docker container. By default
        #: packages the app in subprocess.
        self.use_container = use_container

        #: Docker image name. Used when :attr:`use_container` is set to ``True``.
        self.image = f'lambci/lambda:build-python{python_version}'
        if image is not None:
            self.image = image

        #: Environment variables used during packaging.
        self.env = env if env is not None else {}
        self.env.setdefault('AWS_DEFAULT_REGION', _AWS_DEFAULT_REGION)


class ChaliceError(Exception):
    """Chalice exception."""


class Chalice(cdk.Construct):
    """Chalice construct.

    Adds the provided stage configuration to :attr:`source_dir`/.chalice/config.json.
    Stage name will be the string representation of current CDK ``scope``.

    Packages the application into AWS SAM format and imports the resulting template
    into the construct tree under the provided ``scope``.
    """

    # pylint: disable=redefined-builtin
    # The 'id' parameter name is CDK convention.
    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str, stage_config: dict,
                 package_config: PackageConfig = None, **kwargs) -> None:
        """
        :param str source_dir: Path to Chalice application source code.
        :param dict stage_config: Chalice stage configuration.
            The configuration object should have the same structure as Chalice JSON
            stage configuration.
        :param `PackageConfig` package_config: Configuration for packaging the
            Chalice application.
        :raises `ChaliceError`: Error packaging the Chalice application.
        """
        super().__init__(scope, id, **kwargs)

        #: Path to Chalice application source code.
        self.source_dir = os.path.abspath(source_dir)

        #: Chalice stage name.
        #: It is automatically assigned the encompassing CDK ``scope``'s name.
        self.stage_name = scope.to_string()

        #: Chalice stage configuration.
        #: The object has the same structure as Chalice JSON stage configuration.
        self.stage_config = stage_config

        #: :class:`PackageConfig` object.
        #: If not provided, :class:`PackageConfig` instance with default arguments is used.
        self.package_config = PackageConfig() if package_config is None else package_config

        self._create_stage_with_config()

        #: Path to directory with output of `chalice package` command.
        self.sam_package_dir = self._package_app()

        #: AWS SAM template updated with AWS CDK values where applicable.
        self.sam_template = self._update_sam_template()

        cdk.CfnInclude(self, 'ChaliceApp', template=self.sam_template)

    def _create_stage_with_config(self):
        config_path = os.path.join(self.source_dir, '.chalice/config.json')
        with open(config_path, 'r+') as config_file:
            config = json.load(config_file)
            if 'stages' not in config:
                config['stages'] = {}
            config['stages'][self.stage_name] = self.stage_config
            config_file.seek(0)
            config_file.write(json.dumps(config, indent=2))
            config_file.truncate()

    def _package_app(self) -> str:
        chalice_out_dir = os.path.join(os.getcwd(), 'chalice.out')
        sam_package_dir = os.path.join(chalice_out_dir, uuid.uuid4().hex)

        print(f'Packaging Chalice app for {self.stage_name}')
        if self.package_config.use_container:
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
        try:
            client.containers.run(
                self.package_config.image, command=docker_command,
                environment=self.package_config.env, remove=True,
                volumes=docker_volumes, working_dir='/app')
        except docker.errors.NotFound:
            message = (
                f'Could not find the specified Docker image: {self.package_config.image}. '
                'When using the default lambci/lambda images, make sure your Python '
                'version is supported. See AWS Lambda Runtimes documentation for '
                'supported versions: '
                'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html'
            )
            raise ChaliceError(message)
        finally:
            client.close()

    def _package_app_subprocess(self, sam_package_dir):
        chalice_exe = shutil.which('chalice')
        command = [chalice_exe, 'package', '--stage', self.stage_name, sam_package_dir]

        subprocess.run(command, check=True, cwd=self.source_dir,  # nosec
                       env=self.package_config.env)

    def _update_sam_template(self):
        deployment_zip_path = os.path.join(self.sam_package_dir, 'deployment.zip')
        sam_deployment_asset = assets.Asset(
            self, 'ChaliceAppCode', path=deployment_zip_path)
        sam_template_path = os.path.join(self.sam_package_dir, 'sam.json')

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

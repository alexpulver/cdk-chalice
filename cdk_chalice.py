# pylint: disable=missing-module-docstring

import json
import os
import shutil
import subprocess  # nosec
import sys
from typing import Dict

import docker
from aws_cdk import (
    aws_s3_assets as assets,
    cloudformation_include,
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

        #: (:class:`bool`) If ``True``, package the Chalice app in Docker container.
        #: By default packages the app in subprocess.
        self.use_container = use_container

        #: (:class:`str`) Docker image name. Used when :attr:`use_container` is set
        #: to ``True``.
        self.image = f'lambci/lambda:build-python{python_version}'
        if image is not None:
            self.image = image

        #: (:class:`Dict[str,str]`) Environment variables used during packaging.
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
    def __init__(self, scope: cdk.Construct, id: str, *, source_dir: str,
                 stage_config: dict, package_config: PackageConfig = None,
                 preserve_logical_ids: bool = True, **kwargs) -> None:
        """
        :param str source_dir: Path to Chalice application source code.
        :param dict stage_config: Chalice stage configuration.
            The configuration object should have the same structure as Chalice JSON
            stage configuration.
        :param `PackageConfig` package_config: Configuration for packaging the
            Chalice application.
        :param bool preserve_logical_ids: Whether the resources should have the same
            logical IDs in the resulting CDK template as they did in the original
            CloudFormation template file. If you’re vending a Construct using cdk-chalice,
            make sure to pass this as ``False``. Note: regardless of whether this option
            is true or false, the :attr:`sam_template`'s ``get_resource`` and related
            methods always uses the original logical ID of the resource/element, as
            specified in the template file.
        :raises `ChaliceError`: Error packaging the Chalice application.
        """
        super().__init__(scope, id, **kwargs)

        #: (:class:`str`) Path to Chalice application source code.
        self.source_dir = os.path.abspath(source_dir)

        #: (:class:`str`) Chalice stage name.
        #: It is automatically assigned the encompassing CDK ``scope``'s name.
        self.stage_name = scope.to_string()

        #: (:class:`dict`) Chalice stage configuration.
        #: The object has the same structure as Chalice JSON stage configuration.
        self.stage_config = stage_config

        #: (:class:`PackageConfig`) If not provided, :class:`PackageConfig`
        #: instance with default arguments is used.
        self.package_config = PackageConfig() if package_config is None \
            else package_config

        self._create_stage_with_config()

        chalice_out_dir = os.path.join(os.getcwd(), 'chalice.out')
        package_id = self.node.path.replace('/', '')
        self._sam_package_dir = os.path.join(chalice_out_dir, package_id)

        self._package_app()
        sam_template_with_assets_file = self._generate_sam_template_with_assets(
            chalice_out_dir, package_id)

        #: (:class:`aws_cdk.cloudformation_include.CfnInclude`) AWS SAM template
        #: updated with AWS CDK values where applicable. Can be used to reference,
        #: access, and customize resources generated by `chalice package` command
        #: as CDK native objects.
        self.sam_template = cloudformation_include.CfnInclude(
            self, 'ChaliceApp', template_file=sam_template_with_assets_file,
            preserve_logical_ids=preserve_logical_ids)

    def _create_stage_with_config(self) -> None:
        config_path = os.path.join(self.source_dir, '.chalice/config.json')
        with open(config_path, 'r+') as config_file:
            config = json.load(config_file)
            if 'stages' not in config:
                config['stages'] = {}
            config['stages'][self.stage_name] = self.stage_config
            config_file.seek(0)
            config_file.write(json.dumps(config, indent=2))
            config_file.truncate()

    def _package_app(self) -> None:
        print(f'Packaging Chalice app for {self.stage_name}', flush=True)
        if self.package_config.use_container:
            self._package_app_container()
        else:
            self._package_app_subprocess()

    def _package_app_container(self) -> None:
        docker_volumes = {
            self.source_dir: {'bind': '/app', 'mode': 'rw'},
            self._sam_package_dir: {'bind': '/chalice.out', 'mode': 'rw'}
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
        except docker.errors.NotFound as not_found_error:
            message = (
                f'Could not find the specified Docker image: {self.package_config.image}. '
                'When using the default lambci/lambda images, make sure your Python '
                'version is supported. See AWS Lambda Runtimes documentation for '
                'supported versions: '
                'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html'
            )
            raise ChaliceError(message) from not_found_error
        finally:
            client.close()

    def _package_app_subprocess(self) -> None:
        chalice_exe = shutil.which('chalice')
        command = [chalice_exe, 'package', '--stage', self.stage_name,
                   self._sam_package_dir]

        subprocess.run(command, check=True, cwd=self.source_dir,  # nosec
                       env=self.package_config.env)

    def _generate_sam_template_with_assets(
            self, chalice_out_dir: str, package_id: str) -> str:
        deployment_zip_path = os.path.join(self._sam_package_dir, 'deployment.zip')
        sam_deployment_asset = assets.Asset(
            self, 'ChaliceAppCode', path=deployment_zip_path)
        sam_template_path = os.path.join(self._sam_package_dir, 'sam.json')
        sam_template_with_assets_path = os.path.join(
            chalice_out_dir, f'{package_id}.sam_with_assets.json')

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
        with open(sam_template_with_assets_path, 'w') as sam_template_with_assets_file:
            sam_template_with_assets_file.write(json.dumps(sam_template, indent=2))

        return sam_template_with_assets_path

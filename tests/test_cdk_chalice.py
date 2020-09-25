import json
import os
import shutil
import tempfile
import unittest

from aws_cdk import core as cdk

from cdk_chalice import Chalice, ChaliceError, PackageConfig


class ChaliceTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(dir='/tmp')
        os.chdir(self.temp_dir)

        self.cdk_out_dir = os.path.join(self.temp_dir, 'cdk.out')
        self.chalice_out_dir = os.path.join(self.temp_dir, 'chalice.out')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'chalice_app'),
                        os.path.join(self.temp_dir, 'chalice_app'))
        self.chalice_app_dir = os.path.join(self.temp_dir, 'chalice_app')
        self.chalice_app_deployments_dir = os.path.join(
            self.chalice_app_dir, '.chalice', 'deployments')
        self.chalice_app_config_file = os.path.join(
            self.chalice_app_dir, '.chalice', 'config.json')
        self.chalice_app_stage_config = {
            'api_gateway_stage': 'v1'
        }

        with open(self.chalice_app_config_file, 'w') as config_file:
            chalice_app_config = {
                'version': '2.0',
                'app_name': 'chalice',
            }
            json.dump(chalice_app_config, config_file, indent=2)

    def tearDown(self) -> None:
        os.chdir('/tmp')
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_package_using_subprocess(self) -> None:
        app = cdk.App(outdir=self.cdk_out_dir)
        stack = cdk.Stack(app, 'TestSubprocess')
        chalice = Chalice(stack, 'WebApi',
                          source_dir=self.chalice_app_dir,
                          stage_config=self.chalice_app_stage_config)
        template = self._synth_and_get_template(app, chalice)
        self._check_basic_asserts(chalice, template)

    def test_package_using_docker(self) -> None:
        app = cdk.App(outdir=self.cdk_out_dir)
        stack = cdk.Stack(app, 'TestDocker')
        package_config = PackageConfig(use_container=True)
        chalice = Chalice(stack, 'WebApi',
                          source_dir=self.chalice_app_dir,
                          stage_config=self.chalice_app_stage_config,
                          package_config=package_config)
        template = self._synth_and_get_template(app, chalice)
        self._check_basic_asserts(chalice, template)

    def test_package_using_docker_image_not_found(self) -> None:
        app = cdk.App(outdir=self.cdk_out_dir)
        stack = cdk.Stack(app, 'TestDockerImageNotFound')
        package_config = PackageConfig(use_container=True, image='cdk-chalice')
        with self.assertRaises(ChaliceError):
            Chalice(stack, 'WebApi', source_dir=self.chalice_app_dir,
                    stage_config=self.chalice_app_stage_config,
                    package_config=package_config)

    def test_cloudformation_include(self) -> None:
        app = cdk.App(outdir=self.cdk_out_dir)
        stack = cdk.Stack(app, 'TestCloudformationInclude')
        chalice = Chalice(stack, 'WebApi',
                          source_dir=self.chalice_app_dir,
                          stage_config=self.chalice_app_stage_config)
        rest_api = chalice.sam_template.get_resource('RestAPI')
        rest_api.tracing_enabled = True
        template = self._synth_and_get_template(app, chalice)
        self.assertEqual(
            template['Resources']['RestAPI']['Properties']['TracingEnabled'],
            True
        )

    @staticmethod
    def _synth_and_get_template(app: cdk.App, chalice: Chalice) -> dict:
        cloud_assembly = app.synth()

        chalice_stack_name = cdk.Stack.of(chalice).stack_name
        template = cloud_assembly.get_stack_by_name(chalice_stack_name).template

        return template

    def _check_basic_asserts(self, chalice, template) -> None:
        self.assertTrue(os.path.exists(chalice.sam_package_dir))
        self.assertIsNotNone(chalice.sam_template)
        self.assertNotEqual(
            template['Resources']['APIHandler']['Properties']['CodeUri'],
            './deployment.zip'
        )


if __name__ == '__main__':
    unittest.main()

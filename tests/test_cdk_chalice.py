import json
import os
import shutil
import unittest

from aws_cdk import core as cdk

from cdk_chalice import Chalice, PackageConfig


class ChaliceTestCase(unittest.TestCase):

    CDK_OUT_DIR = os.path.abspath(os.path.join(os.getcwd(), 'cdk.out'))
    CHALICE_OUT_DIR = os.path.abspath(os.path.join(os.getcwd(), 'chalice.out'))
    CHALICE_APP_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'chalice_app'))
    CHALICE_APP_DEPLOYMENTS_DIR = os.path.abspath(
        os.path.join(CHALICE_APP_DIR, '.chalice', 'deployments'))
    CHALICE_APP_CONFIG_FILE = os.path.abspath(
        os.path.join(CHALICE_APP_DIR, '.chalice', 'config.json'))
    CHALICE_APP_STAGE_CONFIG = {
        'api_gateway_stage': 'v1'
    }

    def setUp(self) -> None:
        with open(ChaliceTestCase.CHALICE_APP_CONFIG_FILE, 'w') as config_file:
            chalice_app_config = {
                'version': '2.0',
                'app_name': 'test',
            }
            json.dump(chalice_app_config, config_file, indent=2)

    def tearDown(self) -> None:
        shutil.rmtree(ChaliceTestCase.CDK_OUT_DIR)
        shutil.rmtree(ChaliceTestCase.CHALICE_OUT_DIR)
        shutil.rmtree(ChaliceTestCase.CHALICE_APP_DEPLOYMENTS_DIR)
        os.remove(ChaliceTestCase.CHALICE_APP_CONFIG_FILE)

    def test_package_using_subprocess(self) -> None:
        app = cdk.App(outdir=ChaliceTestCase.CDK_OUT_DIR)
        stack = cdk.Stack(app, 'Stack')
        chalice = Chalice(stack, 'TestPackageUsingSubprocess',
                          source_dir=ChaliceTestCase.CHALICE_APP_DIR,
                          stage_config=ChaliceTestCase.CHALICE_APP_STAGE_CONFIG)
        self._synth_and_assert(app, chalice)

    def test_package_using_docker(self) -> None:
        app = cdk.App(outdir=ChaliceTestCase.CDK_OUT_DIR)
        stack = cdk.Stack(app, 'Stack')
        package_config = PackageConfig(use_container=True)
        chalice = Chalice(stack, 'TestPackageUsingSubprocess',
                          source_dir=ChaliceTestCase.CHALICE_APP_DIR,
                          stage_config=ChaliceTestCase.CHALICE_APP_STAGE_CONFIG,
                          package_config=package_config)
        self._synth_and_assert(app, chalice)

    def _synth_and_assert(self, app: cdk.App, chalice: Chalice) -> None:
        cloud_assembly = app.synth()
        cloudformation_template = cloud_assembly.get_stack_by_name('Stack').template
        self.assertTrue(os.path.exists(chalice.sam_package_dir))
        self.assertIsNotNone(chalice.sam_template)
        self.assertNotEqual(
            cloudformation_template['Resources']['APIHandler']['Properties']['CodeUri'],
            './deployment.zip'
        )


if __name__ == '__main__':
    unittest.main()

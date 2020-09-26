# cdk-chalice

[![PyPI Version](https://badge.fury.io/py/cdk-chalice.svg)](https://badge.fury.io/py/cdk-chalice)
![PythonSupport](https://img.shields.io/static/v1?label=python&message=3.6%20|%203.7%20|%203.8&color=blue?style=flat-square&logo=python)
[![PyPI status](https://img.shields.io/pypi/status/cdk-chalice.svg)](https://pypi.python.org/pypi/cdk-chalice/)
[![Downloads](https://pepy.tech/badge/cdk-chalice/month)](https://pypi.org/project/cdk-chalice)
[![Build Status](https://travis-ci.com/alexpulver/cdk-chalice.svg?branch=master)](https://travis-ci.com/alexpulver/cdk-chalice)
[![codecov](https://codecov.io/gh/alexpulver/cdk-chalice/branch/master/graph/badge.svg)](https://codecov.io/gh/alexpulver/cdk-chalice)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=alexpulver_cdk-chalice&metric=alert_status)](https://sonarcloud.io/dashboard?id=alexpulver_cdk-chalice)
[![Contributors](https://img.shields.io/github/contributors/alexpulver/cdk-chalice.svg)](https://github.com/alexpulver/cdk-chalice/graphs/contributors)

**AWS CDK construct for AWS Chalice**

This library allows to include an [AWS Chalice](https://aws.github.io/chalice/) 
application into a broader [AWS Cloud Development Kit](https://docs.aws.amazon.com/cdk/latest/guide/home.html)
(AWS CDK) application.

The following approach to AWS CDK and AWS Chalice interoperability is taken by the library:

1. **Manually create Chalice application (`chalice new-project`) with default "dev" stage in
   `.chalice/config.json`.** `cdk-chalice` library could perform this Chalice application 
   scaffolding automatically - create new project, or skip this step if project already exists 
   in the target directory (this is `chalice new-project` behavior). The choice to keep this step 
   manual (for now) was made to hopefully make adoption easier for developers who already have 
   existing Chalice projects.

2. **Manually create CDK application (`cdk init [ARGS]`)**

3. **Use `cdk_chalice.Chalice` class to generate stage per CDK stack in `.chalice/config.json` 
   and run `chalice package`**. This is the main purpose of `cdk-chalice` - allow passing 
   CDK tokens for resources, such as DynamoDB table, to SAM template generated by `chalice package` 
   (see example [here](https://github.com/alexpulver/aws-cdk-sam-chalice/blob/master/web-api/.chalice/config.json)), 
   and also to automate the packaging process itself.

If AWS Chalice doesn't support certain options through its configuration mechanism, 
there are two ways to address this:
- Open an [issue](https://github.com/aws/chalice/issues) for AWS Chalice
- Customize the resources after they have been imported into the CDK stack. `cdk-chalice` uses AWS CDK 
  [`cloudformation-include`](https://docs.aws.amazon.com/cdk/api/latest/docs/cloudformation-include-readme.html) 
  module to enable customization. See `cdk-chalice` API documentation for example and additional details.

The API documentation and usage example are available at https://cdk-chalice.softwhat.com/

**Installation**

Install and update using [pip](https://pip.pypa.io/en/stable/installing/):
```bash
pip install -U cdk-chalice
```

#!/usr/bin/env python

from setuptools import setup


long_description = open('README.md', 'r', encoding='utf-8').read()


setup(
    name='cdk-chalice',

    version='0.5.0',

    description='AWS CDK construct for AWS Chalice',

    url='https://github.com/alexpulver/cdk-chalice',

    author='Alex Pulver',
    author_email='alex.pulver@gmail.com',

    license='MIT License',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: JavaScript',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Topic :: Software Development :: Code Generators',
        'Topic :: Utilities',

        'Typing :: Typed',
    ],

    packages=['cdk_chalice'],

    install_requires=[
        'aws_cdk.aws_iam>=1.18.0',
        'aws_cdk.aws_s3_assets>=1.18.0',
        'aws_cdk.core>=1.18.0',
        'docker'
    ],

    python_requires='>=3.6',

    tests_require=['coverage'],
    test_suite='tests',
)

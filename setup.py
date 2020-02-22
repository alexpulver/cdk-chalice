#!/usr/bin/env python

import os
from setuptools import setup


about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'about.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],

    version=about['__version__'],

    description=about['__description__'],

    url=about['__url__'],

    author=about['__author__'],
    author_email=about['__author_email__'],

    license=about['__license__'],

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

    py_modules=['cdk_chalice'],

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

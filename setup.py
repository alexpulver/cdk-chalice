#!/usr/bin/env python

import os
from setuptools import setup


about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'about.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)

with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    author=about['__author__'],
    author_email=about['__author_email__'],
    classifiers=[
        'Development Status :: 4 - Beta',
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
    description=about['__description__'],
    install_requires=[
        'aws_cdk.aws_iam>=1.18.0',
        'aws_cdk.aws_s3_assets>=1.18.0',
        'aws_cdk.core>=1.18.0',
        'docker'
    ],
    license=about['__license__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    name=about['__title__'],
    py_modules=['cdk_chalice'],
    python_requires='>=3.6',
    tests_require=['coverage'],
    test_suite='tests',
    url=about['__url__'],
    version=about['__version__'],
)

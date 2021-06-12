#!/bin/bash

set -o errexit
set -o verbose

black --check --diff .
flake8 --config .flake8
pylint --rcfile .pylintrc cdk_chalice.py
bandit --ini .bandit
coverage run --rcfile .coveragerc

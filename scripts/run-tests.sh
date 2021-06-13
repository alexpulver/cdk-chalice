#!/bin/bash

set -o errexit
set -o verbose

bandit --ini .bandit
black --check --diff .  # There is no configuration file for Black
flake8 --config .flake8
isort --settings-path .isort.cfg --check --diff .
pylint --rcfile .pylintrc cdk_chalice.py

coverage run --rcfile .coveragerc

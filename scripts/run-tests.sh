#!/bin/bash

set -o errexit
set -o verbose

flake8
pylint cdk_chalice.py
bandit --ini .bandit
coverage run

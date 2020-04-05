#!/bin/bash

set -ev

flake8
pylint cdk_chalice.py
bandit --ini .bandit
coverage run

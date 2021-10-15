#!/bin/bash

set -o errexit
set -o verbose

# Install project dependencies
pip install pip-tools==6.4.0
pip-sync requirements.txt requirements-dev.txt

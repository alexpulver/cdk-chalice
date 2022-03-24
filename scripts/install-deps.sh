#!/bin/bash

set -o errexit
set -o verbose

# Install project dependencies
# Pinning pip-tools to 6.4.0 and pip to 21.3.1 due to
# https://github.com/jazzband/pip-tools/issues/1576
pip install pip-tools==6.4.0
pip install pip==21.3.1
pip-sync requirements.txt requirements-dev.txt

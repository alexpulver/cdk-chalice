#!/bin/bash

set -o errexit

if [ -z "$1" ]; then
  echo "Usage: bump-version.sh {major|minor|patch}"
  exit 1
fi

if [ "$1" != "major" ] && [ "$1" != "minor" ] && [ "$1" != "patch" ]; then
  echo "Wrong semantic version part"
  echo
  echo "Usage: bump-version.sh {major|minor|patch}"
  exit 1
fi

bump_part=$1

eval "changelog release --${bump_part}"
version=$(changelog current)
git commit -m "Bump change log version to: ${version}" CHANGELOG.md

bumpversion "${bump_part}"

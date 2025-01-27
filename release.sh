#!/bin/bash

rm -rf dist
set -e

# Check arguments
if [ $# -ne 1 ]; then
  echo "Usage: ./release.sh <version-part>"
  echo "Example: ./release.sh minor"
  exit 1
fi

# Bump version (patch, minor, major)
bump2version $1

# Push changes and tags to GitHub
git push origin main --tags

# Build and upload to PyPI
python -m build
twine upload dist/*

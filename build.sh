#!/usr/bin/env bash
set -o errexit

# Tell Render explicitly to use Python 3.11
export PYTHON_VERSION=3.11.9

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
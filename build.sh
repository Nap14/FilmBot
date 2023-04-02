#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python database/manage.py migrate

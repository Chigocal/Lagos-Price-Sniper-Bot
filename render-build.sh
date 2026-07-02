#!/bin/bash
set -o errexit

pip install -r requirements.txt

apt-get update
playwright install chromium
playwright install-deps chromium

mkdir -p data
#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create the data directory for your JSON files
mkdir -p data

# Install ONLY the Chromium browser (No apt-get or system deps)
playwright install chromium
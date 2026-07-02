#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create the data directory for your JSON files
mkdir -p data

# Force install ALL playwright browsers to ensure the headless shell is included
playwright install
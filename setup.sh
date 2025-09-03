#!/bin/bash
set -e

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install system dependencies if needed
# sudo apt-get update && sudo apt-get install -y python3-dev

# Install Python packages with pip
export PIP_NO_CACHE_DIR=off
export PIP_DISABLE_PIP_VERSION_CHECK=on

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install --no-cache-dir --only-binary :all: -r requirements.txt

echo "Installation complete!"

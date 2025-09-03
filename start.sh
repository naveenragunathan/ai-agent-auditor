#!/bin/bash
set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if not already installed
if [ ! -d "venv" ]; then
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Run the FastAPI app with Uvicorn
echo "Starting server on 0.0.0.0:${PORT:-8000}..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level debug

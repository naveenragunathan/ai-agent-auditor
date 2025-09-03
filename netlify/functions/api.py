import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from main import app
from mangum import Mangum

# Create the handler for Netlify Functions
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """Netlify Functions handler"""
    return handler(event, context)

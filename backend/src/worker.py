"""
Cloudflare Workers entrypoint for Django application
"""
import sys
import os

# Add vendor directory to Python path for dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from django_cf import DjangoCF

# Initialize Django application once at module level
try:
    from slotlist_backend.wsgi import application
    # Create DjangoCF instance once
    django_cf = DjangoCF(application)
except Exception as e:
    # Log initialization error for debugging
    print(f"Django initialization error: {e}")
    raise

async def on_fetch(request, env):
    """
    Main entrypoint for Cloudflare Workers
    """
    # Use the pre-initialized Django application
    return await django_cf.handle_request(request, env)
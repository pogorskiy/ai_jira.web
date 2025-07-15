# app/__init__.py

"""
Package initialization for the FastAPI application.
Loads the .env file so that environment variables (e.g. DATABASE_URL)
are available before any other modules import os.getenv().
"""

from dotenv import load_dotenv, find_dotenv

# Search for a .env file starting from the current directory upward
load_dotenv(find_dotenv())
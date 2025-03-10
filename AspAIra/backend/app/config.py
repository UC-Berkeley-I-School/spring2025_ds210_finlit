"""
Configuration settings for the AspAIra application.
"""
from typing import Dict

# Dify Credentials Setup:
# 1. API Key (needs to be set):
#    - Create in Dify dashboard under "API Keys"
#    - Starts with "app-"
#    - Example: app-1sc0QKSxc2rXRTQNRvLM4Ktk

# Agent configurations
AGENT_CONFIGS = {
    "dify": {
        "v1": {
            "api_key": "app-1sc0QKSxc2rXRTQNRvLM4Ktk",  # Local Dify API key
            "base_url": "http://localhost",  # Updated to use HTTP for local development
            "model": "gpt-4o-mini",
            "required_inputs": [
                "dependents_count",
                "bank_account",
                "debt_status",
                "remittance_status",
                "remittance_amount"
            ]
        }
    }
}

# Default configurations
DEFAULT_AGENT = "dify"
DEFAULT_VERSION = "v1"

# Database configuration
DATABASE_CONFIG = {
    "table_name": "chat_interactions",
    "region": "us-east-1"
}

# API configuration
API_CONFIG = {
    "title": "AspAIra API",
    "description": "API for AspAIra financial coaching application",
    "version": "1.0.0",
    "debug": True
}

# Default version to use
DEFAULT_DIFY_VERSION = 'v1' 
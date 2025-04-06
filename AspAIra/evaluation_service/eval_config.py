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
    "eval_gpt": {
        "api_key": "app-664Y5hBz9w920Wk8Jb6XneF6",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "gpt-4-turbo"
        },
    "eval_claude": {
        "api_key": "app-vrvVKNIRXX8W0E8mBmAj3m17",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "claude-3-opus-20240229"
    },
    "eval_gemini": {
        "api_key": "app-4pOWFyQndXm6Ao68S1YBppKx",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "gemini-pro",
    }
}

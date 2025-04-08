"""
Configuration settings for the AspAIra application.
"""
import os
from typing import Dict

# Dify Credentials Setup:
# 1. API Key (needs to be set):
#    - Create in Dify dashboard under "API Keys"
#    - Starts with "app-"
#    - Example: app-1sc0QKSxc2rXRTQNRvLM4Ktk

# Agent configurations
AGENT_CONFIGS = {
    "eval_gpt": {
        "api_key": os.getenv("EVAL_GPT_API_KEY", "app-local-default"),  # Local Dify API key
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),  # Updated to use HTTP for local development
        "model": "gpt-3.5-turbo"
        },
    "eval_claude": {
        "api_key": os.getenv("EVAL_CLAUDE_API_KEY", "app-local-default"),  # Local Dify API key
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),  # Updated to use HTTP for local development
        "model": "claude-3-opus-20240229"
    },
    "eval_gemini": {
        "api_key": os.getenv("EVAL_GEMINI_API_KEY", "app-local-default"),  # Local Dify API key
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),  # Updated to use HTTP for local development
        "model": "gemini-1.5-pro",
    }
}

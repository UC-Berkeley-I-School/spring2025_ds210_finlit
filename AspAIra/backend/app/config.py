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
    "Baseline_gpt": {
        "api_key": "app-vYXuXAEZCGcjMq7hGc1uzaEh",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "gpt-4o",
        "required_inputs": {
            "number_of_kids": {"source": "profile1", "type": "string"},
            "bank_account": {"source": "profile2", "type": "string"},
            "debt_information": {"source": "profile2", "type": "string"},
            "remittance_information": {"source": "profile2", "type": "string"},
            "remittance_amount": {"source": "profile2", "type": "string"},
            "housing": {"source": "profile1", "type": "string"},
            "job_title": {"source": "profile1", "type": "string"},
            "education_level": {"source": "profile1", "type": "string"},
            "financial_dependents": {"source": "profile2", "type": "string"}
        }
    },
    "Baseline_claude": {
        "api_key": "app-5UVXvE1G6wiZBZ3v0MACCfbj",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "claude-3-5-sonnet-20241022",
        "required_inputs": {
            "number_of_kids": {"source": "profile1", "type": "string"},
            "bank_account": {"source": "profile2", "type": "string"},
            "debt_information": {"source": "profile2", "type": "string"},
            "remittance_information": {"source": "profile2", "type": "string"},
            "remittance_amount": {"source": "profile2", "type": "string"},
            "housing": {"source": "profile1", "type": "string"},
            "job_title": {"source": "profile1", "type": "string"},
            "education_level": {"source": "profile1", "type": "string"},
            "financial_dependents": {"source": "profile2", "type": "string"}
        }
    },
    "V2_claude": {
        "api_key": "app-N1mfbmN31JwFFOfEhOnvGjg3",  # Local Dify API key
        "base_url": "http://localhost",  # Updated to use HTTP for local development
        "model": "claude-3-5-sonnet-20241022",
        "required_inputs": {
            "number_of_kids": {"source": "profile1", "type": "string"},
            "bank_account": {"source": "profile2", "type": "string"},
            "debt_information": {"source": "profile2", "type": "string"},
            "remittance_information": {"source": "profile2", "type": "string"},
            "remittance_amount": {"source": "profile2", "type": "string"},
            "housing": {"source": "profile1", "type": "string"},
            "job_title": {"source": "profile1", "type": "string"},
            "education_level": {"source": "profile1", "type": "string"},
            "financial_dependents": {"source": "profile2", "type": "string"},
            "country_of_origin": {"source": "profile1", "type": "string"},
            "time_in_uae": {"source": "profile1", "type": "string"}
        }
    }
}

# Active agent version
ACTIVE_AGENT_VERSION = "V2_claude"

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
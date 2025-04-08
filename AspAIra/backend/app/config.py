"""
Configuration settings for the AspAIra application.

This module defines configurations for:
- Agent settings including API keys, base URLs, and required inputs.
- AWS DynamoDB and general AWS region settings.
- FastAPI application metadata.
- Default versions used across the application.
"""

import os
from typing import Dict

# ===================== Agent Configurations =====================
AGENT_CONFIGS: Dict[str, Dict] = {
    "Baseline_gpt": {
        "api_key": os.getenv("BASELINE_GPT_API_KEY", "app-local-default"),
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),
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
        "api_key": os.getenv("BASELINE_CLAUDE_API_KEY", "app-local-default"),
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),
        "model": "clause-3-5-sonnet-20241022",
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
        "api_key": os.getenv("V2_CLAUDE_API_KEY", "app-local-default"),
        "base_url": os.getenv("DIFY_API_URL", "http://localhost"),
        "model": "clause-3-5-sonnet-20241022",
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

# ===================== Active Agent Version =====================
# Specifies the currently active agent configuration.
ACTIVE_AGENT_VERSION = os.getenv("ACTIVE_AGENT_VERSION", "V2_claude")

# ===================== Database Configuration =====================
DATABASE_CONFIG = {
    "table_name": os.getenv("DYNAMODB_TABLE_NAME", "chat_interactions"),
    "region": os.getenv("AWS_REGION", "us-east-1")
}

# ===================== API Configuration =====================
API_CONFIG = {
    "title": "AspAIra API",
    "description": "API for AspAIra financial coaching application",
    "version": "1.0.0",
    "debug": os.getenv("DEBUG", "true").lower() == "true"
}

# ===================== Default Dify Version =====================
DEFAULT_DIFY_VERSION = os.getenv("DEFAULT_DIFY_VERSION", "v1")
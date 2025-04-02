from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from decimal import Decimal

# Profile field mappings
PROFILE1_FIELDS = {
    "country_of_origin": "country_of_origin",
    "time_in_uae": "time_in_uae",
    "job_title": "job_title",
    "housing": "housing",
    "education_level": "education_level",
    "number_of_kids": "number_of_kids"
}

PROFILE2_FIELDS = {
    "bank_account": "bank_account",
    "debt_information": "debt_information",
    "remittance_information": "remittance_information",
    "financial_dependents": "financial_dependents"
}

class UsageMetrics(BaseModel):
    """Model for conversation usage metrics"""
    num_turns: int
    avg_tokens_per_turn: Decimal
    avg_completion_tokens: Decimal
    avg_cost_per_turn: Decimal
    total_price: Decimal
    avg_latency: Decimal
    max_latency: Decimal
    currency: str = "USD"

class EvaluationMetrics(BaseModel):
    """Model for evaluation metrics"""
    Personalization: int = Field(ge=1, le=5)
    Language_Simplicity: int = Field(ge=1, le=5)
    Response_Length: int = Field(ge=1, le=5)
    Content_Relevance: int = Field(ge=1, le=5)
    Content_Difficulty: int = Field(ge=1, le=5)

class UserProfile(BaseModel):
    """Model for user profile data"""
    # Profile1 fields
    country_of_origin: Optional[str] = None
    time_in_uae: Optional[str] = None
    job_title: Optional[str] = None
    housing: Optional[str] = None
    education_level: Optional[str] = None
    number_of_kids: Optional[int] = None
    
    # Profile2 fields
    bank_account: Optional[bool] = None
    debt_information: Optional[Dict] = None
    remittance_information: Optional[Dict] = None
    financial_dependents: Optional[int] = None

class EvaluationInput(BaseModel):
    """Model for evaluation input data"""
    convo_id: str  # Changed from conv_id to convo_id
    username: str
    conversation_history: str  # Plain text conversation history
    country_of_origin: str
    time_in_uae: str
    job_title: str
    housing: str
    education_level: str
    number_of_kids: int
    bank_account: bool
    debt_information: Dict
    remittance_information: Dict
    financial_dependents: int

class DifyEvaluationOutput(BaseModel):
    """Model for Dify evaluation output"""
    conversation_id: str
    username: str
    agent_id: str
    evaluation_timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    Personalization: int = Field(ge=0, le=5)
    Language_Simplicity: int = Field(ge=0, le=5)
    Response_Length: int = Field(ge=0, le=5)
    Content_Relevance: int = Field(ge=0, le=5)
    Content_Difficulty: int = Field(ge=0, le=5)
    Notes: str
    usage_metrics: Optional[UsageMetrics] = None 
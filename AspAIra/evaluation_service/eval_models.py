from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Union
from datetime import datetime
from decimal import Decimal
from pydantic import validator

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

class QuizMetrics(BaseModel):
    """Model for quiz metrics"""
    quiz_taken: bool
    quiz_score: Decimal = Field(default=Decimal('0'))

class ScoreMetrics(BaseModel):
    """Model for evaluation scores"""
    Personalization: Decimal = Field(ge=0, le=5)
    Language_Simplicity: Decimal = Field(ge=0, le=5)
    Response_Length: Decimal = Field(ge=0, le=5)
    Content_Relevance: Decimal = Field(ge=0, le=5)
    Content_Difficulty: Decimal = Field(ge=0, le=5)

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
    convo_id: str  
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

class EvaluationNotes(BaseModel):
    """Model for evaluation notes and feedback"""
    summary: str
    key_insights: str
    areas_for_improvement: str
    recommendations: str

class JudgeMetrics(BaseModel):
    """Model for judge-specific metrics"""
    latency: Decimal
    eval_tokens: Decimal
    eval_cost: Decimal
    currency: str = "USD"

class JudgeEvaluation(BaseModel):
    """Model for individual judge's evaluation"""
    judge_id: str
    scores: ScoreMetrics
    evaluation_notes: EvaluationNotes
    judge_metrics: Optional[Dict[str, Decimal]] = None  # Only Decimal values for metrics
    process_status: str = Field(default="success", description="Status of evaluation processing: success, error, or partial")
    raw_response: Optional[str] = Field(default=None, description="Raw response from judge when processing fails")

    @classmethod
    def from_dict(cls, data: Dict) -> 'JudgeEvaluation':
        """Create a JudgeEvaluation from a dictionary"""
        return cls(
            judge_id=data['judge_id'],
            scores={k: Decimal(str(v)) for k, v in data['scores'].items()},
            evaluation_notes=data['evaluation_notes'],
            process_status=data['process_status'],
            raw_response=data.get('raw_response'),
            judge_metrics=data.get('judge_metrics')
        )

class DifyEvaluationOutput(BaseModel):
    """Model for complete evaluation output"""
    conversation_id: str
    username: str
    agent_id: str
    evaluation_timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    judge_evaluations: List[JudgeEvaluation]
    usage_metrics: Optional[UsageMetrics] = None
    quiz_metrics: Optional[QuizMetrics] = None 
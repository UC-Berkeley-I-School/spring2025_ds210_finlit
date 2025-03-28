from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    is_active: bool = True
    profile1: Optional[Dict] = None
    profile2: Optional[Dict] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class ProfilePart1(BaseModel):
    country_of_origin: Literal["Filipino", "Kenyan", "Sri Lankan"]
    time_in_uae: Literal["Less than a year", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
    job_title: Literal["Live In maid", "Live out maid", "Cook", "Nanny"]
    housing: Literal["Live In", "Live Out", "Temporary Housing"]
    education_level: Literal["None", "Primary school", "High school", "College"]
    number_of_dependents: Literal["None", "1", "2", "3", "More than 3"]

    class Config:
        populate_by_name = True

class ProfilePart2(BaseModel):
    bank_account: Literal["FAB", "Emirates NBD", "ADCB", "ADIB", "No Bank Account"]
    debt_information: Literal["Debt in Home Country", "Debt in UAE", "No Debt"]
    remittance_information: Literal["Send money with Bank Transfer", "Send money with Exchange House", 
                                  "Send money offline", "Don't Send any money"]
    remittance_amount: Literal["Less than 100 AED", "100-500 AED", "500-1000 AED", "1000-2000 AED", "More than 2000 AED"]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent_type: str = "dify"  # Default to dify for now
    agent_version: str = "v1"  # Default to v1 for now

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime
    interaction_type: Literal["opening", "content", "quiz", "feedback"]
    quiz: Optional[List[Dict]] = None

class ChatInteraction(BaseModel):
    username: str
    timestamp: datetime
    message: str
    response: str
    interaction_type: Literal["opening", "content", "quiz", "feedback"]
    metadata: Dict = Field(default_factory=dict)
    quiz_data: Optional[Dict] = None
    quiz_answers: Optional[List[str]] = None
    quiz_feedback: Optional[str] = None

class UserEngagement(BaseModel):
    user_id: str
    session_duration: float
    messages_sent: int
    timestamp: datetime

class UserLogin(BaseModel):
    username: str
    password: str

# New conversation models
class ConversationMetadata(BaseModel):
    total_messages: int = 0
    total_duration: int = 0
    topics_covered: List[str] = []

class Conversation(BaseModel):
    conversation_id: str
    username: str
    agent_id: str
    created_at: datetime
    last_activity: datetime
    status: str
    metadata: ConversationMetadata

class RetrieverResource(BaseModel):
    position: int
    content: str
    metadata: Dict = Field(default_factory=dict)

class TokenUsage(BaseModel):
    prompt_tokens: int
    prompt_unit_price: str
    prompt_price_unit: str
    prompt_price: str
    completion_tokens: int
    completion_unit_price: str
    completion_price_unit: str
    completion_price: str
    total_tokens: int
    total_price: str
    currency: str
    latency: float

class ChatMetadata(BaseModel):
    message_length: int
    request_timestamp: str
    response_timestamp: str
    latency_ms: float
    usage: TokenUsage
    retriever_resources: Optional[List[RetrieverResource]] = None

class QuizData(BaseModel):
    questions: List[str]
    answers: List[str]
    score: float
    feedback: str

class ChatMessage(BaseModel):
    """Model for chat messages stored in the database"""
    message_id: str
    conversation_id: str
    username: str
    agent_id: str
    timestamp: datetime
    message: str
    response: str
    interaction_type: str
    dify_metadata: Optional[dict] = None
    quiz_data: Optional[dict] = None
    usage_metrics: Optional[dict] = None

class ChatHistory(BaseModel):
    """Model for chat history response"""
    messages: List[ChatMessage] 
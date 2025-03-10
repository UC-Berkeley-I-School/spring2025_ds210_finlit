from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool = True

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

class UserProfile(BaseModel):
    username: str
    dependents_count: Optional[str] = None
    bank_account: Optional[str] = None
    debt_status: Optional[str] = None
    remittance_status: Optional[str] = None
    remittance_amount: Optional[str] = None 
from pydantic import BaseModel
from typing import Optional, Literal

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    is_active: bool = True

class ProfilePart1(BaseModel):
    country_of_origin: Literal['Philippines', 'Kenya', 'Ethiopia', 'India', 'Sri Lanka']
    time_in_uae: Literal['Less than a year', '1-3 Years', '3-5 Years', '5-10 Years', '10+ Years']
    job_title: Literal['Live-In Maid', 'Live-Out Maid', 'Cook', 'Nanny', 'Seeking Employment']
    housing: Literal['Live-In', 'Live-Out', 'Temporary Housing']
    education_level: Literal['None', 'Primary School', 'High School', 'College']
    number_of_dependents: Literal['None', '1', '2', '3', 'More than 3']

class ProfilePart2(BaseModel):
    bank_account: Literal['FAB', 'Emirates NBD', 'ADCB', 'ADIB', 'No Bank Account']
    debt_information: Literal['Debt in Home Country', 'Debt in UAE', 'No Debt']
    remittance_information: Literal['Send Money through Bank', 'Send Money through Exchange House', 'Send Money through Informal Network', "Don't know how to Send Money"]

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 
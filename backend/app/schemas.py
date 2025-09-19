from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class LeadCreate(BaseModel):
    company: str
    contact_name: str
    email: EmailStr
    title: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = ""

class LeadUpdate(BaseModel):
    company: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    stage: Optional[str] = None
    score: Optional[float] = None

class LeadOut(BaseModel):
    id: int
    company: str
    contact_name: str
    email: EmailStr
    title: Optional[str]
    website: Optional[str]
    notes: str
    score: float
    stage: str
    class Config: from_attributes = True

class ScoreWeights(BaseModel):
    industry_fit: float = 0.4
    size_fit: float = 0.2
    intent_signals: float = 0.3
    data_quality: float = 0.1

class MessageRequest(BaseModel):
    lead_id: int
    tone: str = Field(default="concise, helpful, human")
    call_to_action: str = Field(default="Would you be open to a 20-minute intro call this week?")
    extra_context: Optional[str] = None

class EvalScenario(BaseModel):
    name: str
    prompt: str
    must_include: Optional[str] = None
    must_not_include: Optional[str] = None

class EvalRunResult(BaseModel):
    scenario: str
    ok: bool
    notes: str

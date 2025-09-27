from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    goddess: Optional[str] = "athena"

class Citation(BaseModel):
    title: str
    url: str
    source: str
    date: Optional[str] = None
    description: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    goddess: str
    citations: List[Citation] = []
    timestamp: datetime = datetime.now()

class UserProfile(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    preferred_goddess: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class ChatMessage(BaseModel):
    message_id: str
    user_id: str
    message: str
    response: str
    goddess: str
    citations: List[Citation] = []
    timestamp: datetime = datetime.now()

class GoddessConfig(BaseModel):
    id: str
    name: str
    domain: str
    description: str
    keywords: List[str]
    personality_traits: List[str]
    response_style: str

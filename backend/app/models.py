from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Reference to an indexed NJIT resource used to ground a response."""

    id: str
    title: str
    url: str
    source: str
    snippet: str = Field(default="")
    published: Optional[str] = None


class ChatMessage(BaseModel):
    """Single message in a conversation log."""

    role: str  # "user" | "assistant"
    content: str
    goddess: Optional[str] = None
    intent: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatHistory(BaseModel):
    user_id: str = Field(..., alias="_id")
    messages: List[ChatMessage] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class ChatRequest(BaseModel):
    message: str


class IntentPrediction(BaseModel):
    intent: str
    confidence: float
    rationale: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    goddess: str
    confidence: float
    rationale: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    goddess: str
    intent: str
    citations: List[Citation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace: Dict[str, Any] = Field(default_factory=dict)


class QuizAnswers(BaseModel):
    answers: List[int]


class User(BaseModel):
    user_id: str = Field(..., alias="_id")
    email: str
    name: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    selected_goddess: Optional[str] = None
    quiz_results: Optional[Dict[str, Any]] = None
    intents_seen: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "auth0|123456789",
                "email": "user@example.com",
                "selected_goddess": "Athena",
                "profile": {"major": "Computer Science"},
            }
        }

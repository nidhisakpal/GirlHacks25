from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: str
    title: str
    url: str
    source: str
    snippet: str = ""
    retrieved: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    goddess: str
    intent: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IntentPrediction(BaseModel):
    intent: str
    confidence: float
    rationale: List[str] = Field(default_factory=list)
    suggested_goddess: Optional[str] = None


class ChatHistory(BaseModel):
    user_id: str = Field(..., alias="_id")
    messages: Dict[str, List[ChatMessage]] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class ChatRequest(BaseModel):
    message: str
    goddess: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    goddess: str
    intent: str
    citations: List[Citation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace: Dict[str, Any] = Field(default_factory=dict)

class MatchResult(BaseModel):
    goddess: str
    confidence: float
    rationale: List[str] = Field(default_factory=list)


class User(BaseModel):
    user_id: str = Field(..., alias="_id")
    email: str
    name: Optional[str] = None
    profile: Dict[str, Any] = Field(default_factory=dict)
    selected_goddess: Optional[str] = None
    suggested_goddess: Optional[str] = None
    handoff_stage: Optional[str] = None       # e.g. "awaiting_choice", "awaiting_confirmation"
    quiz_results: Optional[Dict[str, Any]] = None
    intents_seen: List[str] = Field(default_factory=list)
    # NEW: preserve backend-written handoff context for confirm flow
    routing_state: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class QuizAnswers(BaseModel):
    answers: List[int]

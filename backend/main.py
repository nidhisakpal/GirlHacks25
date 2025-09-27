import os
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase

from dotenv import load_dotenv

load_dotenv()  # reads .env in the working directory

from app.auth import verify_token
from app.chat import ChatService
from app.database import (
    append_intents,
    close_mongo_connection,
    connect_to_mongo,
    create_or_update_user,
    get_chat_history,
    get_database,
    update_user_goddess,
)
from app.goddess_matcher import GoddessMatcher
from app.models import ChatRequest, ChatResponse, MatchResult, QuizAnswers, User



app = FastAPI(title="Gaia Mentorship API", version="0.1.0")

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_service = ChatService()
goddess_matcher = GoddessMatcher()


@app.on_event("startup")
async def startup_event() -> None:
    connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    close_mongo_connection()


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config/personas")
async def list_personas() -> Dict[str, Dict[str, str]]:
    return goddess_matcher.personas()


@app.get("/api/user", response_model=User)
async def get_user_profile(
    db: AsyncIOMotorDatabase = Depends(get_database),
    token: Dict = Depends(verify_token),
):
    user_id = str(token.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user ID")

    profile = await create_or_update_user(
        db,
        user_id,
        email=token.get("email", "unknown@njit.edu"),
        profile={
            "name": token.get("name"),
            "picture": token.get("picture"),
        },
    )
    return profile


@app.post("/api/match", response_model=MatchResult)
async def match_goddess_endpoint(
    quiz_answers: QuizAnswers,
    db: AsyncIOMotorDatabase = Depends(get_database),
    token: Dict = Depends(verify_token),
):
    user_id = str(token.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user ID")

    match_result = goddess_matcher.match_for_quiz(quiz_answers.answers)
    await update_user_goddess(db, user_id, match_result.goddess, quiz_answers.model_dump())
    await append_intents(db, user_id, ["quiz"])
    return match_result


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    token: Dict = Depends(verify_token),
):
    user_id = str(token.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user ID")

    response = await chat_service.get_response(user_id, request.message, db)
    return response


@app.get("/api/chat/history")
async def get_history_endpoint(
    db: AsyncIOMotorDatabase = Depends(get_database),
    token: Dict = Depends(verify_token),
):
    user_id = str(token.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no user ID")

    history = await get_chat_history(db, user_id)
    return [message.model_dump() for message in history.messages]


@app.get("/api/public")
def public_endpoint() -> Dict[str, str]:
    return {"message": "This is a public endpoint"}


@app.get("/api/private")
def private_endpoint(token: Dict = Depends(verify_token)) -> Dict[str, Dict]:
    return {"message": "This is a private endpoint", "user": token}


import os
from datetime import datetime
from typing import Iterable, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models import ChatHistory, ChatMessage, Citation, User

# Mongo connection handles
_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def connect_to_mongo() -> None:
    """Initialise the global Mongo client lazily on startup."""

    global _client, _database
    if _client:
        return

    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise ValueError("MONGODB_URL not set")

    _client = AsyncIOMotorClient(mongodb_url)
    db_name = os.getenv("MONGODB_DB", "gaia_mentorship")
    _database = _client.get_database(db_name)


def close_mongo_connection() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


async def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        connect_to_mongo()
    assert _database is not None  # for type checkers
    return _database


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def get_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[User]:
    document = await db.users.find_one({"_id": user_id})
    if not document:
        return None
    return User.model_validate(document)


async def create_or_update_user(
    db: AsyncIOMotorDatabase,
    user_id: str,
    email: str,
    profile: Optional[dict] = None,
) -> User:
    now = datetime.utcnow()
    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "email": email,
                "profile": profile or {},
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )
    document = await db.users.find_one({"_id": user_id})
    assert document is not None
    return User.model_validate(document)


async def update_user_goddess(
    db: AsyncIOMotorDatabase,
    user_id: str,
    goddess: str,
    quiz_results: Optional[dict] = None,
) -> None:
    await db.users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "selected_goddess": goddess,
                "quiz_results": quiz_results or {},
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


async def append_intents(db: AsyncIOMotorDatabase, user_id: str, intents: Iterable[str]) -> None:
    """Record seen intents to help with analytics and matching."""

    await db.users.update_one(
        {"_id": user_id},
        {
            "$addToSet": {"intents_seen": {"$each": list(intents)}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

async def get_chat_history(db: AsyncIOMotorDatabase, user_id: str) -> ChatHistory:
    document = await db.chat_histories.find_one({"_id": user_id})
    if not document:
        return ChatHistory(user_id=user_id, messages=[])
    return ChatHistory.model_validate(document)


def _serialise_message(message: ChatMessage) -> dict:
    payload = message.model_dump(mode="python")
    payload["timestamp"] = message.timestamp
    if message.citations:
        payload["citations"] = [citation.model_dump(mode="python") for citation in message.citations]
    return payload


async def add_chat_message(
    db: AsyncIOMotorDatabase,
    user_id: str,
    *,
    role: str,
    content: str,
    goddess: Optional[str] = None,
    intent: Optional[str] = None,
    citations: Optional[list[Citation]] = None,
) -> ChatMessage:
    message = ChatMessage(
        role=role,
        content=content,
        goddess=goddess,
        intent=intent,
        citations=citations or [],
    )
    await db.chat_histories.update_one(
        {"_id": user_id},
        {
            "$push": {"messages": _serialise_message(message)},
            "$setOnInsert": {"_id": user_id},
        },
        upsert=True,
    )
    return message


async def replace_chat_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    messages: list[ChatMessage],
) -> None:
    await db.chat_histories.update_one(
        {"_id": user_id},
        {
            "$set": {
                "messages": [_serialise_message(message) for message in messages]
            },
        },
        upsert=True,
    )


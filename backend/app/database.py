import os
from datetime import datetime
from typing import Any, Dict, Iterable, Optional


from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models import ChatHistory, ChatMessage, Citation, User

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def connect_to_mongo() -> None:
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
    assert _database is not None
    return _database

# ---------------------------------------------------------------------------

async def get_user(db: AsyncIOMotorDatabase, user_id: str) -> Optional[User]:
    document = await db.users.find_one({"_id": user_id})
    return User.model_validate(document) if document else None


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
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    document = await db.users.find_one({"_id": user_id})
    assert document
    return User.model_validate(document)


async def update_user_goddess(
    db,
    user_id: str,
    goddess: Optional[str] = None,
    quiz_results: Optional[dict] = None,
    suggested: Optional[str] = None,
    handoff_stage: Optional[str] = None,
    *,
    routing_state: Optional[dict] = None,
    handoff_declined: Optional[dict] = None,
    extra: Optional[Dict[str, Any]] = None,  # future-proof
):
    """
    Upserts a user doc and updates selective fields.
    Pass None to leave a field unchanged.
    """
    update: Dict[str, Any] = {}
    if goddess is not None:
        update["selected_goddess"] = goddess
    if quiz_results is not None:
        update["quiz_results"] = quiz_results
    if suggested is not None:
        update["suggested_goddess"] = suggested
    if handoff_stage is not None:
        update["handoff_stage"] = handoff_stage
    if routing_state is not None:
        update["routing_state"] = routing_state
    if handoff_declined is not None:
        update["handoff_declined"] = handoff_declined
    if extra:
        update.update(extra)

    # Assuming users collection; adjust if your name differs
    await db.users.update_one(
        {"_id": user_id},
        {"$set": update},
        upsert=True,
    )



async def append_intents(db: AsyncIOMotorDatabase, user_id: str, intents: Iterable[str]) -> None:
    await db.users.update_one(
        {"_id": user_id},
        {
            "$addToSet": {"intents_seen": {"$each": list(intents)}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )

# ---------------------------------------------------------------------------

async def get_chat_history(db: AsyncIOMotorDatabase, user_id: str) -> ChatHistory:
    document = await db.chat_histories.find_one({"_id": user_id}) or {"_id": user_id, "messages": {}}
    # Ensure every goddess key exists
    for key in ["gaia", "athena", "aphrodite", "artemis", "tyche"]:
        document.setdefault("messages", {}).setdefault(key, [])
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
    goddess: str,
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
            "$setOnInsert": {"_id": user_id},
            "$push": {f"messages.{goddess}": _serialise_message(message)},
        },
        upsert=True,
    )
    return message


async def replace_chat_history(
    db: AsyncIOMotorDatabase,
    user_id: str,
    messages: dict[str, list[ChatMessage]],
) -> None:
    await db.chat_histories.update_one(
        {"_id": user_id},
        {
            "$set": {
                "messages": {
                    key: [_serialise_message(msg) for msg in thread]
                    for key, thread in messages.items()
                }
            },
        },
        upsert=True,
    )

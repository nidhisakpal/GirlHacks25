import os
import motor.motor_asyncio
from typing import Optional
from pymongo import MongoClient

class Database:
    client: Optional[MongoClient] = None
    database = None

db = Database()

async def get_database():
    """Get database connection"""
    if db.database is None:
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise Exception("MONGODB_URL environment variable not set")
        
        db.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        db.database = db.client.gaia_mentorship
        
        # Create indexes
        await create_indexes()
    
    return db.database

async def create_indexes():
    """Create database indexes for better performance"""
    if db.database:
        # User profiles index
        await db.database.user_profiles.create_index("user_id", unique=True)
        await db.database.user_profiles.create_index("email", unique=True)
        
        # Chat messages index
        await db.database.chat_messages.create_index("user_id")
        await db.database.chat_messages.create_index("timestamp")
        
        # Resources index
        await db.database.resources.create_index("source")
        await db.database.resources.create_index("last_updated")

async def close_database():
    """Close database connection"""
    if db.client:
        db.client.close()

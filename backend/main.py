from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from app.auth import verify_token
from app.chat import ChatService
from app.models import ChatRequest, ChatResponse, Citation
from app.database import get_database

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Gaia Mentorship API",
    description="Backend API for the Gaia Goddess-Guided Mentorship platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
chat_service = ChatService()

@app.get("/")
async def root():
    return {"message": "Gaia Mentorship API", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Main chat endpoint for goddess-guided conversations"""
    try:
        # Verify Auth0 token
        user_info = await verify_token(credentials.credentials)
        
        # Process chat request
        response = await chat_service.process_message(
            message=request.message,
            goddess=request.goddess,
            user_id=user_info.get("sub"),
            user_email=user_info.get("email")
        )
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

@app.get("/api/goddesses")
async def get_goddesses():
    """Get available goddess personas"""
    return {
        "goddesses": [
            {
                "id": "athena",
                "name": "Athena",
                "domain": "Academics & Wisdom",
                "description": "Goddess of wisdom, strategy, and academic excellence"
            },
            {
                "id": "aphrodite", 
                "name": "Aphrodite",
                "domain": "Well-being & Self-care",
                "description": "Goddess of love, beauty, and emotional wellness"
            },
            {
                "id": "hera",
                "name": "Hera", 
                "domain": "Career & Leadership",
                "description": "Goddess of marriage, family, and power"
            }
        ]
    }

@app.get("/api/user/profile")
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user profile information"""
    try:
        user_info = await verify_token(credentials.credentials)
        return {"user": user_info}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

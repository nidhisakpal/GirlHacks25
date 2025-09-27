import os
import google.generativeai as genai
from typing import List, Dict, Any
from app.models import ChatResponse, Citation
from app.goddess_matcher import GoddessMatcher
from app.search_service import SearchService
from app.database import get_database

class ChatService:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize services
        self.goddess_matcher = GoddessMatcher()
        self.search_service = SearchService()
    
    async def process_message(
        self, 
        message: str, 
        goddess: str, 
        user_id: str, 
        user_email: str
    ) -> ChatResponse:
        """Process a chat message and return goddess response"""
        
        # Get or create user profile
        db = await get_database()
        user_profile = await self._get_or_create_user_profile(db, user_id, user_email)
        
        # Determine best goddess if not specified
        if not goddess or goddess == "auto":
            goddess = await self.goddess_matcher.match_goddess(message, user_profile)
        
        # Classify intent
        intent = await self._classify_intent(message)
        
        # Search for relevant resources if needed
        citations = []
        if intent in ["events", "academics", "career", "resources"]:
            citations = await self.search_service.search_resources(message, intent)
        
        # Generate goddess response
        response_text = await self._generate_response(
            message, goddess, intent, citations, user_profile
        )
        
        # Save chat message
        await self._save_chat_message(db, user_id, message, response_text, goddess, citations)
        
        return ChatResponse(
            response=response_text,
            goddess=goddess,
            citations=citations
        )
    
    async def _get_or_create_user_profile(self, db, user_id: str, user_email: str):
        """Get or create user profile"""
        profile = await db.user_profiles.find_one({"user_id": user_id})
        
        if not profile:
            profile = {
                "user_id": user_id,
                "email": user_email,
                "preferred_goddess": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
            await db.user_profiles.insert_one(profile)
        
        return profile
    
    async def _classify_intent(self, message: str) -> str:
        """Classify user intent using Gemini"""
        prompt = f"""
        Classify the following user message into one of these categories:
        - events: Questions about campus events, activities, clubs
        - academics: Questions about courses, study help, tutoring
        - career: Questions about jobs, internships, career advice
        - wellness: Questions about mental health, stress, self-care
        - general: General questions or conversation
        
        Message: "{message}"
        
        Respond with only the category name.
        """
        
        try:
            response = self.model.generate_content(prompt)
            intent = response.text.strip().lower()
            
            # Fallback to keyword matching
            if intent not in ["events", "academics", "career", "wellness", "general"]:
                intent = self._keyword_classify_intent(message)
            
            return intent
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return self._keyword_classify_intent(message)
    
    def _keyword_classify_intent(self, message: str) -> str:
        """Fallback keyword-based intent classification"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["event", "club", "activity", "meeting"]):
            return "events"
        elif any(word in message_lower for word in ["study", "course", "class", "homework", "exam", "tutor"]):
            return "academics"
        elif any(word in message_lower for word in ["job", "career", "internship", "resume", "interview"]):
            return "career"
        elif any(word in message_lower for word in ["stress", "anxiety", "mental health", "wellness", "self-care"]):
            return "wellness"
        else:
            return "general"
    
    async def _generate_response(
        self, 
        message: str, 
        goddess: str, 
        intent: str, 
        citations: List[Citation],
        user_profile: Dict[str, Any]
    ) -> str:
        """Generate goddess-voiced response using Gemini"""
        
        goddess_prompts = {
            "athena": "You are Athena, goddess of wisdom and strategy. Respond with scholarly wisdom, practical academic advice, and strategic thinking. Be encouraging but direct.",
            "aphrodite": "You are Aphrodite, goddess of love and beauty. Respond with warmth, empathy, and focus on emotional wellness and self-care. Be nurturing and supportive.",
            "hera": "You are Hera, goddess of marriage and power. Respond with authority, leadership advice, and career guidance. Be confident and empowering."
        }
        
        goddess_prompt = goddess_prompts.get(goddess, goddess_prompts["athena"])
        
        # Build context with citations
        context = ""
        if citations:
            context = "\n\nRelevant NJIT Resources:\n"
            for citation in citations:
                context += f"- {citation.title}: {citation.url}\n"
        
        prompt = f"""
        {goddess_prompt}
        
        User message: "{message}"
        Intent: {intent}
        
        {context}
        
        Respond as the goddess would, providing helpful, grounded advice. If you reference resources, mention them naturally in your response. Keep responses concise but meaningful (2-3 sentences). Never fabricate events or information not provided in the context.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble responding right now. Please try again."
    
    async def _save_chat_message(
        self, 
        db, 
        user_id: str, 
        message: str, 
        response: str, 
        goddess: str, 
        citations: List[Citation]
    ):
        """Save chat message to database"""
        chat_message = {
            "message_id": f"{user_id}_{int(time.time())}",
            "user_id": user_id,
            "message": message,
            "response": response,
            "goddess": goddess,
            "citations": [citation.dict() for citation in citations],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        await db.chat_messages.insert_one(chat_message)

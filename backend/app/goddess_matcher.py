import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Any

class GoddessMatcher:
    def __init__(self):
        # Load sentence transformer for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Goddess configurations
        self.goddesses = {
            "athena": {
                "keywords": [
                    "study", "academic", "course", "homework", "exam", "research", 
                    "learning", "education", "knowledge", "wisdom", "strategy",
                    "tutoring", "library", "scholarship", "grade", "assignment"
                ],
                "personality_traits": [
                    "wise", "strategic", "scholarly", "analytical", "methodical",
                    "intellectual", "thoughtful", "precise", "logical"
                ]
            },
            "aphrodite": {
                "keywords": [
                    "wellness", "mental health", "stress", "anxiety", "self-care",
                    "relationships", "friendship", "love", "beauty", "confidence",
                    "emotional", "therapy", "counseling", "balance", "happiness"
                ],
                "personality_traits": [
                    "nurturing", "empathetic", "warm", "caring", "supportive",
                    "compassionate", "gentle", "understanding", "healing"
                ]
            },
            "hera": {
                "keywords": [
                    "career", "job", "internship", "leadership", "professional",
                    "resume", "interview", "networking", "business", "management",
                    "work", "employment", "skills", "development", "success"
                ],
                "personality_traits": [
                    "authoritative", "confident", "powerful", "ambitious", "strong",
                    "determined", "focused", "professional", "commanding"
                ]
            }
        }
        
        # Pre-compute goddess embeddings
        self.goddess_embeddings = self._compute_goddess_embeddings()
    
    def _compute_goddess_embeddings(self) -> Dict[str, np.ndarray]:
        """Pre-compute embeddings for each goddess"""
        embeddings = {}
        
        for goddess_id, config in self.goddesses.items():
            # Combine keywords and personality traits
            text = " ".join(config["keywords"] + config["personality_traits"])
            embedding = self.model.encode(text)
            embeddings[goddess_id] = embedding
        
        return embeddings
    
    async def match_goddess(self, message: str, user_profile: Dict[str, Any]) -> str:
        """Match user message to appropriate goddess using rules + embeddings"""
        
        # Check user preference first
        if user_profile.get("preferred_goddess"):
            return user_profile["preferred_goddess"]
        
        # Rule-based matching (primary)
        rule_match = self._rule_based_match(message)
        if rule_match:
            return rule_match
        
        # Embedding-based matching (tie-breaker)
        embedding_match = self._embedding_based_match(message)
        return embedding_match
    
    def _rule_based_match(self, message: str) -> str:
        """Rule-based goddess matching using keyword scoring"""
        message_lower = message.lower()
        scores = {}
        
        for goddess_id, config in self.goddesses.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    score += 1
            
            # Weight by keyword importance
            if score > 0:
                scores[goddess_id] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def _embedding_based_match(self, message: str) -> str:
        """Embedding-based goddess matching using cosine similarity"""
        message_embedding = self.model.encode(message)
        
        similarities = {}
        for goddess_id, goddess_embedding in self.goddess_embeddings.items():
            similarity = cosine_similarity(
                message_embedding.reshape(1, -1),
                goddess_embedding.reshape(1, -1)
            )[0][0]
            similarities[goddess_id] = similarity
        
        return max(similarities, key=similarities.get)
    
    def get_goddess_info(self, goddess_id: str) -> Dict[str, Any]:
        """Get goddess configuration information"""
        return self.goddesses.get(goddess_id, {})
    
    def add_goddess(self, goddess_id: str, config: Dict[str, Any]):
        """Add a new goddess configuration (for extensibility)"""
        self.goddesses[goddess_id] = config
        # Recompute embeddings
        self.goddess_embeddings = self._compute_goddess_embeddings()

import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any
from app.models import Citation

class SearchService:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        if not all([self.endpoint, self.key, self.index_name]):
            raise ValueError("Azure Search configuration missing")
        
        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )
    
    async def search_resources(self, query: str, intent: str) -> List[Citation]:
        """Search for relevant NJIT resources"""
        try:
            # Build search query with filters
            search_filter = self._build_filter(intent)
            
            results = self.client.search(
                search_text=query,
                filter=search_filter,
                top=3,
                include_total_count=True
            )
            
            citations = []
            for result in results:
                citation = Citation(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    source=result.get("source", "Unknown"),
                    date=result.get("date"),
                    description=result.get("description", "")
                )
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            print(f"Error searching resources: {e}")
            return []
    
    def _build_filter(self, intent: str) -> str:
        """Build Azure Search filter based on intent"""
        intent_filters = {
            "events": "source eq 'highlander_hub' or source eq 'events'",
            "academics": "source eq 'tutoring' or source eq 'academic_support' or source eq 'courses'",
            "career": "source eq 'handshake' or source eq 'career_services'",
            "wellness": "source eq 'wellness' or source eq 'mental_health' or source eq 'counseling'",
            "general": None
        }
        
        return intent_filters.get(intent)
    
    async def search_all(self, query: str, top: int = 10) -> List[Citation]:
        """Search all resources without filters"""
        try:
            results = self.client.search(
                search_text=query,
                top=top,
                include_total_count=True
            )
            
            citations = []
            for result in results:
                citation = Citation(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    source=result.get("source", "Unknown"),
                    date=result.get("date"),
                    description=result.get("description", "")
                )
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            print(f"Error searching all resources: {e}")
            return []

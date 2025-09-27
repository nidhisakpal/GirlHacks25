import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import time # Import the time module
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch,
    HnswParameters
)

# Load environment variables from the backend .env file
load_dotenv(dotenv_path='../backend/.env')

def format_date(date_str: Optional[str]) -> Optional[str]:
    """Parse a date string and return it in ISO 8601 UTC format with millisecond precision."""
    if not date_str:
        return None
    try:
        # Handle both 'Z' and '+00:00' for UTC timezone info
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # If the datetime object is naive (no timezone), assume it's UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        # Format to ISO 8601 UTC ('Z') format with millisecond precision
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    except (ValueError, TypeError):
        # Return None if the date string is invalid
        return None

class AzureSearchIndexer:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_API_KEY") # Use AZURE_SEARCH_API_KEY
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "gaia-resources")
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Azure Search configuration missing. Ensure AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY are set.")
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )
    
    def create_index(self):
        """Create the Azure AI Search index"""
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=1536, vector_search_profile_name="vector-profile"),
            SimpleField(name="url", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="scraped_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SearchField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), 
                        searchable=True, filterable=True, facetable=True),
        ]
        
        # Vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine"
                    )
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ]
        )
        
        # Semantic search configuration
        semantic_config = SemanticConfiguration(
            name="semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[
                    SemanticField(field_name="description"),
                    SemanticField(field_name="content")
                ]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )
        
        try:
            print(f"Creating or updating index '{self.index_name}'...")
            result = self.index_client.create_or_update_index(index)
            print(f"Index '{self.index_name}' created successfully")
            return result
        except Exception as e:
            print(f"Error creating index: {e}")
            raise
    
    def upload_documents(self, documents: List[Dict[str, Any]]):
        """Upload documents to the search index"""
        try:
            # Prepare documents for upload
            search_docs = []
            for i, doc in enumerate(documents):
                search_doc = {
                    "id": doc.get("id", str(i)),
                    "title": doc.get("title", ""),
                    "description": doc.get("description", ""),
                    "content": doc.get("content", doc.get("description", "")),
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                    "category": doc.get("category", ""),
                    "date": format_date(doc.get("date")),
                    "scraped_at": format_date(doc.get("scraped_at")),
                    "tags": doc.get("tags", [])
                    # content_vector is omitted as we don't have embeddings yet
                }
                search_docs.append(search_doc)
            
            # Upload in batches
            batch_size = 1000
            for i in range(0, len(search_docs), batch_size):
                batch = search_docs[i:i + batch_size]
                result = self.search_client.upload_documents(documents=batch)
                
                # Check for errors
                if not all([r.succeeded for r in result]):
                    print(f"Failed to upload some documents in batch {i//batch_size + 1}")
                    for res in result:
                        if not res.succeeded:
                            print(f"  Error for key {res.key}: {res.error_message}")
                else:
                    print(f"Successfully uploaded batch {i//batch_size + 1} ({len(batch)} documents)")
            
            print(f"Upload completed. Total documents processed: {len(search_docs)}")
            
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise
    
    def delete_index(self):
        """Delete the search index"""
        try:
            self.index_client.delete_index(self.index_name)
            print(f"Index '{self.index_name}' deleted successfully")
        except Exception as e:
            print(f"Error deleting index: {e}")
    
    def get_index_stats(self):
        """Get index statistics"""
        try:
            stats = self.search_client.get_document_count()
            print(f"Index '{self.index_name}' contains {stats} documents")
            return stats
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return 0

def main():
    """Main function to set up Azure AI Search index"""
    indexer = AzureSearchIndexer()
    
    print("Setting up Azure AI Search index...")
    
    # Create index
    indexer.create_index()
    
    # Load sample data
    try:
        with open("njit_resources.json", "r") as f:
            resources = json.load(f)
        
        print(f"Loaded {len(resources)} resources from JSON file")
        
        # Upload documents
        indexer.upload_documents(resources)
        
        # Wait a couple of seconds for indexing to catch up
        print("Waiting for indexing to complete...")
        time.sleep(2)
        
        # Get stats
        indexer.get_index_stats()
        
    except FileNotFoundError:
        print("No resources file found (njit_resources.json). Run scrape_njit_resources.py first.")
    except Exception as e:
        print(f"Error during indexing: {e}")

if __name__ == "__main__":
    main()

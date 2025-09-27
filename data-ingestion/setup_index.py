import os
import json
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
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
    SemanticSearch
)
from typing import List, Dict, Any

class AzureSearchIndexer:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "gaia-resources")
        
        if not all([self.endpoint, self.key]):
            raise ValueError("Azure Search configuration missing")
        
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
            SimpleField(name="url", type=SearchFieldDataType.String),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="date", type=SearchFieldDataType.String),
            SimpleField(name="scraped_at", type=SearchFieldDataType.String),
            SearchableField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
        ]
        
        # Vector search configuration (for future embeddings)
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-config",
                    kind="hnsw",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm="hnsw-config"
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
            for doc in documents:
                search_doc = {
                    "id": doc.get("id", f"doc_{hash(doc.get('url', ''))}"),
                    "title": doc.get("title", ""),
                    "description": doc.get("description", ""),
                    "content": doc.get("content", doc.get("description", "")),
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                    "category": doc.get("category", ""),
                    "date": doc.get("date", ""),
                    "scraped_at": doc.get("scraped_at", ""),
                    "tags": doc.get("tags", [])
                }
                search_docs.append(search_doc)
            
            # Upload in batches
            batch_size = 100
            for i in range(0, len(search_docs), batch_size):
                batch = search_docs[i:i + batch_size]
                result = self.search_client.upload_documents(batch)
                
                # Check for errors
                failed_docs = [doc for doc in result if not doc.succeeded]
                if failed_docs:
                    print(f"Failed to upload {len(failed_docs)} documents in batch {i//batch_size + 1}")
                    for doc in failed_docs:
                        print(f"Error: {doc.error_message}")
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
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize indexer
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
        
        # Get stats
        indexer.get_index_stats()
        
    except FileNotFoundError:
        print("No resources file found. Run scrape_njit_resources.py first.")
    except Exception as e:
        print(f"Error during indexing: {e}")

if __name__ == "__main__":
    main()

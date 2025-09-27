# Azure AI Search Configuration

# Search Service Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=gaia-resources

# Index Configuration
INDEX_FIELDS:
  - id (key)
  - title (searchable)
  - description (searchable)
  - content (searchable)
  - url (simple)
  - source (filterable, facetable)
  - category (filterable, facetable)
  - date (simple)
  - scraped_at (simple)
  - tags (searchable collection)

# Search Configuration
SEARCH_MODE: hybrid (keyword + vector)
SEMANTIC_SEARCH: enabled
VECTOR_SEARCH: enabled (for future embeddings)

# Performance Settings
BATCH_SIZE: 100
MAX_RESULTS: 50
DEFAULT_TOP: 3

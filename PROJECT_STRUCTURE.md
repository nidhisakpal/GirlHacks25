# Gaia Mentorship - Project Structure

```
gaia-mentorship/
├── README.md                           # Main project documentation
├── LICENSE                             # MIT License
├── 
├── frontend/                           # React + Vite + Tailwind frontend
│   ├── package.json                    # Node.js dependencies
│   ├── vite.config.ts                  # Vite configuration
│   ├── tailwind.config.js              # Tailwind CSS configuration
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── tsconfig.node.json              # Node TypeScript configuration
│   ├── index.html                      # HTML entry point
│   ├── env.example                     # Environment variables template
│   └── src/
│       ├── main.tsx                    # React app entry point
│       ├── App.tsx                     # Main app component
│       ├── index.css                   # Global styles with Tailwind
│       └── components/
│           ├── Header.tsx              # App header with Auth0 login
│           ├── Footer.tsx              # App footer with last indexed info
│           ├── LoadingSpinner.tsx     # Loading component
│           ├── GoddessSelection.tsx   # Goddess selection interface
│           └── ChatInterface.tsx       # Main chat interface
│
├── backend/                            # FastAPI backend
│   ├── requirements.txt                # Python dependencies
│   ├── env.example                     # Environment variables template
│   ├── main.py                         # FastAPI app entry point
│   └── app/
│       ├── models.py                   # Pydantic data models
│       ├── database.py                 # MongoDB connection and setup
│       ├── auth.py                     # Auth0 JWT verification
│       ├── chat.py                     # Main chat service logic
│       ├── search_service.py          # Azure AI Search integration
│       └── goddess_matcher.py          # Goddess matching algorithm
│
├── data-ingestion/                     # Web scraping and indexing
│   ├── requirements.txt                # Python dependencies for scraping
│   ├── scrape_njit_resources.py        # Main scraping script
│   ├── setup_index.py                  # Azure Search index setup
│   └── scheduled_ingestion.py          # Automated hourly ingestion
│
├── deployment/                         # Deployment configurations
│   ├── docker-compose.yml             # Docker Compose configuration
│   ├── Dockerfile.backend             # Backend Docker image
│   ├── Dockerfile.frontend            # Frontend Docker image
│   ├── Dockerfile.ingestion           # Data ingestion Docker image
│   ├── nginx.conf                     # Nginx configuration
│   ├── azure-config.md                # Azure deployment settings
│   └── deploy-azure.sh                # Azure deployment script
│
├── docs/                              # Documentation
│   ├── TECHNICAL_DOCUMENTATION.md     # Technical architecture docs
│   ├── SETUP_GUIDE.md                 # Setup and installation guide
│   └── CONTRIBUTING.md                # Contribution guidelines
│
└── azure-search-config.md             # Azure AI Search configuration
```

## Key Files Description

### Frontend (`frontend/`)
- **React + TypeScript**: Modern frontend with type safety
- **Tailwind CSS**: Utility-first CSS framework with custom goddess themes
- **Auth0 Integration**: Secure authentication for NJIT students
- **Chat Interface**: Real-time chat with goddess avatars and citations

### Backend (`backend/`)
- **FastAPI**: High-performance Python web framework
- **Auth0 JWT**: Token-based authentication
- **Gemini AI**: Google's AI for persona responses and intent classification
- **Azure AI Search**: Hybrid search for NJIT resources
- **MongoDB**: User profiles and chat history storage

### Data Ingestion (`data-ingestion/`)
- **Web Scraping**: Automated collection of NJIT resources
- **Azure Search Indexing**: Upload and manage search index
- **Scheduled Jobs**: Hourly automated data updates

### Deployment (`deployment/`)
- **Docker**: Containerized deployment
- **Azure**: Cloud deployment configurations
- **Nginx**: Reverse proxy and static file serving

### Documentation (`docs/`)
- **Technical Docs**: Architecture and implementation details
- **Setup Guide**: Step-by-step installation instructions
- **Contributing**: Guidelines for contributors

## Environment Variables

Each component requires specific environment variables:

### Frontend
- `VITE_AUTH0_DOMAIN`
- `VITE_AUTH0_CLIENT_ID`
- `VITE_AUTH0_AUDIENCE`
- `VITE_API_BASE_URL`

### Backend
- `AUTH0_DOMAIN`
- `AUTH0_CLIENT_ID`
- `AUTH0_CLIENT_SECRET`
- `AUTH0_AUDIENCE`
- `MONGODB_URL`
- `GEMINI_API_KEY`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX_NAME`

## Quick Start

1. **Clone**: `git clone <repository-url>`
2. **Backend**: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
3. **Frontend**: `cd frontend && npm install && npm run dev`
4. **Data**: `cd data-ingestion && python scrape_njit_resources.py && python setup_index.py`

## Architecture Flow

1. **User** logs in via Auth0
2. **Frontend** sends chat messages to backend API
3. **Backend** verifies JWT token and processes message
4. **Goddess Matcher** determines appropriate goddess persona
5. **Intent Classifier** categorizes user query
6. **Search Service** retrieves relevant NJIT resources
7. **Gemini AI** generates goddess-voiced response
8. **Response** returned to frontend with citations
9. **Data** stored in MongoDB for user profiles and chat history

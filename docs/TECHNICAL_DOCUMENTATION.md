# Gaia Mentorship - Technical Documentation

## Architecture Overview

Gaia is a women-focused mentorship web application built for NJIT students. The system uses a microservices architecture with the following components:

### Frontend (React + Vite + Tailwind)
- **Location**: `frontend/`
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom goddess-themed colors
- **Authentication**: Auth0 React SDK
- **Build Tool**: Vite for fast development and optimized builds

### Backend (FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with Python 3.11
- **Authentication**: Auth0 JWT validation
- **AI Integration**: Google Gemini for persona responses and intent classification
- **Search**: Azure AI Search for resource retrieval
- **Database**: MongoDB Atlas for user data and chat history

### Data Ingestion
- **Location**: `data-ingestion/`
- **Purpose**: Web scraping and indexing of NJIT resources
- **Scheduling**: Hourly automated ingestion
- **Sources**: Highlander Hub, Handshake, academic support pages

## Data Flow

1. **User Authentication**: Auth0 handles login and provides JWT tokens
2. **Goddess Matching**: Rules-based + embedding matching determines appropriate goddess
3. **Intent Classification**: Gemini AI classifies user queries (events, academics, career, wellness)
4. **Resource Retrieval**: Azure AI Search finds relevant NJIT resources
5. **Response Generation**: Gemini generates goddess-voiced responses grounded in retrieved resources
6. **Data Storage**: Chat messages and user profiles stored in MongoDB

## API Endpoints

### Authentication Required
- `POST /api/chat` - Main chat endpoint
- `GET /api/user/profile` - User profile information

### Public
- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /api/goddesses` - Available goddess personas

## Goddess Personas

### Athena (Academics & Wisdom)
- **Keywords**: study, academic, course, homework, exam, research, learning, education
- **Personality**: wise, strategic, scholarly, analytical, methodical
- **Response Style**: Encouraging but direct, focuses on practical academic advice

### Aphrodite (Well-being & Self-care)
- **Keywords**: wellness, mental health, stress, anxiety, self-care, relationships, emotional
- **Personality**: nurturing, empathetic, warm, caring, supportive
- **Response Style**: Warm and nurturing, focuses on emotional wellness

### Hera (Career & Leadership)
- **Keywords**: career, job, internship, leadership, professional, resume, networking
- **Personality**: authoritative, confident, powerful, ambitious, strong
- **Response Style**: Confident and empowering, focuses on career development

## Database Schema

### User Profiles Collection
```json
{
  "user_id": "auth0|...",
  "email": "user@njit.edu",
  "name": "Student Name",
  "preferred_goddess": "athena",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Chat Messages Collection
```json
{
  "message_id": "user_id_timestamp",
  "user_id": "auth0|...",
  "message": "User's question",
  "response": "Goddess response",
  "goddess": "athena",
  "citations": [
    {
      "title": "Resource Title",
      "url": "https://...",
      "source": "highlander_hub"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Environment Variables

### Frontend (.env.local)
```
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=your-api-audience
VITE_API_BASE_URL=http://localhost:8000
```

### Backend (.env)
```
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=your-api-audience
MONGODB_URL=mongodb+srv://...
GEMINI_API_KEY=your-gemini-key
AZURE_SEARCH_ENDPOINT=https://...
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=gaia-resources
```

## Deployment

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Data Ingestion
cd data-ingestion
python scrape_njit_resources.py
python setup_index.py
```

### Docker Deployment
```bash
docker-compose up -d
```

### Azure Deployment
```bash
chmod +x deployment/deploy-azure.sh
./deployment/deploy-azure.sh
```

## Security Considerations

1. **Authentication**: All API endpoints require valid Auth0 JWT tokens
2. **CORS**: Configured for specific origins only
3. **Input Validation**: Pydantic models validate all inputs
4. **Rate Limiting**: Consider implementing rate limiting for production
5. **Secrets Management**: All secrets stored in environment variables

## Monitoring & Logging

- **Health Checks**: Built-in health check endpoints
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Logging**: Structured logging for debugging and monitoring
- **Metrics**: Consider adding application metrics for production

## Performance Optimization

1. **Frontend**: Vite provides optimized builds with code splitting
2. **Backend**: FastAPI's async capabilities for high performance
3. **Search**: Azure AI Search provides fast, scalable search
4. **Caching**: Consider implementing Redis for response caching
5. **CDN**: Static assets served via CDN in production

## Extensibility

The system is designed to be easily extensible:

1. **New Goddesses**: Add configurations to `goddess_matcher.py`
2. **New Data Sources**: Extend `NJITDataIngestion` class
3. **New Intents**: Update intent classification in `chat.py`
4. **New Features**: Modular architecture supports easy feature additions

## Troubleshooting

### Common Issues

1. **Auth0 Token Issues**: Verify domain, client ID, and audience configuration
2. **MongoDB Connection**: Check connection string and network access
3. **Azure Search**: Verify endpoint, key, and index configuration
4. **Gemini API**: Check API key and quota limits

### Debug Mode
Set `APP_ENV=development` for detailed error messages and logging.

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate error handling and logging
3. Update documentation for new features
4. Test thoroughly before submitting changes
5. Follow security best practices

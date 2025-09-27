# Setup Guide for Gaia Mentorship

## Prerequisites

Before setting up the project, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **Git**
- **Docker** (optional, for containerized deployment)

## Required Services & API Keys

### 1. Auth0 Setup
1. Create an Auth0 account at [auth0.com](https://auth0.com)
2. Create a new application (Single Page Application)
3. Configure allowed callbacks and origins
4. Note down:
   - Domain
   - Client ID
   - Client Secret
   - Audience (API identifier)

### 2. MongoDB Atlas
1. Create account at [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create a new cluster
3. Create a database user
4. Get the connection string

### 3. Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Enable the Gemini API

### 4. Azure AI Search
1. Create Azure account and subscription
2. Create an Azure AI Search service
3. Note down:
   - Search endpoint URL
   - Admin key
   - Index name (use "gaia-resources")

## Local Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd gaia-mentorship
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env with your actual values
# Required variables:
# - AUTH0_DOMAIN
# - AUTH0_CLIENT_ID
# - AUTH0_CLIENT_SECRET
# - AUTH0_AUDIENCE
# - MONGODB_URL
# - GEMINI_API_KEY
# - AZURE_SEARCH_ENDPOINT
# - AZURE_SEARCH_KEY
# - AZURE_SEARCH_INDEX_NAME

# Run the backend
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp env.example .env.local

# Edit .env.local with your actual values
# Required variables:
# - VITE_AUTH0_DOMAIN
# - VITE_AUTH0_CLIENT_ID
# - VITE_AUTH0_AUDIENCE
# - VITE_API_BASE_URL

# Run the frontend
npm run dev
```

### 4. Data Ingestion Setup
```bash
cd data-ingestion

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp ../backend/env.example .env

# Edit .env with Azure Search credentials

# Run initial scraping
python scrape_njit_resources.py

# Set up Azure Search index
python setup_index.py
```

## Environment Variables Reference

### Backend (.env)
```bash
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=your-api-audience

# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/gaia_mentorship

# Google Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=gaia-resources

# Application Configuration
APP_ENV=development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend (.env.local)
```bash
# Auth0 Configuration
VITE_AUTH0_DOMAIN=your-domain.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=your-api-audience

# API Configuration
VITE_API_BASE_URL=http://localhost:8000
```

## Verification Steps

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
```
Should return: `{"status": "healthy", "version": "1.0.0"}`

### 2. Frontend Access
Open http://localhost:3000 in your browser
- Should see the Gaia landing page
- Login button should work (redirects to Auth0)

### 3. API Integration Test
After logging in, try sending a message in the chat interface
- Should receive a response from a goddess
- Citations should appear if resources are found

## Common Issues & Solutions

### 1. Auth0 Configuration Issues
**Problem**: Login redirects fail or tokens are invalid
**Solution**: 
- Verify callback URLs in Auth0 dashboard
- Check domain, client ID, and audience match exactly
- Ensure CORS origins include your frontend URL

### 2. MongoDB Connection Issues
**Problem**: Backend can't connect to MongoDB
**Solution**:
- Verify connection string format
- Check network access in MongoDB Atlas
- Ensure database user has proper permissions

### 3. Azure Search Issues
**Problem**: Search returns no results
**Solution**:
- Verify endpoint URL and key
- Check if index exists and has data
- Run data ingestion scripts to populate index

### 4. Gemini API Issues
**Problem**: AI responses fail
**Solution**:
- Verify API key is valid
- Check API quota limits
- Ensure API is enabled in Google AI Studio

## Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Azure Deployment
```bash
# Make deployment script executable
chmod +x deployment/deploy-azure.sh

# Set environment variables
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_CLIENT_ID="your-client-id"
# ... (set all required variables)

# Run deployment
./deployment/deploy-azure.sh
```

## Development Tips

1. **Hot Reloading**: Both frontend and backend support hot reloading during development
2. **API Testing**: Use the FastAPI docs at http://localhost:8000/docs
3. **Database Inspection**: Use MongoDB Compass to inspect your database
4. **Search Testing**: Use Azure Search Explorer to test search queries
5. **Logging**: Check console logs for debugging information

## Next Steps

1. Customize goddess personas in `backend/app/goddess_matcher.py`
2. Add new data sources in `data-ingestion/scrape_njit_resources.py`
3. Extend the chat interface with new features
4. Add more sophisticated AI prompts for better responses
5. Implement user preferences and personalization

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the technical documentation
3. Check GitHub issues for similar problems
4. Contact the development team

# Azure App Service Configuration

# Backend API Configuration
AZURE_WEBAPP_NAME=gaia-backend-api
AZURE_RESOURCE_GROUP=gaia-mentorship-rg
AZURE_LOCATION=eastus
AZURE_APP_SERVICE_PLAN=gaia-backend-plan

# Frontend Static Web App Configuration
AZURE_STATIC_WEB_APP_NAME=gaia-frontend
AZURE_STATIC_WEB_APP_RESOURCE_GROUP=gaia-mentorship-rg

# Environment Variables for Production
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_AUDIENCE=your-api-audience
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/gaia_mentorship
GEMINI_API_KEY=your-gemini-api-key
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=gaia-resources
APP_ENV=production
CORS_ORIGINS=https://your-frontend-url.azurestaticapps.net

#!/bin/bash

# Azure deployment script for Gaia Mentorship

set -e

echo "🚀 Starting Azure deployment for Gaia Mentorship..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Set variables
RESOURCE_GROUP="gaia-mentorship-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="gaia-backend-plan"
WEBAPP_NAME="gaia-backend-api"
STATIC_WEB_APP_NAME="gaia-frontend"

echo "📋 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "🏗️ Creating App Service plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku B1 \
    --is-linux

echo "🌐 Creating Web App for backend..."
az webapp create \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON|3.11"

echo "⚙️ Configuring environment variables..."
az webapp config appsettings set \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        AUTH0_DOMAIN="$AUTH0_DOMAIN" \
        AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID" \
        AUTH0_CLIENT_SECRET="$AUTH0_CLIENT_SECRET" \
        AUTH0_AUDIENCE="$AUTH0_AUDIENCE" \
        MONGODB_URL="$MONGODB_URL" \
        GEMINI_API_KEY="$GEMINI_API_KEY" \
        AZURE_SEARCH_ENDPOINT="$AZURE_SEARCH_ENDPOINT" \
        AZURE_SEARCH_KEY="$AZURE_SEARCH_KEY" \
        AZURE_SEARCH_INDEX_NAME="$AZURE_SEARCH_INDEX_NAME" \
        APP_ENV="production" \
        CORS_ORIGINS="https://$STATIC_WEB_APP_NAME.azurestaticapps.net"

echo "📦 Deploying backend..."
cd backend
az webapp deployment source config-zip \
    --name $WEBAPP_NAME \
    --resource-group $RESOURCE_GROUP \
    --src ../deployment/backend-deployment.zip

echo "🎨 Creating Static Web App for frontend..."
az staticwebapp create \
    --name $STATIC_WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --source https://github.com/your-username/gaia-mentorship \
    --branch main \
    --app-location "/frontend" \
    --output-location "dist"

echo "✅ Deployment completed!"
echo "Backend URL: https://$WEBAPP_NAME.azurewebsites.net"
echo "Frontend URL: https://$STATIC_WEB_APP_NAME.azurestaticapps.net"

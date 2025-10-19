#!/bin/bash

# Frontend Deployment Script
# This script helps deploy the frontend using Amplify CLI after CDK deployment

set -e

echo "🚀 Healthcare Frontend Deployment Script"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "apps/frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if Amplify CLI is installed
if ! command -v amplify &> /dev/null; then
    echo "❌ Error: Amplify CLI is not installed"
    echo "📦 Install it with: npm install -g @aws-amplify/cli"
    exit 1
fi

# Get API Gateway URL from CDK outputs
echo "📋 Getting API Gateway URL from CDK outputs..."

API_URL=$(aws cloudformation describe-stacks \
    --stack-name AWSomeBuilder2-ApiStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$API_URL" ]; then
    echo "⚠️  Warning: Could not get API Gateway URL from CDK stack"
    echo "🔧 Make sure the CDK API stack is deployed first"
    echo "💡 You can set it manually later in Amplify console"
    API_URL="https://your-api-gateway-url/v1"
else
    echo "✅ Found API Gateway URL: $API_URL"
fi

# Navigate to frontend directory
cd apps/frontend

# Check if Amplify is already initialized
if [ ! -f "amplify/.config/project-config.json" ]; then
    echo "🔧 Initializing Amplify project..."
    
    # Initialize Amplify (this will prompt for configuration)
    amplify init
    
    echo "✅ Amplify project initialized"
else
    echo "✅ Amplify project already initialized"
fi

# Set environment variables
echo "🔧 Setting environment variables..."

# Set the API URL for production environment
amplify env checkout prod 2>/dev/null || amplify env add prod

echo "📝 Setting VITE_API_BASE_URL to: $API_URL"
amplify env set VITE_API_BASE_URL "$API_URL"
amplify env set VITE_AWS_REGION "us-east-1"

# Deploy the frontend
echo "🚀 Deploying frontend to Amplify..."
amplify publish

echo ""
echo "✅ Frontend deployment completed!"
echo "🌐 Your app should be available at the Amplify URL shown above"
echo ""
echo "📝 Next steps:"
echo "   1. Visit the Amplify console to see your deployment"
echo "   2. Configure custom domain if needed"
echo "   3. Set up CI/CD if desired"

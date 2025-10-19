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

# Check if Amplify Gen2 is already initialized
if [ ! -f "amplify_outputs.json" ]; then
    echo "🔧 Starting Amplify Gen2 sandbox..."
    
    # Install dependencies
    npm install
    
    # Start sandbox (this will create the backend resources)
    echo "📦 Starting sandbox environment..."
    npx ampx sandbox --once
    
    echo "✅ Amplify Gen2 sandbox deployed"
else
    echo "✅ Amplify Gen2 already configured"
fi

# Display values for Amplify Console secrets setup
echo "🔧 CDK Resource Values (set these as secrets in Amplify Console):"
echo "   CDK_API_GATEWAY_ENDPOINT: $API_URL"

# Try to get S3 bucket name
BUCKET_NAME=$(aws s3 ls | grep healthcare | awk '{print $3}' | head -1 || echo "healthcare-documents-bucket")
echo "   CDK_S3_BUCKET_NAME: $BUCKET_NAME"
echo ""
echo "📝 Please set these values as secrets in the Amplify Console (Gen2) before deploying:"
echo "   Go to: Amplify Console → Your App → Hosting → Secrets → Manage secrets"
echo "   See apps/frontend/AMPLIFY_SECRETS.md for detailed instructions."
echo ""

# Build the frontend
echo "🏗️  Building frontend..."
npm run build

# Deploy to production
echo "🚀 Deploying frontend to Amplify..."
npx ampx deploy --branch main

echo ""
echo "✅ Frontend deployment completed!"
echo "🌐 Your app should be available at the Amplify URL shown above"
echo ""
echo "📝 Next steps:"
echo "   1. Visit the Amplify console to see your deployment"
echo "   2. Configure custom domain if needed"
echo "   3. Set up CI/CD if desired"

#!/bin/bash

# Build Healthcare Assistant Agent container locally for testing
# Note: CDK will handle building and pushing to ECR automatically during deployment
# Usage: ./scripts/build-agent-container.sh [IMAGE_TAG]

set -e

# Configuration
IMAGE_TAG=${1:-latest}
REPOSITORY_NAME="healthcare-assistant"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Healthcare Assistant Agent Container (Local)${NC}"
echo "Repository: $REPOSITORY_NAME"
echo "Tag: $IMAGE_TAG"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Build the Docker image for local testing
echo -e "${YELLOW}Building Docker image for local testing...${NC}"
docker build --platform linux/arm64 -t $REPOSITORY_NAME:$IMAGE_TAG ./agents

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}Docker image built successfully: $REPOSITORY_NAME:$IMAGE_TAG${NC}"

# Test the container locally
echo -e "${YELLOW}Testing container health check...${NC}"
CONTAINER_ID=$(docker run -d --platform linux/arm64 -p 8080:8080 $REPOSITORY_NAME:$IMAGE_TAG)

# Wait for container to start
sleep 10

# Check if container is running
if docker ps | grep -q $CONTAINER_ID; then
    echo -e "${GREEN}Container is running successfully${NC}"
    
    # Test health endpoint
    if curl -f http://localhost:8080/ping > /dev/null 2>&1; then
        echo -e "${GREEN}Health check passed${NC}"
    else
        echo -e "${YELLOW}Health check failed (this is expected without AWS credentials)${NC}"
    fi
else
    echo -e "${RED}Container failed to start${NC}"
    docker logs $CONTAINER_ID
fi

# Clean up test container
docker stop $CONTAINER_ID > /dev/null 2>&1 || true
docker rm $CONTAINER_ID > /dev/null 2>&1 || true

echo ""
echo -e "${GREEN}Local container build and test completed!${NC}"
echo "Image: $REPOSITORY_NAME:$IMAGE_TAG"
echo ""
echo "Next steps:"
echo "1. Run 'cdk deploy AssistantStack' to build and deploy with ECR assets"
echo "2. CDK will automatically build and push the container to ECR"
echo "3. The AgentCore Runtime will be updated with the new container"
echo ""
echo "For local development:"
echo "- Use 'cd agents && docker-compose up' to run with local configuration"
echo "- Set environment variables in .env file for testing"

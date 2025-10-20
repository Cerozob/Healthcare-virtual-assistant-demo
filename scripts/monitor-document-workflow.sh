#!/bin/bash

# Document Workflow Monitoring Script
# Monitors the status of document processing

set -e

echo "📊 Healthcare Document Workflow Monitor"
echo "======================================"

# Get stack outputs
RAW_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name AWSomeBuilder2-DocumentWorkflowStack \
    --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$RAW_BUCKET" ]; then
    echo "❌ Error: Could not get bucket information from CloudFormation"
    exit 1
fi

echo "🔍 Monitoring workflow status..."
echo ""

# Check S3 buckets
echo "📁 S3 Bucket Status:"
echo "   Raw bucket: $RAW_BUCKET"
RAW_COUNT=$(aws s3 ls "s3://$RAW_BUCKET/documents/" --recursive | wc -l)
echo "   📄 Documents in raw bucket: $RAW_COUNT"

# Try to get processed bucket
PROCESSED_BUCKET=$(aws ssm get-parameter \
    --name "/healthcare/document-workflow/processed-bucket" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || echo "")

if [ -n "$PROCESSED_BUCKET" ]; then
    echo "   Processed bucket: $PROCESSED_BUCKET"
    PROCESSED_COUNT=$(aws s3 ls "s3://$PROCESSED_BUCKET/" --recursive | wc -l)
    echo "   📄 Processed files: $PROCESSED_COUNT"
else
    echo "   ⚠️  Processed bucket parameter not found"
fi

echo ""

# Check Lambda function logs
echo "📋 Recent Lambda Executions:"

# BDA Trigger Lambda
echo "   🤖 BDA Trigger Lambda:"
BDA_LOGS=$(aws logs describe-log-streams \
    --log-group-name "/aws/lambda/healthcare-bda-trigger" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null || echo "")

if [ "$BDA_LOGS" != "None" ] && [ -n "$BDA_LOGS" ]; then
    LAST_BDA=$(aws logs get-log-events \
        --log-group-name "/aws/lambda/healthcare-bda-trigger" \
        --log-stream-name "$BDA_LOGS" \
        --limit 5 \
        --query 'events[-1].timestamp' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$LAST_BDA" ] && [ "$LAST_BDA" != "None" ]; then
        LAST_BDA_TIME=$(date -d "@$((LAST_BDA/1000))" 2>/dev/null || echo "Unknown")
        echo "      ✅ Last execution: $LAST_BDA_TIME"
    else
        echo "      ⚠️  No recent executions found"
    fi
else
    echo "      ⚠️  No log streams found"
fi

# Data Extraction Lambda
echo "   📊 Data Extraction Lambda:"
EXTRACT_LOGS=$(aws logs describe-log-streams \
    --log-group-name "/aws/lambda/healthcare-data-extraction" \
    --order-by LastEventTime \
    --descending \
    --max-items 1 \
    --query 'logStreams[0].logStreamName' \
    --output text 2>/dev/null || echo "")

if [ "$EXTRACT_LOGS" != "None" ] && [ -n "$EXTRACT_LOGS" ]; then
    LAST_EXTRACT=$(aws logs get-log-events \
        --log-group-name "/aws/lambda/healthcare-data-extraction" \
        --log-stream-name "$EXTRACT_LOGS" \
        --limit 5 \
        --query 'events[-1].timestamp' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$LAST_EXTRACT" ] && [ "$LAST_EXTRACT" != "None" ]; then
        LAST_EXTRACT_TIME=$(date -d "@$((LAST_EXTRACT/1000))" 2>/dev/null || echo "Unknown")
        echo "      ✅ Last execution: $LAST_EXTRACT_TIME"
    else
        echo "      ⚠️  No recent executions found"
    fi
else
    echo "      ⚠️  No log streams found"
fi

echo ""

# Check EventBridge rule
echo "🎯 EventBridge Rule Status:"
RULE_STATUS=$(aws events describe-rule \
    --name "healthcare-bda-completion" \
    --query 'State' \
    --output text 2>/dev/null || echo "NOT_FOUND")

echo "   Rule 'healthcare-bda-completion': $RULE_STATUS"

# Check recent EventBridge events (if possible)
echo ""
echo "📈 Recent Activity Summary:"
echo "   Use AWS Console to check:"
echo "   - CloudWatch Logs for detailed execution logs"
echo "   - Bedrock Data Automation console for processing status"
echo "   - EventBridge console for rule executions"
echo "   - S3 console for file processing results"

echo ""
echo "🔗 Useful AWS Console Links:"
echo "   CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups"
echo "   Bedrock: https://console.aws.amazon.com/bedrock/home"
echo "   EventBridge: https://console.aws.amazon.com/events/home"
echo "   S3: https://console.aws.amazon.com/s3/home"

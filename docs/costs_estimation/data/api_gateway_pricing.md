# Amazon API Gateway Pricing - US East (N. Virginia)

**Region**: us-east-1  
**Pricing Date**: October 2025  
**Source**: AWS Pricing API via MCP Server  
**Effective Date**: July 1, 2025

## Overview

Amazon API Gateway offers three types of APIs with different pricing models:
- **HTTP APIs**: Cost-optimized for building RESTful APIs
- **REST APIs**: Full-featured APIs with more capabilities
- **WebSocket APIs**: Real-time two-way communication

## HTTP API Pricing

**Service**: API Gateway HTTP API  
**Operation**: `ApiGatewayHttpApi`  
**Usage Type**: `USE1-ApiGatewayHttpRequest`  
**SKU**: FC2TWT2UEPTBKVBX

### Request Pricing (Tiered)

| Volume | Price per Million Requests | Price per Request |
|--------|---------------------------|-------------------|
| First 300 million requests/month | $1.00 | $0.0000010000 |
| Over 300 million requests/month | $0.90 | $0.0000009000 |

### Key Features
- Lower cost than REST APIs
- Automatic deployments
- CORS support
- JWT authorizers
- No data transfer charges for API Gateway itself (see Data Transfer section)

## REST API Pricing

**Service**: API Gateway REST API  
**Operation**: `ApiGatewayRequest`  
**Usage Type**: `USE1-ApiGatewayRequest`  
**SKU**: KKDZ3TFSXUSMCZ3A

### Request Pricing (Tiered)

| Volume | Price per Million Requests | Price per Request |
|--------|---------------------------|-------------------|
| First 333 million requests/month | $3.50 | $0.0000035000 |
| Next 667 million requests/month (333M - 1B) | $2.80 | $0.0000028000 |
| Next 19 billion requests/month (1B - 20B) | $2.38 | $0.0000023800 |
| Over 20 billion requests/month | $1.51 | $0.0000015100 |

### Key Features
- Full API management capabilities
- API keys and usage plans
- Request/response transformations
- API caching (additional cost)
- Custom domain names
- More authorization options

## WebSocket API Pricing

**Service**: API Gateway WebSocket  
**Operation**: `ApiGatewayWebSocket`  
**Product Family**: WebSocket

### Message Pricing (Tiered)

**Usage Type**: `USE1-ApiGatewayMessage`  
**SKU**: 3Y5E3ETY2M5CMHYP

| Volume | Price per Million Messages | Price per Message |
|--------|---------------------------|-------------------|
| First 1 billion messages/month | $1.00 | $0.0000010000 |
| Over 1 billion messages/month | $0.80 | $0.0000008000 |

### Connection Minutes Pricing

**Usage Type**: `USE1-ApiGatewayMinute`  
**SKU**: UTA8VPBNDBWNCNMC

| Volume | Price per Million Minutes | Price per Minute |
|--------|---------------------------|-------------------|
| All connection minutes | $0.25 | $0.0000002500 |

### Key Features
- Persistent connections
- Real-time two-way communication
- Message routing
- Connection management
- Charged for both messages and connection duration

## Data Transfer Pricing

**Service**: AWS Data Transfer  
**Transfer Type**: AWS Outbound  
**From Location**: US East (N. Virginia)  
**To Location**: External (Internet)  
**SKU**: HQEH3ZWJVT46JHRG

### Data Transfer Out (Tiered)

| Volume | Price per GB |
|--------|-------------|
| First 10 TB/month | $0.09 |
| Next 40 TB/month (10 TB - 50 TB) | $0.085 |
| Next 100 TB/month (50 TB - 150 TB) | $0.07 |
| Over 150 TB/month | $0.05 |

### Notes on Data Transfer
- **Data Transfer IN**: Free for all API types
- **Data Transfer OUT**: Charged at standard AWS data transfer rates (above)
- **Between AWS Services**: Data transfer between API Gateway and other AWS services in the same region is typically free
- **CloudFront Integration**: Using CloudFront can reduce data transfer costs

## API Caching Pricing

[NEEDS REVIEW] - Cache pricing data not retrieved in this query. Cache pricing varies by cache size (0.5GB to 237GB) and is charged per hour.

**Known Cache Sizes Available**:
- 0.5 GB
- 1.55 GB
- 6.05 GB
- 13.5 GB
- 28.4 GB
- 58.2 GB
- 118 GB
- 237 GB

**Action Required**: Run separate query for cache pricing if caching is planned for the implementation.

## Free Tier

**HTTP APIs**: 
- 1 million API calls per month for 12 months (AWS Free Tier)

**REST APIs**:
- 1 million API calls per month for 12 months (AWS Free Tier)

**WebSocket APIs**:
- 1 million messages and 750,000 connection minutes per month for 12 months (AWS Free Tier)

**Data Transfer**:
- 100 GB/month data transfer out aggregated across all AWS services (first 12 months)

## Cost Comparison: HTTP API vs REST API

For the AWSomeBuilder2 healthcare system using **10,000 MAU** with **10M requests/month**:

### HTTP API Cost
```
10M requests × $1.00/1M = $10.00/month
```

### REST API Cost
```
10M requests × $3.50/1M = $35.00/month
```

**Savings with HTTP API**: $25.00/month (71% cost reduction)

## Recommendations for AWSomeBuilder2

1. **Use HTTP APIs**: The system currently uses HTTP APIs, which is optimal for cost
2. **No Caching Needed Initially**: With 10M requests/month, caching adds cost without significant benefit
3. **Monitor Data Transfer**: Track data transfer costs separately; optimize response payload sizes
4. **WebSocket Not Required**: Current architecture doesn't use WebSockets (agent integration uses HTTP)
5. **Stay in Free Tier**: First 12 months benefit from 1M free requests/month

## Usage Assumptions for Production (10K MAU)

Based on the design document:
- **API Type**: HTTP API (cost-optimized)
- **Monthly Requests**: 10M requests (10K MAU × 20 sessions × 50 API calls)
- **Peak Load**: 30,000 RPM during business hours
- **Average Request Size**: 5 KB
- **Average Response Size**: 10 KB
- **Data Transfer Out**: ~150 GB/month (10M × 15 KB average)

## Monthly Cost Calculation (Production)

### API Gateway HTTP API
```
Requests: 10M × $1.00/1M = $10.00
Data Transfer: 150 GB × $0.09 = $13.50
─────────────────────────────────
Total API Stack: $23.50/month
```

**Note**: Data transfer is typically included in overall AWS data transfer calculations and may be optimized with CloudFront or other CDN solutions.

## Scaling Scenarios

### 50K MAU (5x Growth)
```
Requests: 50M × $1.00/1M = $50.00
Data Transfer: 750 GB × $0.09 = $67.50
Total: $117.50/month
```

### 100K MAU (10x Growth)
```
Requests: 100M × $1.00/1M = $100.00
Data Transfer: 1,500 GB × $0.09 = $135.00
Total: $235.00/month
```

### 500K MAU (50x Growth)
```
Requests: 500M × $0.95/1M = $475.00 (volume discount applies)
Data Transfer: 7,500 GB × $0.087 = $652.50 (blended rate)
Total: $1,127.50/month
```

## Optimization Opportunities

1. **Response Compression**: Enable gzip compression to reduce data transfer costs by 60-80%
2. **Payload Optimization**: Minimize JSON response sizes through field selection
3. **CloudFront Integration**: Use CloudFront for caching and reduced data transfer costs
4. **Request Batching**: Combine multiple operations into single API calls where possible
5. **Throttling Configuration**: Implement appropriate throttling to prevent cost overruns

## Additional Considerations

### Throttling Limits (Default)
- **Account-level**: 10,000 requests per second (RPS)
- **Regional**: Can be increased via support ticket
- **Per-API**: Configurable (current: 100 RPS, 200 burst)

### Monitoring Recommendations
- Set up CloudWatch alarms for request count thresholds
- Monitor 4XX and 5XX error rates (don't pay for failed requests)
- Track data transfer patterns
- Review API Gateway metrics weekly

### Security Considerations
- JWT authorizers: No additional cost
- Lambda authorizers: Lambda execution costs apply
- WAF integration: Separate WAF pricing applies
- Custom domain names: Route 53 costs apply

## References

- AWS API Gateway Pricing: https://aws.amazon.com/api-gateway/pricing/
- AWS Data Transfer Pricing: https://aws.amazon.com/ec2/pricing/on-demand/#Data_Transfer
- API Gateway Quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html

## Validation Notes

✅ HTTP API pricing verified via AWS Pricing API  
✅ REST API pricing verified via AWS Pricing API  
✅ WebSocket API pricing verified via AWS Pricing API  
✅ Data Transfer pricing verified via AWS Pricing API  
⚠️ [NEEDS REVIEW] Cache pricing not included - requires separate query if needed  
✅ Pricing effective as of July 1, 2025  
✅ All prices in USD for us-east-1 region

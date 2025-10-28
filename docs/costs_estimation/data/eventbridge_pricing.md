# Amazon EventBridge Pricing Data (US East - N. Virginia)

**Source**: AWS Pricing API  
**Region**: us-east-1 (US East - N. Virginia)  
**Date Retrieved**: October 28, 2025  
**Service Code**: AWSEvents

## Custom Events

### Custom Event Publishing (PutEvents)
- **Price**: $1.00 per million events
- **Unit**: Per million 64K chunks
- **Description**: EventBridge custom events received
- **Use Case**: Application-generated events, S3 notifications, custom workflows

## Partner Events

### Partner Event Publishing
- **Price**: $1.00 per million events  
- **Unit**: Per million 64K chunks
- **Description**: EventBridge partner events received
- **Use Case**: Third-party SaaS integrations

## Cross-Account Event Invocations

### Custom Events (Cross-Account)
- **Price**: $0.05 per million invocations
- **Unit**: Per million 64K chunks
- **Description**: Cross-account invocations with custom events

### Partner Events (Cross-Account)
- **Price**: $0.05 per million invocations
- **Unit**: Per million 64K chunks  
- **Description**: Cross-account invocations with partner events

### AWS Management Events (Cross-Account)
- **Price**: $1.00 per million invocations
- **Unit**: Per million 64K chunks
- **Description**: Cross-account invocations with AWS management events

## EventBridge Scheduler

### Scheduled Invocations
- **Free Tier**: First 14 million invocations per month
- **Paid Tier**: $1.00 per million invocations (after free tier)
- **Unit**: Per invocation
- **Description**: Scheduled rule invocations

## EventBridge Pipes

### Pipe Requests
- **Price**: $0.40 per million requests
- **Unit**: Per million 64K chunks
- **Description**: EventBridge Pipes processing requests

## API Destinations

### API Destination Invocations
- **Price**: $0.20 per million invocations
- **Unit**: Per million 64K chunks
- **Description**: Invocations of API Destinations

## Schema Discovery

### Schema Discovery Events
- **Price**: $0.10 per million events
- **Unit**: Per million 8K chunks
- **Description**: Events ingested for schema discovery

## Event Archive and Replay

### Event Archive Storage
- **Price**: $0.10 per GB-month
- **Unit**: Per GB-month
- **Description**: Storage for archived events

### Event Storage (Standard)
- **Price**: $0.023 per GB-month
- **Unit**: Per GB-month
- **Description**: Standard storage for events

## Rule Evaluations

**[NEEDS REVIEW]** - Rule evaluation pricing not explicitly found in API results. Typically:
- Rule evaluations are included in the event publishing cost
- No separate charge for rule pattern matching
- Charges apply when events are delivered to targets

## Data Transfer

**[NEEDS REVIEW]** - Data transfer pricing not found in EventBridge-specific results. Standard AWS data transfer rates apply:
- Same-region transfers: No charge
- Cross-region transfers: Standard AWS data transfer rates
- Internet egress: Standard AWS data transfer rates

## Free Tier

### AWS Events (Default Event Bus)
- **Free**: All AWS service events (CloudWatch Events)
- **Description**: Events from AWS services like EC2, S3, etc. are free

### EventBridge Scheduler Free Tier
- **Free**: First 14 million scheduled invocations per month
- **Ongoing**: Free tier applies monthly

## Event Size and Chunking

### Event Size Limits
- **Maximum Event Size**: 256 KB
- **Chunking**: Events are charged in 64K chunks (8K for schema discovery)
- **Minimum Charge**: 1 chunk per event regardless of actual size

## Notes and Assumptions

1. **Pricing Effective Date**: July 1, 2025
2. **Currency**: USD
3. **Billing Period**: Monthly
4. **Event Chunking**: 
   - Most operations use 64K chunks
   - Schema discovery uses 8K chunks
5. **Free AWS Events**: Events from AWS services to default event bus are free
6. **Cross-Account**: Additional charges apply for cross-account event delivery

## Missing Data Requiring Review

The following pricing components were not found in the API results and require manual verification:

1. **Rule Evaluation Costs**: Whether rule pattern matching incurs separate charges
2. **Data Transfer Costs**: Cross-region and internet egress pricing
3. **Event Replay Costs**: Pricing for replaying archived events
4. **Dead Letter Queue**: Costs for failed event delivery handling
5. **Event Filtering**: Whether content-based filtering incurs additional costs
6. **Custom Bus Pricing**: Costs for custom event buses vs default bus

## Validation Required

**[NEEDS REVIEW]** The following items require human validation:
- Rule evaluation methodology and any associated costs
- Data transfer pricing for cross-region event delivery
- Event replay pricing structure
- Custom event bus vs default event bus pricing differences
- Integration costs with specific AWS services
- Batch event publishing discounts or optimizations

## Use Case Pricing Examples

### Document Workflow Events (Estimated)
Based on task requirements for S3 uploads and BDA completions:
- **S3 Upload Events**: Free (AWS service events)
- **Custom Workflow Events**: $1.00 per million events
- **Cross-Account Delivery**: Additional $0.05 per million (if applicable)

### Typical Monthly Costs
- **10M custom events**: $10.00
- **5M scheduled invocations**: Free (within 14M free tier)
- **1M API destination calls**: $0.20
- **100GB event archive**: $10.00

## API Query Details

- **Service Code**: AWSEvents
- **Filters Applied**: Location: US East (N. Virginia)
- **Output Options**: OnDemand pricing terms only
- **Product Families**: EventBridge, CloudWatch Events
- **Date Retrieved**: October 28, 2025

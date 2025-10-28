# Amazon CloudWatch and AWS CloudTrail Pricing Data (US East - N. Virginia)

**Source**: AWS Pricing API  
**Region**: us-east-1 (US East - N. Virginia)  
**Date Retrieved**: October 28, 2025  
**Service Codes**: AmazonCloudWatch, AWSCloudTrail

## CloudWatch Logs

### Log Ingestion (Standard Log Class)
- **Custom Logs**: $0.50 per GB ingested
- **Vended Logs** (tiered pricing):
  - First 10TB: $0.50 per GB
  - Next 20TB: $0.25 per GB  
  - Next 20TB: $0.10 per GB
  - Over 50TB: $0.05 per GB

### Log Ingestion (Infrequent Access Log Class)
- **Custom Logs**: $0.25 per GB ingested
- **Vended Logs** (tiered pricing):
  - First 10TB: $0.25 per GB
  - Next 20TB: $0.15 per GB
  - Next 20TB: $0.075 per GB
  - Over 50TB: $0.05 per GB

### Log Storage
- **Standard Storage**: $0.03 per GB-month
- **Note**: Storage pricing applies to both Standard and Infrequent Access log classes

### Log Queries and Analysis
- **CloudWatch Logs Insights**: $0.005 per GB scanned
- **Live Tail Sessions**: $0.01 per minute of session

### Log Export and Delivery
- **Export to S3** (tiered pricing):
  - First 10TB: $0.25 per GB
  - Next 20TB: $0.15 per GB
  - Next 20TB: $0.075 per GB
  - Over 50TB: $0.05 per GB

- **Export to Kinesis Firehose** (tiered pricing):
  - First 10TB: $0.25 per GB
  - Next 20TB: $0.15 per GB
  - Next 20TB: $0.075 per GB
  - Over 50TB: $0.05 per GB

### Data Processing and Transformation
- **Parquet Conversion**: $0.03 per GB converted
- **Data Protection Scanning**: $0.12 per GB scanned

## CloudWatch Metrics

### Custom Metrics (Tiered Pricing)
- **First 10,000 metrics**: $0.30 per metric-month
- **Next 240,000 metrics**: $0.10 per metric-month
- **Next 750,000 metrics**: $0.05 per metric-month
- **Over 1,000,000 metrics**: $0.02 per metric-month

### Container Insights Metrics
- **ECS Container Insights**: $0.07 per metric-month
- **EKS Container Insights**: Observation-based pricing:
  - First 1B observations: $0.21 per million observations
  - Next 3B observations: $0.18 per million observations
  - Over 4B observations: $0.10 per million observations

### Metric Streams
- **Metric Updates**: $0.003 per 1,000 metric updates

## CloudWatch Alarms

### Standard Alarms
- **Standard Resolution**: $0.10 per alarm-month
- **High Resolution**: $0.30 per alarm-month
- **Composite Alarms**: $0.50 per alarm-month
- **Metric Insight Alarms**: $0.10 per metric analyzed per month

## CloudWatch API Requests

### Metric Data APIs
- **GetMetricData**: $0.01 per 1,000 metrics requested
- **GetMetricWidgetImage**: $0.02 per 1,000 metrics requested
- **GetInsightRuleReport**: $0.01 per 1,000 metrics requested
- **General API Requests**: $0.01 per 1,000 requests

## CloudWatch Synthetics (Canaries)
- **Canary Runs**: $0.0012 per canary run

## CloudWatch Application Monitoring

### Real User Monitoring (RUM)
- **RUM Events**: $1.00 per 100,000 events
- **Free Tier**: First-time users get free events (limited)

### Application Signals
- **First 100M signals**: $1.50 per million signals
- **Next 900M signals**: $0.75 per million signals  
- **Over 1B signals**: $0.30 per million signals

### Application Signals Data Ingestion
- **First 10TB**: $0.35 per GB
- **Next 20TB**: $0.20 per GB
- **Over 30TB**: $0.15 per GB

### CloudWatch Evidently
- **Events**: $5.00 per million events
- **Analysis Units**: $7.50 per million analysis units
- **Free Trial**: First 3M events and 10M analysis units free

## CloudWatch Database Insights

### RDS Database Insights
- **Provisioned Instances**: $0.0125 per vCPU-hour monitored
- **Aurora Serverless**: $0.003125 per ACU-hour monitored

## CloudWatch Network Monitoring

### Internet Monitor
- **Monitored Resources**: $0.01 per resource per hour
- **City-Networks**: $0.74 per 10,000 city-networks per hour

### Network Flow Monitor
- **Resource Hours**: $0.0069 per monitored resource hour

### Network Monitor (Hybrid)
- **Monitoring Hours**: $0.10 per hour

## CloudWatch Contributor Insights

### Rules and Events
- **CloudWatch Logs Rules**: $0.50 per rule per month
- **DynamoDB Rules**: $0.50 per rule per month
- **PrivateLink Rules**: $9.00 per rule per month
- **Events Processing**: $0.02 per million events
- **DynamoDB Events**: $0.03 per million events

## CloudWatch X-Ray Integration
- **Spans Indexed**: $0.00000075 per span indexed

## CloudWatch Centralization
- **Centralized Data**: $0.05 per GB

---

# AWS CloudTrail Pricing

## CloudTrail Event Recording

### Management Events
- **Free Events**: $0.00 (first copy of management events per region)
- **Paid Events**: $0.02 per 100,000 events (additional copies)

### Data Events
- **Data Events**: $0.001 per 1,000 events ($1.00 per million events)

### Network Activity Events
- **Network Events**: $0.001 per 1,000 events ($1.00 per million events)

### CloudTrail Insights
- **Insights Events**: $0.0035 per 1,000 events analyzed ($3.50 per million events)

## CloudTrail Lake (Event Data Store)

### Data Ingestion (Tiered Pricing)
- **First 5TB**: $2.50 per GB
- **Next 20TB**: $1.00 per GB  
- **Over 25TB**: $0.50 per GB

### Data Ingestion with 1-Year Retention
- **Live CloudTrail Logs**: $0.75 per GB
- **Other Data Sources**: $0.50 per GB

### Data Storage
- **Extended Retention**: $0.023 per GB-month (beyond default retention)

### Data Queries
- **Query Scanned Data**: $0.005 per GB scanned
- **Free Trial**: Free query scanning during trial period

## CloudTrail Free Tier

### Always Free
- **First Management Event Copy**: Free per region
- **Default Event History**: 90 days of management events (free)

### Trial Benefits
- **Free Trial Ingestion**: Limited free ingestion for new users
- **Free Trial Queries**: Limited free query scanning

## Use Case Pricing Examples

### Basic CloudTrail Setup
- **Management Events Only**: Free (first copy)
- **S3 Data Events**: 10M events × $0.001 = $10.00/month
- **CloudTrail Insights**: 1M events × $0.0035 = $3.50/month

### CloudWatch Logs for Lambda Functions
- **Log Ingestion**: 50GB × $0.50 = $25.00/month
- **Log Storage**: 100GB × $0.03 = $3.00/month
- **Log Queries**: 10GB scanned × $0.005 = $0.05/month

### CloudWatch Metrics and Alarms
- **Custom Metrics**: 100 metrics × $0.30 = $30.00/month (first 10K tier)
- **Standard Alarms**: 50 alarms × $0.10 = $5.00/month
- **API Requests**: 100K requests × $0.01/1K = $1.00/month

## Notes and Assumptions

1. **Pricing Effective Date**: September 1, 2025 (CloudWatch), July 1, 2025 (CloudTrail)
2. **Currency**: USD
3. **Billing Period**: Monthly
4. **Free Tier**: 
   - CloudWatch: 10 custom metrics, 10 alarms, 1M API requests, 5GB log ingestion
   - CloudTrail: First copy of management events per region
5. **Vended Logs**: Include AWS service logs (VPC Flow Logs, CloudFront, WAF, etc.)

## Missing Data Requiring Review

The following pricing components were not found in the API results and require manual verification:

1. **CloudWatch Dashboard Pricing**: Custom dashboard costs
2. **CloudWatch Cross-Region Data Transfer**: Costs for cross-region log replication
3. **CloudTrail Cross-Region Replication**: Costs for multi-region trails
4. **CloudWatch Anomaly Detection**: Machine learning-based anomaly detection costs
5. **CloudWatch ServiceLens**: Application performance monitoring costs

## Validation Required

**[NEEDS REVIEW]** The following items require human validation:
- Dashboard pricing structure and costs
- Cross-region data transfer rates for logs and events
- Anomaly detection and machine learning feature pricing
- ServiceLens and application performance monitoring costs
- Integration costs with other AWS services
- Volume discounts for enterprise customers

## API Query Details

- **Service Codes**: AmazonCloudWatch, AWSCloudTrail
- **Filters Applied**: Location: US East (N. Virginia)
- **Output Options**: OnDemand pricing terms only
- **Product Families**: Multiple (Logs, Metrics, Alarms, Events, etc.)
- **Date Retrieved**: October 28, 2025

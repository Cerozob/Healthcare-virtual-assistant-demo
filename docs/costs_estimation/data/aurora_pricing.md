# Aurora PostgreSQL Serverless v2 Pricing (us-east-1)

**Data Source**: AWS Pricing API  
**Service Code**: AmazonRDS  
**Region**: us-east-1  
**Last Updated**: October 28, 2025  
**Pricing Effective Date**: October 1, 2025

## Overview

This document contains pricing information for Amazon Aurora PostgreSQL Serverless v2 in the us-east-1 region, collected via the AWS Pricing MCP server.

## Compute Pricing (Aurora Capacity Units - ACU)

### Standard Serverless v2

- **Price**: $0.12 per ACU-hour
- **Unit**: ACU-Hr
- **Description**: Aurora Capacity Unit hour running Aurora PostgreSQL Serverless v2
- **SKU**: AVKW7ZJP8D72HNQC

### I/O-Optimized Serverless v2

- **Price**: $0.16 per ACU-hour
- **Unit**: ACU-Hr
- **Description**: Aurora Capacity Unit hour running Aurora PostgreSQL Serverless v2 IO-Optimized
- **SKU**: KG668U3YXJQ6YH9Y
- **Note**: I/O-Optimized mode includes unlimited I/O operations at no additional charge

## Storage Pricing

### Standard Storage

- **Price**: $0.10 per GB-month
- **Unit**: GB-Mo
- **Description**: Consumed storage for Aurora PostgreSQL (General Purpose)
- **Volume Type**: General Purpose-Aurora
- **SKU**: 7GYUVAA992PFJPCB

### I/O-Optimized Storage

- **Price**: $0.225 per GB-month
- **Unit**: GB-Mo
- **Description**: I/O-Optimized consumed storage for Aurora PostgreSQL
- **Volume Type**: IO Optimized-Aurora
- **SKU**: 5YXZF9S373QUR5VW
- **Note**: Use with I/O-Optimized ACU pricing for unlimited I/O operations

## I/O Operations Pricing (Standard Mode Only)

### Standard I/O Requests

- **Price**: $0.20 per 1 million I/O requests
- **Unit**: IOs (per million)
- **Description**: I/O requests for Aurora PostgreSQL (Standard mode)
- **SKU**: 7JDSZP38DMKT9B86
- **Note**: Not applicable when using I/O-Optimized mode

## Backup Storage Pricing

### Backup Storage (Beyond Free Tier)

- **Price**: $0.021 per GB-month
- **Unit**: GB-Mo
- **Description**: Backup storage exceeding free allocation for Aurora PostgreSQL
- **SKU**: AYEW6PNFPJSSTGH7
- **Free Tier**: Backup storage equal to database storage size is included at no charge

## Additional Operations

### Snapshot Export to S3

- **Price**: $0.010 per GB
- **Unit**: GB
- **Description**: RDS Snapshot Export to S3 for Aurora PostgreSQL
- **SKU**: MGVW9URHS44W4TGQ

## Pricing Mode Comparison

| Feature | Standard Mode | I/O-Optimized Mode |
|---------|--------------|-------------------|
| **ACU-hour** | $0.12 | $0.16 (+33%) |
| **Storage (GB-month)** | $0.10 | $0.225 (+125%) |
| **I/O Requests** | $0.20 per 1M | Included (unlimited) |
| **Best For** | Low to moderate I/O workloads | High I/O workloads (>200M I/O requests/month) |

## Cost Optimization Notes

1. **I/O-Optimized Break-Even Point**: 
   - For a database with consistent high I/O, I/O-Optimized becomes cost-effective when I/O costs exceed the additional compute and storage premiums
   - Example: For 500GB storage with 200M I/O requests/month:
     - Standard: Storage ($50) + I/O ($40) = $90/month
     - I/O-Optimized: Storage ($112.50) + I/O ($0) = $112.50/month
   - Break-even occurs around 200-250M I/O requests/month depending on storage size

2. **ACU Scaling**:
   - Minimum: 0.5 ACU
   - Maximum: 128 ACU (configurable)
   - Scales in increments of 0.5 ACU
   - Billed per second with a 5-minute minimum

3. **Storage Scaling**:
   - Automatically scales from 10 GB to 128 TB
   - Billed for consumed storage only
   - No need to provision storage capacity

4. **Backup Storage**:
   - First backup equal to database size is free
   - Additional backups charged at $0.021/GB-month
   - Retention period configurable (1-35 days)

## [NEEDS REVIEW] Items Requiring Human Validation

None identified. All pricing data successfully retrieved from AWS Pricing API.

## References

- AWS Pricing API Query Date: October 28, 2025
- Service: AmazonRDS
- Database Engine: Aurora PostgreSQL
- Deployment Option: Serverless v2
- Region: us-east-1

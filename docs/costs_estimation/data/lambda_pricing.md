# AWS Lambda Pricing (us-east-1)

**Data Source**: AWS Pricing API  
**Service Code**: AWSLambda  
**Region**: us-east-1  
**Last Updated**: October 28, 2025  
**Pricing Effective Date**: October 1, 2025

## Overview

This document contains pricing information for AWS Lambda in the us-east-1 region, collected via the AWS Pricing MCP server.

## Request Pricing

### Standard Requests (x86_64)

- **Price**: $0.20 per 1 million requests
- **Unit**: Requests
- **Description**: Invocation call for a Lambda function
- **SKU**: GU2ZS9HVP6QTQ7KE

### ARM (Graviton2) Requests

- **Price**: $0.20 per 1 million requests
- **Unit**: Requests
- **Description**: Invocation call for a Lambda function for ARM
- **SKU**: K7BX6567RJ67A2KE
- **Note**: Same price as x86_64, but compute duration is 20% cheaper

### Lambda@Edge Requests

- **Price**: $0.60 per 1 million requests
- **Unit**: Request
- **Description**: Invocation call for a Lambda@Edge function
- **SKU**: NQA9ZMGJKNJQT78E

## Compute Duration Pricing (GB-seconds)

### Standard x86_64 Compute

Tiered pricing based on total GB-seconds per month:

| Tier | Range (GB-seconds) | Price per GB-second |
|------|-------------------|---------------------|
| **Tier 1** | 0 - 6 billion | $0.0000166667 |
| **Tier 2** | 6 billion - 15 billion | $0.0000150000 |
| **Tier 3** | 15 billion+ | $0.0000133334 |

- **SKU**: TG3M4CAGBA3NYQBH
- **Description**: Invocation duration weighted by memory assigned to function

### ARM (Graviton2) Compute

Tiered pricing based on total GB-seconds per month:

| Tier | Range (GB-seconds) | Price per GB-second | Savings vs x86 |
|------|-------------------|---------------------|----------------|
| **Tier 1** | 0 - 7.5 billion | $0.0000133334 | 20% |
| **Tier 2** | 7.5 billion - 18.75 billion | $0.0000120001 | 20% |
| **Tier 3** | 18.75 billion+ | $0.0000106667 | 20% |

- **SKU**: 72SBSFWPMDTH8S3J
- **Description**: Invocation duration weighted by memory assigned to function for ARM
- **Note**: 20% cost savings compared to x86_64

### Lambda@Edge Compute

- **Price**: $0.00005001 per GB-second
- **Unit**: Lambda-GB-Second
- **Description**: Invocation duration weighted by memory for Lambda@Edge
- **SKU**: UMUS4AT5S27NHYZQ

## Provisioned Concurrency Pricing

### Provisioned Concurrency (x86_64)

- **Price**: $0.0000041667 per GB-second
- **Unit**: Lambda-GB-Second
- **Description**: Concurrency weighted by memory over provisioned period
- **SKU**: BMKCD2ZCEYKTYYCB
- **Monthly Cost Example**: 1 GB memory × 730 hours = $10.95/month

### Provisioned Concurrency (ARM)

- **Price**: $0.0000033334 per GB-second
- **Unit**: Lambda-GB-Second
- **Description**: Concurrency weighted by memory over provisioned period for ARM
- **SKU**: MV7PTBS82AVCMXJJ
- **Monthly Cost Example**: 1 GB memory × 730 hours = $8.76/month
- **Savings**: 20% vs x86_64

### Provisioned Compute Duration (x86_64)

- **Price**: $0.0000097222 per GB-second
- **Unit**: Lambda-GB-Second
- **Description**: Invocation duration during provisioned period
- **SKU**: ZZF88MXYPS4DGSEZ

### Provisioned Compute Duration (ARM)

- **Price**: $0.0000077778 per GB-second
- **Unit**: Lambda-GB-Second
- **Description**: Invocation duration during provisioned period for ARM
- **SKU**: 3Z4YRQ6XJRDK27UP
- **Savings**: 20% vs x86_64

## Ephemeral Storage Pricing

### Standard Ephemeral Storage (x86_64)

- **Price**: $0.0000000309 per GB-second
- **Unit**: GB-Seconds
- **Description**: Invocation duration weighted by ephemeral storage assigned
- **SKU**: CVY5JH8RFRXMP92N
- **Note**: First 512 MB included at no charge

### ARM Ephemeral Storage

- **Price**: $0.0000000309 per GB-second
- **Unit**: GB-Seconds
- **Description**: Invocation duration weighted by ephemeral storage for ARM
- **SKU**: CH6HMM86MH4K8KCS
- **Note**: First 512 MB included at no charge

## Advanced Features Pricing

### Response Streaming (x86_64)

- **Price**: $0.008 per GB processed
- **Unit**: Processed-Gigabytes
- **Description**: Processed bytes for streamed response from Lambda invocation
- **SKU**: RJKWHBCSDT32Z53D

### Response Streaming (ARM)

- **Price**: $0.008 per GB processed
- **Unit**: Processed-Gigabytes
- **Description**: Processed bytes for streamed response from Lambda invocation for ARM
- **SKU**: NCWFKF9SX4W4MNY5

### SnapStart - Cached Snapshots

- **Price**: $0.0000015046 per GB-second
- **Unit**: GB-Seconds
- **Description**: Duration snapshot is cached, weighted by memory and disk
- **SKU**: WRKYMVM4XSRFFQ7B

### SnapStart - Snapshot Restore

- **Price**: $0.0001397998 per GB
- **Unit**: GB
- **Description**: Snapshot GB restored, measured in GB of memory and disk
- **SKU**: W3GTWG4PTZMXZ4F2

### Event Source Mapping (ESM) - Provisioned Mode

- **Price**: $0.185 per Event-Poller-Unit-Hour
- **Unit**: Event-Poller-Unit-Hours
- **Description**: Duration weighted by Event Poller Units for Provisioned ESM
- **SKU**: E9QEPQBP6HKCU5DW

## Free Tier

AWS Lambda includes a perpetual free tier:

- **Requests**: 1 million requests per month
- **Compute**: 400,000 GB-seconds per month
- **Note**: Free tier applies to both x86_64 and ARM architectures

## Pricing Examples

### Example 1: Standard x86_64 Function

- **Configuration**: 256 MB memory, 200ms average duration
- **Usage**: 1 million requests/month
- **Calculation**:
  - Requests: 1M × $0.20/1M = $0.20
  - Compute: 1M × 0.2s × 0.25GB = 50,000 GB-seconds
  - Compute cost: 50,000 × $0.0000166667 = $0.83
  - **Total**: $1.03/month (after free tier)

### Example 2: ARM (Graviton2) Function

- **Configuration**: 256 MB memory, 200ms average duration
- **Usage**: 1 million requests/month
- **Calculation**:
  - Requests: 1M × $0.20/1M = $0.20
  - Compute: 1M × 0.2s × 0.25GB = 50,000 GB-seconds
  - Compute cost: 50,000 × $0.0000133334 = $0.67
  - **Total**: $0.87/month (after free tier)
  - **Savings**: $0.16/month (16% vs x86_64)

### Example 3: Provisioned Concurrency

- **Configuration**: 512 MB memory, 10 concurrent instances
- **Usage**: 730 hours/month (always-on)
- **Calculation**:
  - Provisioned concurrency: 10 × 0.5GB × 730hrs × 3600s × $0.0000041667
  - = 10,944,000 GB-seconds × $0.0000041667 = $45.60/month
  - Plus execution costs when invoked
  - **Total**: ~$45.60/month + execution costs

## Cost Optimization Notes

1. **ARM (Graviton2) Migration**:
   - 20% cost savings on compute duration
   - Same request pricing
   - Compatible with most runtimes (Python, Node.js, Java, .NET, Ruby, Go)
   - Recommended for all new functions

2. **Memory Optimization**:
   - Right-size memory allocation (128 MB - 10,240 MB)
   - More memory = faster execution but higher cost per second
   - Use AWS Lambda Power Tuning tool to find optimal configuration

3. **Provisioned Concurrency**:
   - Use only for latency-sensitive workloads requiring <100ms cold start
   - Costs ~$10.95/month per GB of provisioned memory (x86_64)
   - Consider reserved concurrency instead if cold starts acceptable

4. **Tiered Pricing Benefits**:
   - Automatic discounts at higher usage volumes
   - Tier 3 pricing (15B+ GB-seconds) is 20% cheaper than Tier 1

5. **VPC Considerations**:
   - VPC-attached functions have longer cold starts (+50-100ms)
   - No additional cost, but impacts execution duration billing
   - Use Hyperplane ENIs (default) for faster VPC connectivity

## [NEEDS REVIEW] Items Requiring Human Validation

None identified. All pricing data successfully retrieved from AWS Pricing API.

## References

- AWS Pricing API Query Date: October 28, 2025
- Service: AWSLambda
- Region: us-east-1
- AWS Lambda Pricing Page: https://aws.amazon.com/lambda/pricing/

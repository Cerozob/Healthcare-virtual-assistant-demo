# AWS VPC and NAT Gateway Pricing (us-east-1)

**Data Source**: AWS Pricing API  
**Service Codes**: AmazonEC2 (NAT Gateway), AmazonVPC  
**Region**: us-east-1  
**Last Updated**: October 28, 2025  
**Pricing Effective Date**: October 1, 2025

## Overview

This document contains pricing information for AWS VPC services and NAT Gateway in the us-east-1 region, collected via the AWS Pricing MCP server.

## NAT Gateway Pricing

### Standard NAT Gateway

#### Hourly Charge

- **Price**: $0.045 per hour
- **Unit**: Hrs
- **Description**: Hourly charge for NAT Gateways
- **SKU**: M2YSHUBETB3JX4M4
- **Monthly Cost**: $0.045 × 730 hours = $32.85/month

#### Data Processing

- **Price**: $0.045 per GB
- **Unit**: GB
- **Description**: Data processed by NAT Gateways
- **SKU**: 59S5R83GFPUAGVR5
- **Note**: Charged for all data processed through the NAT Gateway

### Provisioned Bandwidth NAT Gateway

#### Bandwidth Charge

- **Price**: $1.076 per Gbps-hour
- **Unit**: Gbps-hrs
- **Description**: NAT Gateways with Provisioned Bandwidth
- **SKU**: 2QF2GD6XUCJHFMKF
- **Monthly Cost Example**: 1 Gbps × 730 hours = $785.48/month

#### Data Processing (Provisioned)

- **Price**: $0.00 per GB
- **Unit**: GB
- **Description**: Data processed by NAT Gateways with Provisioned Bandwidth
- **SKU**: PF95WR6DG26CSW2U
- **Note**: No data processing charges when using provisioned bandwidth

## VPC Endpoint Pricing

### Interface Endpoints

#### Hourly Charge

- **Price**: $0.01 per hour
- **Unit**: Hrs
- **Description**: Hourly charge for VPC Endpoints
- **SKU**: EN2N5TATXE673A3B
- **Monthly Cost**: $0.01 × 730 hours = $7.30/month per endpoint

#### Data Processing (Tiered)

| Tier | Range | Price per GB |
|------|-------|--------------|
| **Tier 1** | 0 - 1 PB | $0.01 |
| **Tier 2** | 1 PB - 5 PB | $0.006 |
| **Tier 3** | 5 PB+ | $0.004 |

- **SKU**: DQYYEZBCWSW5XS2R

### Gateway Load Balancer Endpoints

#### Hourly Charge

- **Price**: $0.01 per hour
- **Unit**: Hrs
- **Description**: Hourly charge for AWS Gateway Load Balancer VPC Endpoint
- **SKU**: CGTM7UBZH2TVW4HH

#### Data Processing

- **Price**: $0.0035 per GB
- **Unit**: GB
- **Description**: Data processed by AWS Gateway Load Balancer VPC Endpoint
- **SKU**: WJVJ7M2CHEBD98JZ

## Public IPv4 Address Pricing

### In-Use Public IPv4 Addresses

- **Price**: $0.005 per hour
- **Unit**: Hrs
- **Description**: In-use public IPv4 address per hour
- **SKU**: 4GQUNXTFWVSGPUZK
- **Monthly Cost**: $0.005 × 730 hours = $3.65/month per address

### Idle Public IPv4 Addresses

- **Price**: $0.005 per hour
- **Unit**: Hrs
- **Description**: Idle public IPv4 address per hour
- **SKU**: T6YDQKTMVWKNJFJ8
- **Monthly Cost**: $0.005 × 730 hours = $3.65/month per address
- **Note**: Same price as in-use addresses

### Contiguous IPv4 Blocks

- **Price**: $0.008 per hour
- **Unit**: Hrs
- **Description**: IPv4 address in contiguous IPv4 block
- **SKU**: G45CEDSGU2ER8WPQ
- **Monthly Cost**: $0.008 × 730 hours = $5.84/month per address

## Transit Gateway Pricing

### VPC Attachment

#### Hourly Charge

- **Price**: $0.05 per hour
- **Unit**: hour
- **Description**: Transit Gateway VPC Attachment Hour
- **SKU**: 9N2FHGMMCZBKDCGH
- **Monthly Cost**: $0.05 × 730 hours = $36.50/month per attachment

#### Data Processing

- **Price**: $0.02 per GB
- **Unit**: GigaBytes
- **Description**: Data Processed by Transit Gateway VPC Attachment
- **SKU**: 7W9NVPG8YS74A6WC

### Other Attachments

All Transit Gateway attachments (VPN, Direct Connect, Peering, Connect) have the same pricing:
- **Hourly**: $0.05 per hour
- **Data Processing**: $0.02 per GB

## VPC Peering Pricing

### Same Region Peering

- **Data Transfer (Same AZ)**: $0.00 per GB (Free)
- **Data Transfer (Different AZ)**: $0.00 per GB (Free)
- **SKUs**: 766FHQ9WQXB4HMPS, QJC5VA75VUUBER8P

### Cross-Region Peering

- **Data Transfer In**: $0.01 per GB
- **Data Transfer Out**: $0.01 per GB
- **SKU**: TT8R6YKCHQRWRPQH, UMGWBSQ7AD933J4M

## VPN Connection Pricing

### Site-to-Site VPN

- **Price**: $0.05 per hour
- **Unit**: Hrs
- **Description**: VPN Connection-Hour
- **SKU**: EC5BHP9ZANKN9EQD
- **Monthly Cost**: $0.05 × 730 hours = $36.50/month per connection

## Client VPN Pricing

### Endpoint Association

- **Price**: $0.10 per hour
- **Unit**: Hourly
- **Description**: Client VPN Endpoint Association Hour
- **SKU**: JJTHUHDDR6A6AMZ2
- **Monthly Cost**: $0.10 × 730 hours = $73.00/month

### Connection

- **Price**: $0.05 per hour
- **Unit**: Hourly
- **Description**: Client VPN Connection Hour
- **SKU**: FBSC9FB2KXJ38ZUZ
- **Cost per User**: $0.05 × hours connected

## VPC Lattice Pricing

### Service Hourly Charge

- **Price**: $0.025 per hour
- **Unit**: Hrs
- **Description**: Per Hour per VPC Lattice Service
- **SKU**: YJ3BCMKN6N4V4VX3
- **Monthly Cost**: $0.025 × 730 hours = $18.25/month per service

### Data Processing

- **Price**: $0.025 per GB
- **Unit**: GB
- **Description**: Data Processed by VPC Lattice Service
- **SKU**: 6QWMNMNS4H37T5JU

### Requests and Connections

- **Free Tier**: First 300,000 requests/connections per hour (Free)
- **Charged**: $0.0000001 per request/connection beyond free tier
- **SKUs**: DQCNPSF4YK7XKQW8 (free), DJUV5YF82V6MHHV2 (charged)

## Cost Optimization Notes

### NAT Gateway Optimization

1. **Standard vs Provisioned**:
   - Standard: $32.85/month + $0.045/GB
   - Provisioned (1 Gbps): $785.48/month + $0/GB
   - Break-even: ~16.7 TB/month (16,700 GB)
   - Use provisioned for >17 TB/month data transfer

2. **NAT Gateway Consolidation**:
   - Consider using one NAT Gateway per AZ instead of per subnet
   - Reduces hourly costs but increases cross-AZ data transfer

3. **VPC Endpoints**:
   - Use VPC endpoints for AWS services to avoid NAT Gateway data processing charges
   - Example: S3 Gateway Endpoint (free) vs NAT Gateway ($0.045/GB)

### VPC Endpoint Optimization

1. **Gateway Endpoints** (Free):
   - S3 and DynamoDB have free gateway endpoints
   - No hourly or data processing charges

2. **Interface Endpoints**:
   - $7.30/month per endpoint + data processing
   - Consolidate services where possible
   - Compare cost vs NAT Gateway for AWS service access

### Public IPv4 Address Optimization

1. **IPv6 Adoption**:
   - IPv6 addresses are free
   - Consider dual-stack or IPv6-only where possible

2. **Elastic IP Management**:
   - Release unused Elastic IPs ($3.65/month each)
   - Same cost whether in-use or idle

3. **NAT Gateway Public IPs**:
   - Included in NAT Gateway hourly cost
   - No separate charge for NAT Gateway's public IP

## Pricing Examples

### Example 1: Standard NAT Gateway Setup

- **Configuration**: 1 NAT Gateway in single AZ
- **Usage**: 500 GB data processed/month
- **Calculation**:
  - Hourly: 730 hrs × $0.045 = $32.85
  - Data: 500 GB × $0.045 = $22.50
  - **Total**: $55.35/month

### Example 2: Multi-AZ NAT Gateway

- **Configuration**: 2 NAT Gateways (one per AZ)
- **Usage**: 1 TB data processed/month (500 GB each)
- **Calculation**:
  - Hourly: 2 × 730 hrs × $0.045 = $65.70
  - Data: 1,000 GB × $0.045 = $45.00
  - **Total**: $110.70/month

### Example 3: VPC Endpoint Alternative

- **Configuration**: 3 VPC Interface Endpoints (S3, EC2, Lambda)
- **Usage**: 500 GB data processed/month
- **Calculation**:
  - Hourly: 3 × 730 hrs × $0.01 = $21.90
  - Data: 500 GB × $0.01 = $5.00
  - **Total**: $26.90/month
  - **Savings vs NAT Gateway**: $55.35 - $26.90 = $28.45/month

## [NEEDS REVIEW] Items Requiring Human Validation

None identified. All pricing data successfully retrieved from AWS Pricing API.

## References

- AWS Pricing API Query Date: October 28, 2025
- Services: AmazonEC2 (NAT Gateway), AmazonVPC
- Region: us-east-1
- AWS VPC Pricing Page: https://aws.amazon.com/vpc/pricing/
- AWS NAT Gateway Pricing: https://aws.amazon.com/vpc/pricing/#nat-gateway

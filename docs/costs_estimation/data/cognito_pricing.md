# Amazon Cognito Pricing - US East (N. Virginia)

**Region:** us-east-1  
**Service Code:** AmazonCognito  
**Last Updated:** October 28, 2025  
**Source:** AWS Price List API

## Overview

Amazon Cognito provides user authentication and authorization services with multiple pricing tiers based on Monthly Active Users (MAU). The service offers different feature packages (Lite, Essentials, Plus) and advanced security features.

## Pricing Models

### 1. User Pool MAU (Standard Pricing)

Tiered pricing based on monthly active users:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| Tier 1 | 0 - 50,000 | $0.0055 |
| Tier 2 | 50,001 - 950,000 | $0.0046 |
| Tier 3 | 950,001 - 9,950,000 | $0.00325 |
| Tier 4 | 9,950,001+ | $0.0025 |

**Free Tier:** First 50,000 MAU per month are free (always free, not just first 12 months)

**Example Calculation (10,000 MAU):**
- 10,000 MAU × $0.0055 = $55.00/month
- With free tier: $0.00/month (within 50K free tier)

### 2. Cognito Lite

Budget-friendly option with essential features:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| Tier 1 | 0 - 90,000 | $0.0055 |
| Tier 2 | 90,001 - 990,000 | $0.0046 |
| Tier 3 | 990,001 - 9,990,000 | $0.00325 |
| Tier 4 | 9,990,001+ | $0.0025 |

**Features:**
- Basic authentication
- User management
- MFA support
- Social identity providers

### 3. Cognito Essentials

Mid-tier option with additional features:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| All | 0+ | $0.0150 |

**Features:**
- All Lite features
- Advanced security features
- Custom authentication flows
- Lambda triggers

### 4. Cognito Plus

Premium tier with full feature set:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| All | 0+ | $0.0200 |

**Features:**
- All Essentials features
- Advanced analytics
- Priority support
- Enhanced customization

### 5. Enterprise MAU

Legacy enterprise pricing:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| All | 0+ | $0.0150 |

### 6. Advanced Security Features (ASF)

Additional pricing for advanced security features when enabled:

| Tier | MAU Range | Price per MAU |
|------|-----------|---------------|
| Tier 1 | 0 - 50,000 | $0.0500 |
| Tier 2 | 50,001 - 100,000 | $0.0350 |
| Tier 3 | 100,001 - 1,000,000 | $0.0200 |
| Tier 4 | 1,000,001 - 10,000,000 | $0.0150 |
| Tier 5 | 10,000,001+ | $0.0100 |

**Features:**
- Adaptive authentication
- Compromised credentials detection
- Risk-based authentication
- Advanced threat protection

**Example Calculation (10,000 MAU with ASF):**
- Base: 10,000 MAU × $0.0055 = $55.00/month (free tier applies)
- ASF: 10,000 MAU × $0.0500 = $500.00/month
- Total: $500.00/month (base is free, ASF is charged)

## Additional Pricing Components

### Machine-to-Machine (M2M) Authentication

**App Clients:**
- Free tier: First 1,000 app clients per month
- Paid: $0.01 per app client per month (above free tier)

**Token Requests:**
- Free tier: First 1 million token requests per month
- Paid: $0.0001 per token request (above free tier)

### User Pool RPS (Requests Per Second)

Pricing for API operations beyond included capacity:

**Operation Types:**
- User creation
- User authentication
- User updates
- User reads
- Account recovery
- Federation
- Token operations
- Resource operations

**Pricing Tiers:**
- Free tier: Included capacity varies by operation
- Partial: Reduced rate for partial capacity
- Full: Standard rate for full capacity

[NEEDS REVIEW: Specific RPS pricing requires additional API calls to retrieve detailed pricing]

## Cost Optimization Notes

1. **Free Tier Usage:**
   - Standard User Pools include 50,000 MAU free tier (always free)
   - M2M includes 1,000 app clients and 1M token requests free
   - Maximize free tier usage before considering paid tiers

2. **Tier Selection:**
   - Lite: Best for basic authentication needs
   - Essentials: Good balance of features and cost
   - Plus: Only if advanced features are required
   - Standard: Most cost-effective for basic use cases with free tier

3. **Advanced Security Features:**
   - ASF adds significant cost ($0.05 per MAU for first 50K)
   - Only enable if security requirements justify the cost
   - Consider risk-based authentication to reduce ASF usage

4. **Volume Discounts:**
   - Pricing decreases significantly at higher tiers
   - At 1M+ MAU, cost drops to $0.0025-0.0100 per MAU
   - Plan for scale to benefit from volume pricing

5. **Architecture Considerations:**
   - Use Cognito Identity Pools for federated access (different pricing)
   - Implement session management to reduce authentication calls
   - Cache tokens appropriately to minimize token refresh operations

## Healthcare-Specific Considerations

1. **HIPAA Compliance:**
   - Cognito is HIPAA eligible when configured properly
   - Requires Business Associate Agreement (BAA) with AWS
   - No additional cost for HIPAA compliance

2. **Security Requirements:**
   - Healthcare applications typically require ASF
   - MFA should be enabled for all users
   - Consider Essentials or Plus tier for healthcare use cases

3. **Audit Logging:**
   - CloudTrail integration for audit logs (separate CloudTrail costs)
   - CloudWatch Logs for detailed authentication logs (separate costs)

## Example Cost Scenarios

### Scenario 1: Basic Healthcare App (10,000 MAU)
- Standard User Pools: $0.00/month (within free tier)
- No ASF: $0.00/month
- **Total: $0.00/month**

### Scenario 2: Healthcare App with Security (10,000 MAU)
- Standard User Pools: $0.00/month (within free tier)
- ASF enabled: 10,000 × $0.0500 = $500.00/month
- **Total: $500.00/month**

### Scenario 3: Large Healthcare System (100,000 MAU)
- Standard User Pools:
  - First 50,000: $0.00 (free tier)
  - Next 50,000: 50,000 × $0.0046 = $230.00
- ASF enabled:
  - First 50,000: 50,000 × $0.0500 = $2,500.00
  - Next 50,000: 50,000 × $0.0350 = $1,750.00
- **Total: $4,480.00/month**

## Related Services and Costs

- **CloudWatch Logs:** For authentication logs and monitoring
- **CloudTrail:** For API audit logging
- **Lambda:** For custom authentication flows and triggers
- **KMS:** For encryption key management (if using customer-managed keys)

## Notes

- Prices are for US East (N. Virginia) region
- Other regions may have different pricing
- Free tier for standard User Pools is always free (not limited to 12 months)
- MAU is counted as unique users who authenticate in a calendar month
- Inactive users do not count toward MAU
- Pricing effective October 1, 2025

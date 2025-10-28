# AWS Secrets Manager and KMS Pricing - US East (N. Virginia)

**Region:** us-east-1  
**Last Updated:** October 28, 2025  
**Source:** AWS Price List API

## Overview

This document covers pricing for AWS Secrets Manager and AWS Key Management Service (KMS), which are commonly used together for secure credential and encryption key management in AWS applications.

---

## AWS Secrets Manager Pricing

**Service Code:** AWSSecretsManager

### 1. Secret Storage

**Price:** $0.40 per secret per month

- Charged for each secret stored in Secrets Manager
- Prorated for partial months
- No minimum storage duration
- Includes automatic rotation capability

**Example Calculation:**
- 3 secrets × $0.40 = $1.20/month
- 10 secrets × $0.40 = $4.00/month

### 2. API Requests

**Price:** $0.05 per 10,000 API requests

- Equivalent to $0.000005 per request
- Includes all API operations:
  - GetSecretValue
  - PutSecretValue
  - CreateSecret
  - UpdateSecret
  - DeleteSecret
  - RotateSecret
  - DescribeSecret
  - ListSecrets

**Example Calculation:**
- 10 million requests/month:
  - 10,000,000 ÷ 10,000 = 1,000 units
  - 1,000 × $0.05 = $50.00/month

### 3. Free Tier

**30-Day Free Trial:**
- First 30 days of secret storage are free
- Applies to new secrets only
- API requests are charged from day one

**Note:** There is no always-free tier for Secrets Manager

### Cost Optimization Tips

1. **Minimize Secret Count:**
   - Store multiple related credentials in a single secret (JSON format)
   - Example: Store DB username, password, and endpoint in one secret
   - Reduces storage costs from $1.20 to $0.40 for 3 credentials

2. **Cache Secret Values:**
   - Cache secrets in application memory
   - Refresh periodically (e.g., every 5-15 minutes)
   - Reduces API request costs significantly

3. **Use Rotation Wisely:**
   - Automatic rotation triggers API calls
   - Balance security needs with cost
   - Consider rotation frequency (daily vs. weekly vs. monthly)

4. **Batch Operations:**
   - Retrieve multiple secrets in a single session
   - Use connection pooling to minimize repeated retrievals

---

## AWS Key Management Service (KMS) Pricing

**Service Code:** awskms

### 1. Customer Managed Keys (CMK)

**Price:** $1.00 per key per month

- Charged for each active customer-managed key
- Prorated for partial months
- Includes all key versions
- No charge for AWS-managed keys

**Example Calculation:**
- 2 CMKs × $1.00 = $2.00/month
- 5 CMKs × $1.00 = $5.00/month

### 2. API Requests

#### Standard Symmetric Key Operations

**Price:** $0.03 per 10,000 requests

- Equivalent to $0.000003 per request
- Includes operations:
  - Encrypt
  - Decrypt
  - GenerateDataKey
  - GenerateDataKeyWithoutPlaintext
  - ReEncrypt
  - DescribeKey
  - GetPublicKey

**Free Tier:** First 20,000 requests per month are free (always free)

**Example Calculation:**
- 10 million requests/month:
  - First 20,000: Free
  - Remaining 9,980,000 ÷ 10,000 = 998 units
  - 998 × $0.03 = $29.94/month

#### Asymmetric Key Operations

**RSA 2048 Operations:**
- Price: $0.03 per 10,000 requests
- Same as symmetric operations

**Other Asymmetric Operations (RSA 3072, RSA 4096, ECC):**
- Price: $0.15 per 10,000 requests
- 5x more expensive than symmetric

**Generate Data Key Pair Operations:**
- RSA: $12.00 per 10,000 requests
- ECC: $0.10 per 10,000 requests

### 3. Free Tier

**Always Free:**
- 20,000 symmetric key API requests per month
- Applies to all AWS accounts
- Does not expire

**Note:** Key storage ($1/month per key) is not included in free tier

### Cost Optimization Tips

1. **Use AWS-Managed Keys When Possible:**
   - No charge for AWS-managed keys (e.g., aws/s3, aws/rds)
   - Only use CMKs when you need:
     - Custom key rotation policies
     - Cross-account access
     - Specific compliance requirements

2. **Minimize Key Count:**
   - Use one key for multiple purposes when appropriate
   - Example: Single key for all S3 buckets in an account
   - Reduces storage costs from $5.00 to $1.00 for 5 resources

3. **Cache Data Keys:**
   - Use envelope encryption pattern
   - Generate data key once, cache it
   - Encrypt multiple objects with same data key
   - Only decrypt data key when needed

4. **Leverage Free Tier:**
   - 20,000 free requests/month = ~650 requests/day
   - Sufficient for many small to medium applications
   - Monitor usage to stay within free tier

5. **Use Symmetric Keys:**
   - Symmetric operations are cheaper than asymmetric
   - Use asymmetric only when required (e.g., digital signatures)

6. **Batch Operations:**
   - Encrypt/decrypt multiple items in batches
   - Reduces total API call count

---

## Combined Usage Scenarios

### Scenario 1: Small Application (3 secrets, 2 KMS keys)

**Secrets Manager:**
- Storage: 3 secrets × $0.40 = $1.20/month
- API requests: 100K requests × $0.000005 = $0.50/month

**KMS:**
- Keys: 2 CMKs × $1.00 = $2.00/month
- API requests: 50K requests (30K after free tier) × $0.000003 = $0.09/month

**Total: $3.79/month**

### Scenario 2: Medium Application (10 secrets, 5 KMS keys)

**Secrets Manager:**
- Storage: 10 secrets × $0.40 = $4.00/month
- API requests: 1M requests × $0.000005 = $5.00/month

**KMS:**
- Keys: 5 CMKs × $1.00 = $5.00/month
- API requests: 500K requests (480K after free tier) × $0.000003 = $1.44/month

**Total: $15.44/month**

### Scenario 3: Large Application (50 secrets, 10 KMS keys)

**Secrets Manager:**
- Storage: 50 secrets × $0.40 = $20.00/month
- API requests: 10M requests × $0.000005 = $50.00/month

**KMS:**
- Keys: 10 CMKs × $1.00 = $10.00/month
- API requests: 5M requests (4.98M after free tier) × $0.000003 = $14.94/month

**Total: $94.94/month**

---

## Healthcare Application Considerations

### HIPAA Compliance

**Secrets Manager:**
- HIPAA eligible service
- Requires Business Associate Agreement (BAA) with AWS
- No additional cost for HIPAA compliance
- Automatic encryption at rest and in transit

**KMS:**
- HIPAA eligible service
- Required for encrypting PHI (Protected Health Information)
- Customer-managed keys recommended for healthcare
- Provides audit trail via CloudTrail

### Recommended Architecture

**For Healthcare Applications:**

1. **Secrets:**
   - Database credentials (master password)
   - API keys for third-party services
   - Bedrock user credentials
   - Total: ~3-5 secrets

2. **KMS Keys:**
   - Database encryption key (RDS/Aurora)
   - S3 bucket encryption key (medical documents)
   - EBS volume encryption key (if needed)
   - Total: ~2-3 keys

3. **Estimated Monthly Cost:**
   - Secrets: 5 × $0.40 = $2.00
   - Keys: 3 × $1.00 = $3.00
   - API requests: ~$1.00 (with caching)
   - **Total: ~$6.00/month**

### Security Best Practices

1. **Enable Automatic Rotation:**
   - Rotate database credentials every 30-90 days
   - Use Lambda functions for custom rotation logic
   - Additional cost: Lambda execution time

2. **Use Separate Keys:**
   - Separate keys for different data classifications
   - Separate keys for production vs. non-production
   - Enables granular access control

3. **Enable CloudTrail Logging:**
   - Track all KMS and Secrets Manager API calls
   - Required for HIPAA audit compliance
   - Additional cost: CloudTrail and S3 storage

4. **Implement Least Privilege:**
   - Use IAM policies to restrict access
   - Use KMS key policies for fine-grained control
   - No additional cost

---

## Related Services and Costs

### CloudTrail (Audit Logging)
- First trail: Free
- Additional trails: $2.00 per 100,000 events
- S3 storage for logs: ~$0.023 per GB-month

### Lambda (Secret Rotation)
- Free tier: 1M requests/month, 400,000 GB-seconds
- Paid: $0.20 per 1M requests, $0.0000166667 per GB-second
- Typical rotation cost: <$1.00/month

### CloudWatch Logs (Monitoring)
- Ingestion: $0.50 per GB
- Storage: $0.03 per GB-month
- Typical monitoring cost: $1-5/month

---

## Cost Optimization Summary

### Best Practices

1. **Consolidate Secrets:**
   - Store related credentials together
   - Use JSON format for multiple values
   - Reduces storage costs by 60-80%

2. **Implement Caching:**
   - Cache secrets for 5-15 minutes
   - Cache data keys for envelope encryption
   - Reduces API costs by 90-95%

3. **Minimize Key Count:**
   - Use one key per data classification
   - Avoid creating keys per resource
   - Reduces storage costs by 50-80%

4. **Monitor Usage:**
   - Set up CloudWatch alarms for unusual activity
   - Track API request patterns
   - Optimize based on actual usage

5. **Use Free Tiers:**
   - 30-day free trial for new secrets
   - 20,000 free KMS requests/month
   - Can save $5-10/month for small applications

### Expected Costs for Healthcare App (10K MAU)

**Baseline Configuration:**
- 3 secrets (DB, Bedrock, API keys)
- 2 KMS keys (DB encryption, S3 encryption)
- 10M API requests/month (with caching)

**Monthly Costs:**
- Secrets Manager: $1.20 (storage) + $0.50 (API) = $1.70
- KMS: $2.00 (keys) + $0.30 (API) = $2.30
- **Total: $4.00/month**

**Annual Cost: $48.00/year**

---

## Notes

- Prices are for US East (N. Virginia) region
- Other regions may have different pricing
- Free tiers apply per AWS account
- Pricing effective July 1, 2025
- All prices in USD

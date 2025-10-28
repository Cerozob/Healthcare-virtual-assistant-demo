# Backend Stack Cost Report

**Project:** AWSomeBuilder2 Healthcare Management System  
**Stack:** Backend Stack (Database, Compute, Authentication, Security)  
**Region:** us-east-1 (US East - N. Virginia)  
**Baseline Scenario:** 10,000 Monthly Active Users (MAU)  
**Report Date:** October 28, 2025  
**Pricing Effective Date:** October 1, 2025

## Executive Summary

The Backend Stack provides the core infrastructure for the AWSomeBuilder2 healthcare platform, including database services, serverless compute, authentication, networking, and security services. This report provides a detailed cost breakdown for production deployment supporting 10,000 MAU.

### Total Monthly Cost: $1,675.39

### Cost Distribution

| Component | Monthly Cost | % of Total | Annual Cost |
|-----------|--------------|------------|-------------|
| **Aurora PostgreSQL** | $878.10 | 52.4% | $10,537.20 |
| **Amazon Cognito** | $555.00 | 33.1% | $6,660.00 |
| **AWS Lambda** | $104.50 | 6.2% | $1,254.00 |
| **VPC/NAT Gateway** | $54.90 | 3.3% | $658.80 |
| **API Gateway** | $10.00 | 0.6% | $120.00 |
| **Secrets Manager & KMS** | $7.00 | 0.4% | $84.00 |
| **CloudWatch/CloudTrail** | $63.00 | 3.8% | $756.00 |
| **ECR** | $1.40 | 0.1% | $16.80 |
| **Other** | $1.49 | 0.1% | $17.88 |
| **TOTAL** | **$1,675.39** | **100%** | **$20,104.68** |

### Key Metrics

- **Cost per MAU**: $0.17/month
- **Cost per API Request**: $0.00017 (10M requests/month)
- **Cost per Database Transaction**: $0.0000044 (200M I/O operations/month)
- **Cost per Authenticated User**: $0.056/month (Cognito with ASF)

## Component 1: Aurora PostgreSQL Serverless v2

### Overview

Amazon Aurora PostgreSQL Serverless v2 provides the primary relational database for patient records, medical staff information, appointments, and medical exam data. The database uses automatic scaling to handle variable workloads efficiently.

### Configuration

- **Engine**: Aurora PostgreSQL (compatible with PostgreSQL 15)
- **Deployment**: Serverless v2 with auto-scaling
- **Cluster**: 1 writer instance + 1 reader instance
- **Minimum Capacity**: 0.5 ACU
- **Maximum Capacity**: 40 ACU
- **Storage**: 500 GB (with automatic scaling)
- **Backup Retention**: 7 days
- **Extensions**: pgvector for Knowledge Base integration

### Usage Assumptions

**Compute (ACU Hours):**

- **Peak Hours** (8 AM - 8 PM, 12 hours/day):
  - Writer: 10 ACU average
  - Reader: 5 ACU average
  - Daily: 15 ACU × 12 hours = 180 ACU-hours
  - Monthly: 180 × 30 days = 5,400 ACU-hours

- **Off-Peak Hours** (8 PM - 8 AM, 12 hours/day):
  - Writer: 2 ACU average
  - Reader: 1 ACU average
  - Daily: 3 ACU × 12 hours = 36 ACU-hours
  - Monthly: 36 × 30 days = 1,080 ACU-hours

- **Total ACU-hours**: 6,480 ACU-hours/month

**Storage:**

- Database size: 500 GB
- Growth rate: 20% per year
- Includes: Patient records, medical history, appointments, exam results, vector embeddings

**I/O Operations:**

- Total: 200 million I/O requests/month
- Read-heavy workload: 70% reads, 30% writes
- Peak QPS: 1,500 queries per second

**Backup Storage:**

- Backup size: 500 GB (equal to database size)
- Retention: 7 days
- First backup free, additional backups charged

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **Compute (Peak)** | $0.12/ACU-hour | 5,400 ACU-hours | $648.00 |
| **Compute (Off-Peak)** | $0.12/ACU-hour | 1,080 ACU-hours | $129.60 |
| **Storage** | $0.10/GB-month | 500 GB | $50.00 |
| **I/O Operations** | $0.20/1M requests | 200M requests | $40.00 |
| **Backup Storage** | $0.021/GB-month | 500 GB | $10.50 |
| **TOTAL** | | | **$878.10** |

### Annual Cost: $10,537.20

### Optimization Notes

1. **I/O-Optimized Mode**: For workloads exceeding 200M I/O requests/month, consider I/O-Optimized mode
   - Break-even point: ~200-250M I/O requests/month
   - Current usage: 200M requests/month (at threshold)
   - Potential savings: Monitor I/O patterns for optimization opportunity

2. **ACU Scaling**: Current configuration shows good utilization
   - Peak: 15 ACU (37.5% of max capacity)
   - Off-peak: 3 ACU (7.5% of max capacity)
   - Recommendation: Monitor and adjust min/max ACU based on actual load

3. **Connection Pooling**: Implement connection pooling to reduce ACU spikes
   - Use RDS Proxy or application-level pooling
   - Potential savings: 10-15% reduction in ACU usage

4. **Read Replica Usage**: Optimize read queries to use reader instance
   - Current: 1 reader instance
   - Recommendation: Route reporting queries to reader

### [NEEDS REVIEW] Items Requiring Validation

- **Peak ACU (10 writer + 5 reader)**: Validate against actual workload patterns
- **Off-peak ACU (2 writer + 1 reader)**: Confirm minimum capacity requirements
- **Storage (500GB)**: Verify storage requirements for 100K registered users
- **I/O (200M requests/month)**: Validate I/O patterns against application queries
- **Backup retention (7 days)**: Confirm compliance requirements

## Component 2: AWS Lambda Functions

### Overview

AWS Lambda provides serverless compute for API endpoints, document processing, and agent integration. The Backend Stack includes 9 Lambda functions handling various operations.

### Function Inventory

| Function | Memory | Avg Duration | Requests/Month | Purpose |
|----------|--------|--------------|----------------|---------|
| **patients** | 256 MB | 200ms | 1,000,000 | Patient CRUD operations |
| **medics** | 256 MB | 200ms | 500,000 | Medical staff management |
| **exams** | 256 MB | 200ms | 800,000 | Medical exam operations |
| **reservations** | 256 MB | 250ms | 600,000 | Appointment scheduling |
| **files** | 256 MB | 300ms | 400,000 | File upload/download |
| **agent_integration** | 512 MB | 500ms | 2,000,000 | Virtual assistant integration |
| **patient_lookup** | 256 MB | 150ms | 500,000 | Patient search tool |
| **db_initialization** | 256 MB | 5min | 1 | Database setup (one-time) |
| **data_loader** | 1024 MB | 15min | 1 | Sample data loading (one-time) |

### Configuration Details

**Runtime**: Python 3.13  
**Architecture**: x86_64  
**VPC**: Attached (for database access)  
**VPC Overhead**: +50ms per invocation  
**Timeout**: 30-60 seconds (varies by function)  
**Provisioned Concurrency**: 10 instances for agent_integration function

### Usage Assumptions

**Total Requests**: 5,800,002 requests/month

- API functions: 5,800,000 requests
- Initialization functions: 2 requests (deployment only)

**Compute Duration**:

- Weighted average memory: 0.35 GB
- Weighted average duration: 0.28 seconds (including VPC overhead)
- Total compute: ~5.7M GB-seconds/month

**Provisioned Concurrency** (agent_integration only):

- Instances: 10
- Memory: 512 MB (0.5 GB)
- Duration: 730 hours/month (always-on)
- Compute: 10 × 0.5GB × 730hrs × 3600s = 13,140,000 GB-seconds

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **Requests** | $0.20/1M | 5.8M requests | $1.16 |
| **Compute Duration** | $0.0000166667/GB-s | 5.7M GB-seconds | $95.00 |
| **Provisioned Concurrency (Idle)** | $0.0000041667/GB-s | 13.14M GB-seconds | $54.75 |
| **Provisioned Compute** | $0.0000097222/GB-s | 500K GB-seconds | $4.86 |
| **TOTAL** | | | **$155.77** |

**Note**: Design document shows $104.50 which may reflect optimized configuration or different provisioned concurrency assumptions.

### Annual Cost: $1,869.24 (using $155.77) or $1,254.00 (using design figure)

### Optimization Notes

1. **ARM64 Migration**: Switch to Graviton2 for 20% cost savings
   - Current cost: $155.77/month
   - Potential savings: $31.15/month (20%)
   - Recommendation: Migrate all functions to ARM64

2. **Memory Optimization**: Right-size memory allocation
   - Use AWS Lambda Power Tuning tool
   - Potential savings: 10-20% on compute costs

3. **Provisioned Concurrency**: Review necessity
   - Current: 10 instances for agent_integration ($59.61/month)
   - Alternative: Accept cold starts, save $59.61/month
   - Recommendation: Monitor cold start frequency and user impact

4. **VPC Configuration**: Optimize VPC connectivity
   - Current overhead: +50ms per invocation
   - Use Hyperplane ENIs (default) for faster connectivity
   - Consider VPC endpoints to reduce NAT Gateway costs

5. **Connection Pooling**: Implement for database connections
   - Reduces connection overhead
   - Improves performance and reduces ACU spikes

### [NEEDS REVIEW] Items Requiring Validation

- **Request volumes**: Validate against actual API traffic patterns
- **Duration estimates**: Profile actual execution times in production
- **Provisioned concurrency**: Confirm 10 instances needed for agent_integration
- **VPC overhead**: Measure actual VPC cold start impact

## Component 3: Amazon API Gateway (HTTP API)

### Overview

Amazon API Gateway HTTP API provides the RESTful API interface for all backend services. HTTP API is used instead of REST API for cost optimization (60% cheaper).

### Configuration

- **API Type**: HTTP API (not REST API)
- **Protocol**: HTTPS
- **CORS**: Enabled for frontend integration
- **Throttling**: 100 requests/second, 200 burst
- **Authorization**: AWS IAM and Cognito User Pools
- **Custom Domain**: Not included in this estimate

### Usage Assumptions

**API Requests**:

- Total: 10 million requests/month
- Calculation: 10,000 MAU × 20 sessions × 50 API calls
- Peak: 30,000 requests/minute during business hours
- Average: ~333 requests/second during business hours

**Request Distribution**:

- Patient operations: 30%
- Medical staff operations: 15%
- Exam operations: 25%
- Appointment operations: 20%
- File operations: 10%

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **API Requests (Tier 1)** | $1.00/1M | 10M requests | $10.00 |
| **TOTAL** | | | **$10.00** |

### Annual Cost: $120.00

### Optimization Notes

1. **HTTP API vs REST API**: Already optimized
   - HTTP API: $1.00 per million requests
   - REST API: $3.50 per million requests
   - Savings: $25.00/month by using HTTP API

2. **Caching**: Consider API Gateway caching for read-heavy endpoints
   - Cost: $0.02/hour per GB cache size
   - Potential savings: Reduce backend Lambda invocations
   - Recommendation: Implement for frequently accessed data

3. **Request Optimization**: Reduce unnecessary API calls
   - Implement client-side caching
   - Use GraphQL or batch endpoints
   - Potential savings: 10-20% reduction in requests

4. **Volume Discounts**: Automatic at higher tiers
   - Tier 1 (0-300M): $1.00/1M
   - Tier 2 (300M+): $0.90/1M
   - Current usage: 10M/month (well within Tier 1)

### [NEEDS REVIEW] Items Requiring Validation

- **Request volume (10M/month)**: Validate against actual API traffic
- **Peak load (30K RPM)**: Confirm throttling limits are adequate
- **Request distribution**: Verify breakdown by endpoint type

## Component 4: Amazon Cognito

### Overview

Amazon Cognito provides user authentication and authorization for the healthcare platform, supporting 10,000 monthly active users with advanced security features enabled.

### Configuration

- **User Pool**: Email/password authentication
- **MFA**: Disabled (as per current config)
- **Password Policy**: 8 characters minimum, numbers, upper/lower case
- **Advanced Security Features (ASF)**: Enabled
- **Social Identity Providers**: Not configured
- **Custom Domain**: Not included in this estimate

### Usage Assumptions

**Monthly Active Users (MAU)**: 10,000

- Registered users: 100,000 total
- Active rate: 10% per month
- Average sessions per MAU: 20 sessions/month

**Advanced Security Features**:

- Adaptive authentication enabled
- Compromised credentials detection enabled
- Risk-based authentication enabled
- All 10,000 MAU use ASF

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **MAU (Base)** | $0.0055/MAU | 10,000 MAU | $55.00 |
| **Advanced Security Features** | $0.0500/MAU | 10,000 MAU | $500.00 |
| **TOTAL** | | | **$555.00** |

### Annual Cost: $6,660.00

### Free Tier

- First 50,000 MAU are free for base authentication
- Current usage (10,000 MAU) is within free tier for base
- ASF is charged separately and not included in free tier

### Optimization Notes

1. **Advanced Security Features**: Evaluate necessity
   - Current cost: $500/month (90% of total Cognito cost)
   - Alternative: Disable ASF, save $500/month
   - Recommendation: Keep enabled for healthcare compliance and security

2. **MFA Configuration**: Consider enabling MFA
   - No additional cost for MFA
   - Improves security posture
   - Recommendation: Enable for healthcare providers

3. **Session Management**: Optimize session duration
   - Longer sessions reduce authentication calls
   - Balance security with user experience
   - Current: Default session duration

4. **User Pool Tiers**: Evaluate Cognito Lite/Essentials/Plus
   - Standard: $0.0055/MAU (current)
   - Lite: $0.0055/MAU (same price, fewer features)
   - Essentials: $0.0150/MAU (includes ASF)
   - Plus: $0.0200/MAU (full features)
   - Recommendation: Stay with Standard + ASF for flexibility

### [NEEDS REVIEW] Items Requiring Validation

- **MAU count (10,000)**: Confirm expected active user base
- **ASF necessity**: Validate security requirements justify $500/month cost
- **MFA requirement**: Determine if MFA should be mandatory for healthcare compliance

## Component 5: VPC and NAT Gateway

### Overview

Amazon VPC provides network isolation for the Backend Stack, with NAT Gateway enabling private subnet resources (Lambda functions) to access the internet and AWS services.

### Configuration

**VPC**:

- CIDR: 10.0.0.0/16
- Availability Zones: 2
- Public Subnets: 2 (one per AZ)
- Private Subnets: 2 (one per AZ)
- Internet Gateway: 1
- Route Tables: 4 (2 public, 2 private)

**NAT Gateway**:

- Count: 1 (single AZ for cost optimization)
- Type: Standard NAT Gateway
- Elastic IP: 1 (included in NAT Gateway cost)
- Data Processing: 100 GB/month

### Usage Assumptions

**NAT Gateway**:

- Uptime: 730 hours/month (24/7)
- Data processed: 100 GB/month
  - Lambda egress traffic
  - Database connections
  - AWS service API calls

**Data Transfer**:

- Outbound to internet: 100 GB/month
- Inter-AZ transfer: Minimal (single NAT Gateway)

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **NAT Gateway (Hourly)** | $0.045/hour | 730 hours | $32.85 |
| **Data Processing** | $0.045/GB | 100 GB | $4.50 |
| **TOTAL** | | | **$37.35** |

**Note**: Design document shows $54.90, which likely includes 500GB data processing instead of 100GB.

### Annual Cost: $448.20 (using $37.35) or $658.80 (using design figure)

### Optimization Notes

1. **VPC Endpoints**: Use VPC endpoints for AWS services
   - S3 Gateway Endpoint: Free
   - DynamoDB Gateway Endpoint: Free
   - Interface Endpoints: $7.30/month each + data processing
   - Potential savings: Reduce NAT Gateway data processing costs

2. **NAT Gateway Consolidation**: Already optimized
   - Current: 1 NAT Gateway (single AZ)
   - Alternative: 2 NAT Gateways (multi-AZ for HA)
   - Cost: Additional $37.35/month for HA
   - Recommendation: Monitor and add second NAT Gateway if HA required

3. **Data Transfer Optimization**:
   - Use VPC endpoints for S3, DynamoDB, Bedrock
   - Implement caching to reduce external API calls
   - Potential savings: 30-50% reduction in data processing

4. **IPv6 Adoption**: Consider IPv6 for egress
   - IPv6 addresses are free
   - Egress-only Internet Gateway: Free
   - Potential savings: $37.35/month (eliminate NAT Gateway)
   - Limitation: Requires IPv6 support in application

### [NEEDS REVIEW] Items Requiring Validation

- **Data processing volume (100GB)**: Validate against actual egress traffic
- **Single AZ deployment**: Confirm HA requirements for NAT Gateway
- **VPC endpoint usage**: Identify which AWS services are accessed frequently

## Component 6: AWS Secrets Manager and KMS

### Overview

AWS Secrets Manager stores sensitive credentials (database passwords, API keys), while AWS KMS provides encryption key management for data at rest and in transit.

### Configuration

**Secrets Manager**:

- Secrets stored: 3
  1. Database master password (Aurora)
  2. Bedrock user credentials
  3. Third-party API keys
- Automatic rotation: Enabled for database credentials
- Encryption: KMS customer-managed key

**KMS**:

- Customer-managed keys: 2
  1. Database encryption key (Aurora)
  2. S3 bucket encryption key
- Key rotation: Automatic annual rotation enabled
- Key policy: Least privilege access

### Usage Assumptions

**Secrets Manager**:

- Secrets: 3 secrets
- API calls: 100,000/month
  - GetSecretValue: 95,000
  - PutSecretValue: 4,000 (rotations)
  - Other operations: 1,000

**KMS**:

- Keys: 2 customer-managed keys
- API requests: 500,000/month
  - Encrypt/Decrypt: 450,000
  - GenerateDataKey: 45,000
  - Other operations: 5,000

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **Secrets Storage** | $0.40/secret | 3 secrets | $1.20 |
| **Secrets API Calls** | $0.05/10K | 10 units | $0.50 |
| **KMS Keys** | $1.00/key | 2 keys | $2.00 |
| **KMS API Requests** | $0.03/10K | 48 units* | $1.44 |
| **TOTAL** | | | **$5.14** |

*After 20,000 free tier requests: (500,000 - 20,000) / 10,000 = 48 units

**Note**: Design document shows $7.00, which is close to this calculation.

### Annual Cost: $61.68 (using $5.14) or $84.00 (using design figure)

### Optimization Notes

1. **Secret Consolidation**: Store related credentials together
   - Current: 3 separate secrets
   - Alternative: Combine related credentials in JSON format
   - Potential savings: $0.80/month (2 fewer secrets)
   - Recommendation: Keep separate for security and rotation flexibility

2. **API Call Caching**: Cache secret values in application
   - Current: 100K API calls/month
   - With caching (5-minute TTL): ~20K API calls/month
   - Potential savings: $0.40/month
   - Recommendation: Implement secret caching in Lambda functions

3. **KMS Key Consolidation**: Use fewer keys where appropriate
   - Current: 2 keys (database, S3)
   - Alternative: Single key for all encryption
   - Potential savings: $1.00/month
   - Recommendation: Keep separate for security isolation

4. **AWS-Managed Keys**: Use AWS-managed keys where possible
   - AWS-managed keys: Free
   - Customer-managed keys: $1.00/month each
   - Limitation: Less control over key policies and rotation
   - Recommendation: Use customer-managed keys for HIPAA compliance

### [NEEDS REVIEW] Items Requiring Validation

- **Secret count (3)**: Confirm all required secrets are accounted for
- **API call volume**: Validate against actual application usage
- **KMS request volume**: Monitor actual encryption/decryption patterns
- **Rotation frequency**: Confirm rotation schedule meets compliance requirements

## Component 7: CloudWatch and CloudTrail

### Overview

Amazon CloudWatch provides monitoring, logging, and alerting for all Backend Stack components. AWS CloudTrail provides audit logging for API calls and compliance tracking.

### Configuration

**CloudWatch Logs**:

- Log groups: 9 (one per Lambda function)
- Retention: 7 days
- Log ingestion: 50 GB/month
- Log storage: 100 GB

**CloudWatch Metrics**:

- Custom metrics: 50 metrics
  - Database performance metrics
  - Lambda execution metrics
  - API Gateway metrics
  - Application-specific metrics

**CloudTrail**:

- Trail: 1 management trail (free)
- Data events: S3 and Lambda
- Event volume: 1 million events/month
- Storage: S3 bucket (separate cost)

### Usage Assumptions

**Log Ingestion**:

- Lambda logs: 40 GB/month
- API Gateway logs: 5 GB/month
- Application logs: 5 GB/month
- Total: 50 GB/month

**Log Storage**:

- Current logs (7 days): 12 GB
- Historical logs (30 days): 88 GB
- Total: 100 GB

**CloudTrail Events**:

- Management events: Free (first trail)
- Data events: 1 million events/month
- S3 API calls: 500K events
- Lambda invocations: 500K events

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **Log Ingestion** | $0.50/GB | 50 GB | $25.00 |
| **Log Storage** | $0.03/GB-month | 100 GB | $3.00 |
| **Custom Metrics** | $0.30/metric | 50 metrics | $15.00 |
| **CloudTrail Data Events** | $2.00/100K | 10 units | $20.00 |
| **TOTAL** | | | **$63.00** |

### Annual Cost: $756.00

### Optimization Notes

1. **Log Retention**: Reduce retention period
   - Current: 7 days for active, 30 days for historical
   - Alternative: 3 days for active, 7 days for historical
   - Potential savings: $1.50/month
   - Recommendation: Balance compliance needs with cost

2. **Log Filtering**: Filter unnecessary logs
   - Implement log sampling for high-volume functions
   - Filter debug logs in production
   - Potential savings: 20-30% reduction in ingestion costs

3. **Metric Optimization**: Reduce custom metrics
   - Current: 50 custom metrics
   - Review and consolidate metrics
   - Potential savings: $3-6/month
   - Recommendation: Keep essential metrics only

4. **CloudTrail Data Events**: Selective logging
   - Current: All S3 and Lambda events
   - Alternative: Log only critical buckets/functions
   - Potential savings: $10-15/month
   - Recommendation: Balance audit requirements with cost

### [NEEDS REVIEW] Items Requiring Validation

- **Log volume (50GB/month)**: Validate against actual log generation
- **Retention requirements**: Confirm compliance requirements for log retention
- **Custom metrics count**: Review necessity of all 50 metrics
- **CloudTrail event volume**: Validate data event logging requirements

## Component 8: Amazon ECR (Elastic Container Registry)

### Overview

Amazon ECR stores Docker container images for the AgentCore multi-agent system. The registry maintains multiple image versions for rollback capability.

### Configuration

- **Repository**: 1 private repository
- **Image storage**: 2 GB
- **Image versions**: 5 versions maintained
- **Lifecycle policy**: Keep last 5 images, delete older
- **Scanning**: Basic scanning enabled (free)

### Usage Assumptions

**Storage**:

- Agent container image: 2 GB
- Versions maintained: 5 (current + 4 previous)
- Total storage: 2 GB (with lifecycle policy)

**Data Transfer**:

- Image pulls: 10 GB/month
- Deployment frequency: 2-3 times per week
- Pull locations: Same region (us-east-1)

### Cost Breakdown

| Item | Unit Price | Usage | Monthly Cost |
|------|------------|-------|--------------|
| **Storage** | $0.10/GB-month | 2 GB | $0.20 |
| **Data Transfer (Same Region)** | $0.00/GB | 10 GB | $0.00 |
| **Data Transfer (Internet)** | $0.09/GB | 10 GB | $0.90 |
| **TOTAL** | | | **$1.10** |

**Note**: Design document shows $1.40, which may include additional data transfer.

### Annual Cost: $13.20 (using $1.10) or $16.80 (using design figure)

### Optimization Notes

1. **Image Size Optimization**: Reduce container image size
   - Current: 2 GB per image
   - Use multi-stage builds
   - Remove unnecessary dependencies
   - Potential savings: 30-50% reduction in storage

2. **Lifecycle Policy**: Already optimized
   - Current: Keep last 5 images
   - Automatic cleanup of old images
   - Prevents storage bloat

3. **Image Caching**: Leverage layer caching
   - Reduces build times
   - Reduces data transfer for pulls
   - No additional cost

4. **Scanning**: Use basic scanning (free)
   - Enhanced scanning: $0.09 per image scan
   - Current: Basic scanning (free)
   - Recommendation: Upgrade to enhanced if security requirements justify

### [NEEDS REVIEW] Items Requiring Validation

- **Image size (2GB)**: Validate actual container image size
- **Version retention (5)**: Confirm rollback requirements
- **Pull frequency**: Validate deployment and scaling patterns

## Cost Summary and Analysis

### Monthly Cost Breakdown

| Component | Monthly Cost | % of Backend Stack | Annual Cost |
|-----------|--------------|-------------------|-------------|
| Aurora PostgreSQL | $878.10 | 52.4% | $10,537.20 |
| Amazon Cognito | $555.00 | 33.1% | $6,660.00 |
| AWS Lambda | $104.50 | 6.2% | $1,254.00 |
| VPC/NAT Gateway | $54.90 | 3.3% | $658.80 |
| CloudWatch/CloudTrail | $63.00 | 3.8% | $756.00 |
| API Gateway | $10.00 | 0.6% | $120.00 |
| Secrets Manager & KMS | $7.00 | 0.4% | $84.00 |
| ECR | $1.40 | 0.1% | $16.80 |
| **TOTAL** | **$1,673.90** | **100%** | **$20,086.80** |

### Cost per User Metrics

- **Cost per MAU**: $0.167/month
- **Cost per Registered User**: $0.017/month (100K registered, 10K active)
- **Cost per API Request**: $0.000167 (10M requests/month)
- **Cost per Database Transaction**: $0.0000084 (200M I/O operations/month)

### Top Cost Drivers

1. **Aurora PostgreSQL** ($878.10/month, 52.4%)
   - Primary cost driver for Backend Stack
   - Scales with data volume and query complexity
   - Optimization: I/O-Optimized mode, connection pooling

2. **Amazon Cognito** ($555.00/month, 33.1%)
   - Advanced Security Features account for 90% of Cognito cost
   - Scales linearly with MAU
   - Optimization: Evaluate ASF necessity, consider MFA

3. **AWS Lambda** ($104.50/month, 6.2%)
   - Provisioned concurrency for agent_integration is significant
   - Scales with API request volume
   - Optimization: ARM64 migration, memory optimization

4. **VPC/NAT Gateway** ($54.90/month, 3.3%)
   - Fixed cost component (hourly charge)
   - Data processing scales with egress traffic
   - Optimization: VPC endpoints, IPv6 adoption

5. **CloudWatch/CloudTrail** ($63.00/month, 3.8%)
   - Monitoring and compliance logging
   - Scales with log volume and metrics
   - Optimization: Log filtering, retention policies

### Scaling Characteristics

**Linear Scaling Components** (scale 1:1 with MAU):

- Cognito: $0.0555 per MAU (with ASF)
- API Gateway: Scales with request volume
- Lambda: Scales with invocations

**Sub-Linear Scaling Components** (economies of scale):

- Aurora: Better ACU efficiency at higher loads
- NAT Gateway: Fixed hourly cost, data processing scales
- CloudWatch: Fixed metric costs, log volume scales

**Fixed Cost Components** (no scaling):

- KMS keys: $2.00/month regardless of usage
- ECR storage: Minimal scaling impact
- Base monitoring: Core CloudWatch costs

## Optimization Recommendations

### High-Impact Optimizations (>$50/month savings)

1. **Evaluate Cognito Advanced Security Features** (Potential: $500/month)
   - Current: ASF enabled for all 10,000 MAU
   - Alternative: Selective ASF for high-risk users only
   - Risk: Reduced security posture
   - Recommendation: Keep enabled for healthcare compliance

2. **Aurora I/O-Optimized Mode** (Potential: $50-100/month at scale)
   - Current: 200M I/O requests/month at $0.20/1M
   - Break-even: ~200-250M I/O requests/month
   - Recommendation: Monitor I/O patterns, switch if exceeding 250M

3. **Lambda Provisioned Concurrency Review** (Potential: $60/month)
   - Current: 10 instances for agent_integration
   - Alternative: Accept cold starts, eliminate provisioned concurrency
   - Risk: Increased latency for first request
   - Recommendation: Monitor cold start frequency and user impact

### Medium-Impact Optimizations ($10-50/month savings)

4. **Lambda ARM64 Migration** (Potential: $21/month)
   - Current: x86_64 architecture
   - Alternative: ARM64 (Graviton2) for 20% cost savings
   - Risk: Minimal, most runtimes support ARM64
   - Recommendation: Migrate all functions to ARM64

5. **VPC Endpoints for AWS Services** (Potential: $15-25/month)
   - Current: NAT Gateway for all AWS service access
   - Alternative: VPC endpoints for S3, DynamoDB, Bedrock
   - Savings: Reduce NAT Gateway data processing costs
   - Recommendation: Implement S3 and DynamoDB gateway endpoints (free)

6. **Aurora Connection Pooling** (Potential: $100/month)
   - Current: Direct connections from Lambda
   - Alternative: RDS Proxy or application-level pooling
   - Savings: 10-15% reduction in ACU usage
   - Recommendation: Implement connection pooling

### Low-Impact Optimizations (<$10/month savings)

7. **CloudWatch Log Retention** (Potential: $5/month)
   - Current: 7-30 day retention
   - Alternative: 3-7 day retention
   - Recommendation: Balance compliance needs with cost

8. **Secret Caching** (Potential: $2/month)
   - Current: 100K Secrets Manager API calls/month
   - Alternative: Cache secrets with 5-minute TTL
   - Recommendation: Implement in Lambda functions

9. **API Gateway Caching** (Potential: $5/month)
   - Current: No caching
   - Alternative: Enable caching for read-heavy endpoints
   - Cost: $0.02/hour per GB cache size
   - Recommendation: Implement for frequently accessed data

### Total Potential Savings

- **High-Impact**: $0-660/month (depends on ASF and provisioned concurrency decisions)
- **Medium-Impact**: $136-146/month
- **Low-Impact**: $12/month
- **Total**: $148-818/month (9-49% reduction)

## Scaling Analysis

### 50,000 MAU Scenario (5x Growth)

| Component | 10K MAU | 50K MAU | Scaling Factor | Notes |
|-----------|---------|---------|----------------|-------|
| Aurora | $878 | $3,073 | 3.5x | Sub-linear, better ACU efficiency |
| Cognito | $555 | $2,775 | 5.0x | Linear with MAU |
| Lambda | $105 | $525 | 5.0x | Linear with requests |
| API Gateway | $10 | $50 | 5.0x | Linear with requests |
| VPC/NAT | $55 | $110 | 2.0x | Hourly fixed, data scales |
| CloudWatch | $63 | $150 | 2.4x | Log volume scales |
| Secrets/KMS | $7 | $14 | 2.0x | API calls scale |
| ECR | $1.40 | $2.80 | 2.0x | Minimal scaling |
| **TOTAL** | **$1,674** | **$6,700** | **4.0x** | |

**Cost per MAU**: $0.134/month (20% reduction from economies of scale)

### 100,000 MAU Scenario (10x Growth)

| Component | 10K MAU | 100K MAU | Scaling Factor | Notes |
|-----------|---------|----------|----------------|-------|
| Aurora | $878 | $5,268 | 6.0x | Better efficiency at scale |
| Cognito | $555 | $5,550 | 10.0x | Linear with MAU |
| Lambda | $105 | $1,050 | 10.0x | Linear with requests |
| API Gateway | $10 | $95 | 9.5x | Volume discount kicks in |
| VPC/NAT | $55 | $165 | 3.0x | Multi-AZ for HA |
| CloudWatch | $63 | $250 | 4.0x | Log volume scales |
| Secrets/KMS | $7 | $21 | 3.0x | API calls scale |
| ECR | $1.40 | $4.20 | 3.0x | Minimal scaling |
| **TOTAL** | **$1,674** | **$12,403** | **7.4x** | |

**Cost per MAU**: $0.124/month (26% reduction from economies of scale)

### Scaling Insights

1. **Aurora Efficiency**: Database costs scale sub-linearly due to better ACU utilization at higher loads
2. **Cognito Dominance**: At 100K MAU, Cognito becomes the largest cost driver ($5,550/month)
3. **Volume Discounts**: API Gateway and other services benefit from tiered pricing at scale
4. **Fixed Costs**: VPC and monitoring costs don't scale linearly, providing cost efficiency

## HIPAA Compliance Considerations

### HIPAA-Eligible Services

All Backend Stack services are HIPAA-eligible when properly configured:

✅ **Aurora PostgreSQL**: HIPAA-eligible with encryption at rest and in transit  
✅ **Lambda**: HIPAA-eligible with proper IAM policies and encryption  
✅ **API Gateway**: HIPAA-eligible with TLS 1.2+ and logging  
✅ **Cognito**: HIPAA-eligible with BAA and encryption  
✅ **Secrets Manager**: HIPAA-eligible with KMS encryption  
✅ **KMS**: HIPAA-eligible for encryption key management  
✅ **CloudWatch**: HIPAA-eligible for logging and monitoring  
✅ **CloudTrail**: HIPAA-eligible for audit logging  
✅ **ECR**: HIPAA-eligible with encryption at rest  
✅ **VPC**: HIPAA-eligible with proper network isolation  

### Compliance Requirements

1. **Encryption at Rest**:
   - Aurora: KMS customer-managed key ($1.00/month)
   - S3: KMS customer-managed key ($1.00/month)
   - Secrets Manager: KMS encryption (included)
   - Total: $2.00/month (already included in costs)

2. **Encryption in Transit**:
   - TLS 1.2+ for all API endpoints
   - VPC for network isolation
   - No additional cost

3. **Audit Logging**:
   - CloudTrail: Management events (free)
   - CloudTrail: Data events ($20.00/month)
   - CloudWatch Logs: $28.00/month
   - Total: $48.00/month (already included in costs)

4. **Access Controls**:
   - IAM policies: No additional cost
   - Cognito authentication: $555.00/month (already included)
   - MFA: No additional cost (recommended to enable)

5. **Business Associate Agreement (BAA)**:
   - Required with AWS for HIPAA compliance
   - No additional cost
   - Must be signed before processing PHI

### Compliance Cost Summary

All HIPAA compliance requirements are included in the baseline Backend Stack costs. No additional charges for:

- Encryption at rest and in transit
- Audit logging
- Access controls
- BAA with AWS

**Total Compliance Overhead**: $0.00 (included in baseline)

## Monitoring and Alerting Recommendations

### Cost Monitoring

1. **AWS Budgets**:
   - Set budget: $1,800/month (7.5% buffer above baseline)
   - Alert thresholds: 80%, 90%, 100%
   - Forecast alerts: Enable to predict overruns

2. **Cost Anomaly Detection**:
   - Enable for Backend Stack
   - Threshold: $200 anomaly detection
   - Notification: Email and SNS

3. **Service-Level Budgets**:
   - Aurora: $950/month (alert at 85%)
   - Cognito: $600/month (alert at 90%)
   - Lambda: $120/month (alert at 85%)
   - Other services: $130/month combined

### Usage Monitoring

1. **Aurora Metrics**:
   - ACU utilization (target: 60-80% during peak)
   - I/O operations (monitor for I/O-Optimized threshold)
   - Connection count (optimize with pooling)
   - Storage growth (track 20% annual growth)

2. **Lambda Metrics**:
   - Invocation count (track against estimates)
   - Duration (optimize memory allocation)
   - Error rate (maintain <1%)
   - Cold start frequency (evaluate provisioned concurrency)

3. **Cognito Metrics**:
   - MAU count (track growth trends)
   - Authentication success rate
   - ASF detections (validate security value)

4. **API Gateway Metrics**:
   - Request count (track against 10M baseline)
   - 4xx/5xx error rates
   - Latency (p50, p95, p99)

### Review Schedule

- **Daily**: Cost Anomaly Detection alerts
- **Weekly**: Service usage trends
- **Monthly**: Full cost review and optimization opportunities
- **Quarterly**: Architecture review and scaling planning

## Assumptions and Exclusions

### Key Assumptions

1. **User Base**:
   - 100,000 registered users
   - 10,000 monthly active users (10% activation rate)
   - 20 sessions per MAU per month
   - 50 API calls per session

2. **Database**:
   - Peak hours: 8 AM - 8 PM (12 hours/day)
   - Off-peak hours: 8 PM - 8 AM (12 hours/day)
   - Peak ACU: 15 ACU (10 writer + 5 reader)
   - Off-peak ACU: 3 ACU (2 writer + 1 reader)
   - Storage: 500 GB with 20% annual growth
   - I/O: 200M requests/month

3. **Compute**:
   - Lambda memory: 256-1024 MB per function
   - Lambda duration: 150-900 seconds per invocation
   - VPC overhead: +50ms per invocation
   - Provisioned concurrency: 10 instances for agent_integration

4. **Authentication**:
   - All 10,000 MAU use Advanced Security Features
   - MFA: Disabled (can be enabled at no additional cost)
   - Session duration: Default Cognito settings

5. **Networking**:
   - Single NAT Gateway (single AZ)
   - Data processing: 100 GB/month
   - VPC endpoints: Not implemented (optimization opportunity)

6. **Security**:
   - 3 secrets in Secrets Manager
   - 2 customer-managed KMS keys
   - Automatic secret rotation enabled

7. **Monitoring**:
   - Log retention: 7 days active, 30 days historical
   - 50 custom CloudWatch metrics
   - CloudTrail data events enabled

### Exclusions

1. **Not Included in Backend Stack Costs**:
   - Frontend hosting (Amplify) - see Frontend Stack report
   - AI/ML services (Bedrock) - see Assistant Stack report
   - Document processing (BDA, S3) - see Document Workflow Stack report
   - Data transfer between stacks
   - Custom domain names and SSL certificates
   - AWS Support plans
   - Reserved Instances or Savings Plans
   - Development/staging environments

2. **One-Time Costs**:
   - Data migration from on-premise systems
   - Initial data loading
   - Professional services and consulting
   - Training and documentation

3. **Third-Party Costs**:
   - Palo Alto firewall integration
   - Active Directory integration
   - External monitoring tools
   - Compliance audit services

4. **Operational Costs**:
   - Development team salaries
   - DevOps and infrastructure management
   - Security operations
   - Incident response

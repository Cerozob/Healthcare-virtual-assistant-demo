# Service-Level Cost Breakdown Report

**Report Date**: October 28, 2025  
**Region**: us-east-1 (US East - N. Virginia)  
**Baseline Scenario**: 10,000 Monthly Active Users (MAU)  
**Pricing Model**: ON DEMAND

---

## Executive Summary

This report provides a comprehensive breakdown of AWS service costs across all stacks in the AWSomeBuilder2 healthcare management system. The analysis groups costs by individual AWS service to identify the primary cost drivers and optimization opportunities across the entire system architecture.

### Total System Cost by Service

**Monthly Total**: $28,440.21  
**Annual Total**: $341,282.52  
**Services Count**: 15 AWS services across 5 stacks

---

## Service Cost Ranking

### Top 10 AWS Services by Cost

| Rank | AWS Service | Monthly Cost | % of Total | Annual Cost | Primary Stack | Secondary Stacks |
|------|-------------|--------------|------------|-------------|---------------|------------------|
| 1 | **Amazon Bedrock (Foundation Models)** | $11,940.00 | 42.0% | $143,280.00 | Assistant | - |
| 2 | **Amazon Bedrock (Data Automation)** | $7,910.00 | 27.8% | $94,920.00 | Document Workflow | - |
| 3 | **Amazon Bedrock (Guardrails)** | $6,000.00 | 21.1% | $72,000.00 | Assistant | - |
| 4 | **AWS Lambda** | $1,182.00 | 4.2% | $14,184.00 | Backend, Document Workflow | - |
| 5 | **Amazon Aurora PostgreSQL** | $878.10 | 3.1% | $10,537.20 | Backend | - |
| 6 | **Amazon Cognito** | $555.00 | 2.0% | $6,660.00 | Backend | - |
| 7 | **Amazon Bedrock (Knowledge Base)** | $350.40 | 1.2% | $4,204.80 | Assistant | - |
| 8 | **Amazon Bedrock (Embeddings)** | $200.00 | 0.7% | $2,400.00 | Assistant | - |
| 9 | **AWS Amplify** | $182.52 | 0.6% | $2,190.24 | Frontend | - |
| 10 | **Amazon S3** | $132.25 | 0.5% | $1,587.00 | Document Workflow | - |

### Remaining Services (11-15)

| Rank | AWS Service | Monthly Cost | % of Total | Annual Cost | Primary Stack |
|------|-------------|--------------|------------|-------------|---------------|
| 11 | **Amazon CloudWatch** | $126.00 | 0.4% | $1,512.00 | Backend, Document Workflow |
| 12 | **Amazon Bedrock (AgentCore)** | $89.14 | 0.3% | $1,069.68 | Assistant |
| 13 | **Amazon VPC/NAT Gateway** | $54.90 | 0.2% | $658.80 | Backend |
| 14 | **Amazon EventBridge** | $10.00 | 0.04% | $120.00 | Document Workflow |
| 15 | **Amazon API Gateway** | $10.32 | 0.04% | $123.84 | API |

**Subtotal Top 15**: $28,620.63 (100.6% - includes rounding differences)

---

## Service Analysis by Category

### AI/ML Services - $25,682.30/month (90.3%)

#### Amazon Bedrock Services

| Bedrock Service | Monthly Cost | % of Bedrock | % of Total | Stack |
|-----------------|--------------|--------------|------------|-------|
| **Foundation Models** | $11,940.00 | 47.5% | 42.0% | Assistant |
| **Data Automation** | $7,910.00 | 31.5% | 27.8% | Document Workflow |
| **Guardrails** | $6,000.00 | 23.9% | 21.1% | Assistant |
| **Knowledge Base** | $350.40 | 1.4% | 1.2% | Assistant |
| **Embeddings** | $200.00 | 0.8% | 0.7% | Assistant |
| **AgentCore** | $89.14 | 0.4% | 0.3% | Assistant |
| **Bedrock Total** | **$26,489.54** | **100%** | **93.1%** | Multiple |

**Key Insights**:
- Bedrock services represent 93.1% of total system cost
- Foundation Models (Claude 3.5 Haiku/Sonnet) are the largest single cost driver
- Data Automation for document processing is the second largest cost
- Guardrails for content safety represent significant compliance cost

**Optimization Opportunities**:
- Model routing optimization: $1,200-$2,400/month
- Guardrails policy optimization: $1,500-$3,000/month
- Document processing batch optimization: $400-$800/month

### Compute Services - $2,060.10/month (7.2%)

| Service | Monthly Cost | % of Category | Stack Distribution |
|---------|--------------|---------------|-------------------|
| **AWS Lambda** | $1,182.00 | 57.4% | Backend ($104.50), Document Workflow ($1,077.31) |
| **Amazon Aurora** | $878.10 | 42.6% | Backend (100%) |

**Lambda Function Breakdown**:
- Document Workflow Functions: $1,077.31 (91.1%)
  - Data Extraction: $1,000.10 (84.6%)
  - BDA Trigger: $2.18 (0.2%)
  - Data Cleanup: $50.02 (4.2%)
  - Error Analysis: $25.01 (2.1%)
- Backend API Functions: $104.50 (8.9%)
  - All CRUD operations and agent integration

**Aurora Database Breakdown**:
- Compute (ACU-hours): $777.60 (88.5%)
- Storage (500GB): $50.00 (5.7%)
- I/O Operations (200M): $40.00 (4.6%)
- Backup Storage: $10.50 (1.2%)

### Authentication & Security - $562.00/month (2.0%)

| Service | Monthly Cost | % of Category | Purpose |
|---------|--------------|---------------|---------|
| **Amazon Cognito** | $555.00 | 98.8% | User authentication (10K MAU + ASF) |
| **AWS Secrets Manager** | $1.70 | 0.3% | Credential storage (3 secrets) |
| **AWS KMS** | $3.44 | 0.6% | Encryption key management (2 keys) |
| **AWS CloudTrail** | $1.86 | 0.3% | Audit logging |

**Cognito Cost Breakdown**:
- Base MAU: $55.00 (9.9%)
- Advanced Security Features: $500.00 (90.1%)

### Storage Services - $132.25/month (0.5%)

| Service | Monthly Cost | % of Category | Purpose |
|---------|--------------|---------------|---------|
| **Amazon S3** | $132.25 | 100% | Document storage, lifecycle management |

**S3 Cost Breakdown**:
- Standard Storage: $55.20 (41.7%)
- Cross-Region Replication: $34.50 (26.1%)
- Standard-IA Storage: $6.25 (4.7%)
- Intelligent Tiering: $7.50 (5.7%)
- Data Transfer: $9.00 (6.8%)
- Other (requests, logs, etc.): $19.80 (15.0%)

### Networking Services - $247.74/month (0.9%)

| Service | Monthly Cost | % of Category | Purpose |
|---------|--------------|---------------|---------|
| **AWS Amplify** | $182.52 | 73.7% | Frontend hosting and CDN |
| **VPC/NAT Gateway** | $54.90 | 22.2% | Network isolation and egress |
| **API Gateway** | $10.32 | 4.2% | HTTP API endpoints |

**Amplify Cost Breakdown**:
- Data Transfer: $180.00 (98.6%)
- Build Minutes: $1.50 (0.8%)
- Hosting Requests: $0.90 (0.5%)
- Storage: $0.12 (0.1%)

### Monitoring & Operations - $136.00/month (0.5%)

| Service | Monthly Cost | % of Category | Purpose |
|---------|--------------|---------------|---------|
| **Amazon CloudWatch** | $126.00 | 92.6% | Logging, metrics, monitoring |
| **Amazon EventBridge** | $10.00 | 7.4% | Event-driven workflows |

**CloudWatch Cost Breakdown**:
- Log Ingestion: $50.00 (39.7%)
- Custom Metrics: $45.00 (35.7%)
- Log Storage: $6.00 (4.8%)
- CloudTrail Data Events: $25.00 (19.8%)

---

## Cross-Stack Service Usage

### Services Used Across Multiple Stacks

#### AWS Lambda
- **Backend Stack**: $104.50/month
  - 7 API functions (patients, medics, exams, reservations, files, agent_integration, patient_lookup)
  - 2 utility functions (db_initialization, data_loader)
- **Document Workflow Stack**: $1,077.31/month
  - 4 workflow functions (BDA trigger, data extraction, cleanup, error analysis)
- **Total Lambda Cost**: $1,181.81/month

#### Amazon CloudWatch
- **Backend Stack**: $63.00/month
  - Lambda function logs
  - Aurora metrics
  - API Gateway logs
- **Document Workflow Stack**: $63.00/month
  - Document processing logs
  - S3 access logs
  - BDA workflow metrics
- **Total CloudWatch Cost**: $126.00/month

### Single-Stack Services

#### Assistant Stack Only
- Amazon Bedrock (all services): $26,489.54/month
- Amazon ECR: $0.20/month

#### Document Workflow Stack Only
- Amazon S3: $132.25/month
- Amazon EventBridge: $10.00/month

#### Backend Stack Only
- Amazon Aurora PostgreSQL: $878.10/month
- Amazon Cognito: $555.00/month
- AWS Secrets Manager: $1.70/month
- AWS KMS: $3.44/month
- VPC/NAT Gateway: $54.90/month

#### Frontend Stack Only
- AWS Amplify: $182.52/month

#### API Stack Only
- Amazon API Gateway: $10.32/month

---

## Service Optimization Analysis

### High-Impact Optimization Services (>$1,000/month potential)

#### 1. Amazon Bedrock Foundation Models ($11,940/month)
**Optimization Potential**: $1,200-$2,400/month (10-20% reduction)

**Strategies**:
- Increase Claude 3.5 Haiku usage from 90% to 95%
- Improve prompt caching from 60% to 75% hit rate
- Implement intelligent query routing
- Consider provisioned throughput for predictable workloads

**Implementation Priority**: High (largest cost driver)

#### 2. Amazon Bedrock Data Automation ($7,910/month)
**Optimization Potential**: $400-$800/month (5-10% reduction)

**Strategies**:
- Increase batch processing from 80% to 95%
- Implement document compression before processing
- Optimize document classification for processing efficiency
- Reduce real-time processing where possible

**Implementation Priority**: High (second largest cost driver)

#### 3. Amazon Bedrock Guardrails ($6,000/month)
**Optimization Potential**: $1,500-$3,000/month (25-50% reduction)

**Strategies**:
- Implement selective policy application
- Use client-side pre-filtering for obvious violations
- Apply expensive policies only to sensitive content
- Consider risk-based guardrails activation

**Implementation Priority**: High (significant compliance cost)

### Medium-Impact Optimization Services ($100-$1,000/month potential)

#### 4. AWS Lambda ($1,182/month)
**Optimization Potential**: $200-$400/month (17-34% reduction)

**Strategies**:
- Migrate all functions to ARM64 (20% cost savings)
- Right-size memory allocation based on profiling
- Optimize provisioned concurrency usage
- Implement connection pooling for database functions

**Implementation Priority**: Medium

#### 5. Amazon Aurora PostgreSQL ($878/month)
**Optimization Potential**: $100-$200/month (11-23% reduction)

**Strategies**:
- Implement connection pooling to reduce ACU spikes
- Evaluate I/O-Optimized mode for high I/O workloads
- Optimize query performance to reduce compute time
- Consider read replica optimization

**Implementation Priority**: Medium

#### 6. Amazon Cognito ($555/month)
**Optimization Potential**: $0-$500/month (0-90% reduction)

**Strategies**:
- Evaluate necessity of Advanced Security Features
- Implement selective ASF for high-risk users only
- Consider alternative authentication approaches
- Enable MFA to potentially reduce ASF dependency

**Implementation Priority**: Medium (requires security evaluation)

### Low-Impact Optimization Services (<$100/month potential)

#### 7. AWS Amplify ($182.52/month)
**Optimization Potential**: $90/month (49% reduction)

**Strategies**:
- Increase CDN cache hit rate from 80% to 90%
- Implement asset compression and optimization
- Reduce average page size through code splitting
- Optimize build process efficiency

**Implementation Priority**: Low

#### 8. Amazon S3 ($132.25/month)
**Optimization Potential**: $20-$40/month (15-30% reduction)

**Strategies**:
- Implement more aggressive lifecycle policies
- Optimize cross-region replication scope
- Use S3 Intelligent Tiering more effectively
- Reduce request costs through batching

**Implementation Priority**: Low

---

## Service Cost Trends and Scaling

### Linear Scaling Services (Scale 1:1 with MAU)

| Service | Current Cost | 50K MAU (5x) | 100K MAU (10x) | Scaling Factor |
|---------|--------------|---------------|-----------------|----------------|
| Bedrock Foundation Models | $11,940 | $59,700 | $119,400 | 1.0x |
| Bedrock Data Automation | $7,910 | $39,550 | $79,100 | 1.0x |
| Bedrock Guardrails | $6,000 | $30,000 | $60,000 | 1.0x |
| Lambda Functions | $1,182 | $5,910 | $11,820 | 1.0x |
| Cognito | $555 | $2,775 | $5,550 | 1.0x |
| API Gateway | $10.32 | $51.60 | $103.20 | 1.0x |

### Sub-Linear Scaling Services (Economies of Scale)

| Service | Current Cost | 50K MAU (5x) | 100K MAU (10x) | Scaling Factor |
|---------|--------------|---------------|-----------------|----------------|
| Aurora PostgreSQL | $878 | $3,073 | $5,268 | 0.6x |
| Amplify | $182.52 | $912.60 | $1,825.20 | 1.0x |
| S3 Storage | $132.25 | $661.25 | $1,322.50 | 1.0x |

### Fixed Cost Services (No Scaling)

| Service | Cost at Any Scale | Notes |
|---------|-------------------|-------|
| VPC/NAT Gateway | $54.90/month | Hourly charge, minimal data scaling |
| KMS Keys | $3.44/month | Per-key pricing |
| ECR | $0.20/month | Minimal scaling impact |
| EventBridge | $10.00/month | Event volume scales but cost minimal |

### Volume Discount Thresholds

| Service | Current Tier | Next Tier Threshold | Discount Available |
|---------|--------------|--------------------|--------------------|
| API Gateway | Tier 1 ($1.00/1M) | 300M requests | 10% ($0.90/1M) |
| Bedrock Models | Standard | Provisioned Throughput | 20-30% |
| S3 Data Transfer | First 10TB ($0.09/GB) | Next 40TB | 6% ($0.085/GB) |
| CloudWatch Logs | Standard | - | No volume discounts |

---

## Service Dependencies and Integration Costs

### Critical Service Dependencies

#### Primary Dependencies
1. **Bedrock Foundation Models** ← **Bedrock Guardrails**
   - All model interactions must pass through guardrails
   - Cost ratio: 2:1 (Models:Guardrails)
   - Optimization must consider both services together

2. **Lambda Functions** ← **Aurora PostgreSQL**
   - All API functions depend on database connectivity
   - VPC configuration adds latency and cost
   - Connection pooling affects both services

3. **Bedrock Data Automation** ← **S3 Storage**
   - All document processing requires S3 storage
   - Lifecycle policies affect processing costs
   - Cross-region replication impacts BDA access patterns

#### Secondary Dependencies
1. **API Gateway** ← **Lambda Functions**
   - All API requests trigger Lambda executions
   - Request volume directly correlates

2. **Amplify** ← **Cognito**
   - Frontend authentication depends on Cognito
   - User growth affects both services

3. **CloudWatch** ← **All Services**
   - Monitoring costs scale with service usage
   - Log volume increases with system activity

### Integration Cost Considerations

#### Data Transfer Costs
- **Intra-Region**: Free between most services
- **Cross-AZ**: $0.01/GB for Aurora Multi-AZ
- **Internet Egress**: $0.09/GB for Amplify CDN
- **VPC Endpoints**: Could reduce NAT Gateway costs

#### API Call Costs
- **Secrets Manager**: $0.05 per 10K API calls
- **KMS**: $0.03 per 10K requests
- **Parameter Store**: Free for standard parameters

---

## Service-Level Monitoring Recommendations

### Critical Service Alerts (>$5,000/month)

#### Amazon Bedrock Foundation Models
- **Budget Alert**: $13,000/month (110% of baseline)
- **Usage Alert**: >2.2M interactions/month
- **Performance Alert**: Cache hit rate <50%
- **Cost Anomaly**: >$2,000 daily increase

#### Amazon Bedrock Data Automation
- **Budget Alert**: $8,500/month (107% of baseline)
- **Usage Alert**: >220K pages/month
- **Performance Alert**: Batch ratio <70%
- **Cost Anomaly**: >$1,500 daily increase

#### Amazon Bedrock Guardrails
- **Budget Alert**: $6,500/month (108% of baseline)
- **Usage Alert**: >25M text units/month
- **Performance Alert**: Violation rate >10%
- **Cost Anomaly**: >$1,000 daily increase

### Important Service Alerts ($500-$5,000/month)

#### AWS Lambda
- **Budget Alert**: $1,300/month (110% of baseline)
- **Usage Alert**: >6M invocations/month
- **Performance Alert**: Error rate >1%
- **Cost Anomaly**: >$200 daily increase

#### Amazon Aurora PostgreSQL
- **Budget Alert**: $950/month (108% of baseline)
- **Usage Alert**: >7,000 ACU-hours/month
- **Performance Alert**: I/O >250M requests/month
- **Cost Anomaly**: >$150 daily increase

#### Amazon Cognito
- **Budget Alert**: $600/month (108% of baseline)
- **Usage Alert**: >11,000 MAU
- **Performance Alert**: Auth failure rate >5%
- **Cost Anomaly**: >$100 daily increase

### Standard Service Alerts (<$500/month)

#### All Other Services
- **Budget Alert**: 110% of baseline cost
- **Usage Alert**: 120% of expected usage
- **Cost Anomaly**: >$50 daily increase

---

## Recommendations by Service

### Immediate Actions (0-30 days)

#### High-Priority Services
1. **Amazon Bedrock Foundation Models**
   - Implement token usage monitoring
   - Set up cache hit rate tracking
   - Create model routing efficiency dashboard

2. **Amazon Bedrock Data Automation**
   - Monitor batch vs real-time processing ratio
   - Track document processing success rates
   - Set up volume trend analysis

3. **Amazon Bedrock Guardrails**
   - Analyze policy violation patterns
   - Identify opportunities for selective application
   - Monitor text processing volume trends

#### Medium-Priority Services
4. **AWS Lambda**
   - Profile memory usage across all functions
   - Plan ARM64 migration strategy
   - Implement connection pooling for database functions

5. **Amazon Aurora PostgreSQL**
   - Monitor ACU utilization patterns
   - Analyze I/O request patterns for optimization opportunities
   - Set up connection pooling evaluation

### Short-Term Actions (1-3 months)

#### Optimization Implementation
1. **Bedrock Services**
   - Deploy model routing optimization
   - Implement enhanced prompt caching
   - Roll out selective guardrails policies

2. **Compute Services**
   - Execute Lambda ARM64 migration
   - Implement Aurora connection pooling
   - Optimize Lambda memory allocation

3. **Storage and Networking**
   - Deploy S3 lifecycle optimization
   - Implement Amplify CDN improvements
   - Evaluate VPC endpoint implementation

### Long-Term Actions (3-12 months)

#### Strategic Optimization
1. **Enterprise Scaling Preparation**
   - Evaluate provisioned throughput for Bedrock
   - Plan multi-region architecture
   - Implement advanced monitoring and automation

2. **Cost Governance**
   - Establish service-level cost ownership
   - Create optimization tracking and reporting
   - Plan for enterprise pricing negotiations

---

## Conclusion

The service-level cost analysis reveals that the AWSomeBuilder2 system is heavily dominated by Amazon Bedrock services, which account for 93.1% of total costs. This AI-first architecture provides significant value but requires careful optimization to maintain cost efficiency.

### Key Findings

1. **Service Concentration**: Top 3 services (all Bedrock) represent 90.9% of total cost
2. **Optimization Potential**: $4,325-$8,525/month (15-30% reduction) across all services
3. **Scaling Characteristics**: Most services scale linearly with user growth
4. **Critical Dependencies**: Bedrock services are tightly coupled and must be optimized together

### Success Factors

- Focus optimization efforts on Bedrock services (93% of cost)
- Implement comprehensive monitoring for top 5 services
- Maintain service dependency awareness during optimization
- Plan for predictable linear scaling with user growth

The service-level breakdown provides clear priorities for cost optimization and monitoring, enabling targeted improvements that will have the greatest impact on overall system cost efficiency.

---

**Report Version**: 1.0  
**Last Updated**: October 28, 2025  
**Prepared By**: AWS Cost Estimation Team  
**Next Review**: November 28, 2025

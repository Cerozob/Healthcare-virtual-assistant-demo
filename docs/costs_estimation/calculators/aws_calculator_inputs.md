# AWS Pricing Calculator Input Guide

**AWSomeBuilder2 Healthcare Management System**  
**Date**: October 28, 2025  
**Region**: us-east-1 (US East - N. Virginia)  
**Purpose**: Three scenarios for AWS Pricing Calculator validation

---

## Overview

This document provides detailed inputs for the AWS Pricing Calculator organized by service to match the calculator's structure. Three scenarios are provided:

1. **Demo Scenario** (1 user - developer testing)
2. **Production Scenario** (10,000 MAU - baseline estimate)  
3. **Scale Scenario** (100,000 MAU - 10x growth)

**Reference Documents**:
- Service Cost Breakdown: `docs/costs_estimation/reports/service_cost_breakdown.md`
- Stack Cost Summary: `docs/costs_estimation/reports/stack_cost_summary.md`
- Assumptions Document: `docs/costs_estimation/reports/assumptions_and_exclusions.md`
- Network Gap Analysis: `docs/costs_estimation/reports/network_cost_gap_analysis.md`

---

## Scenario 1: Demo Scenario (1 User)

**Use Case**: Single developer testing and demonstration  
**MAU**: 1 user  
**Sessions**: 50 sessions/month  
**AI Interactions**: 500 interactions/month  
**Documents**: 10 documents/month (80 pages)

### Amazon Bedrock

#### Foundation Models
- **Service**: Amazon Bedrock Foundation Models
- **Model**: Claude 3.5 Haiku (primary)
- **Input Tokens**: 1,000,000 tokens/month (500 interactions × 2,000 tokens)
- **Output Tokens**: 400,000 tokens/month (500 interactions × 800 tokens)
- **Cache Hit Rate**: 60%
- **Estimated Cost**: $5.97/month

**Calculator Inputs**:
```
Service: Amazon Bedrock
Model: Claude 3.5 Haiku
Input tokens: 1,000,000 per month
Output tokens: 400,000 per month
Caching: 60% hit rate
```

#### Data Automation (Document Processing)
- **Service**: Amazon Bedrock Data Automation
- **Pages Processed**: 80 pages/month
- **Processing Type**: 80% batch, 20% real-time
- **Estimated Cost**: $3.16/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Data Automation
Pages: 80 per month
Batch processing: 64 pages
Real-time processing: 16 pages
```

#### Guardrails
- **Service**: Amazon Bedrock Guardrails
- **Text Units**: 8,400 text units/month (500 interactions × 2,800 tokens × 6 chars/token ÷ 1,000)
- **Policies**: Content Policy + PII Detection
- **Estimated Cost**: $2.10/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Guardrails
Text units: 8,400 per month
Content Policy: Enabled
PII Detection: Enabled
```

#### Knowledge Base
- **Service**: Amazon Bedrock Knowledge Base
- **OCUs**: 0.5 OCU (minimum for testing)
- **Runtime**: 730 hours/month
- **Queries**: 500 queries/month
- **Estimated Cost**: $87.60/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Knowledge Base
OCUs: 0.5
Runtime hours: 730 per month
Queries: 500 per month
```

### AWS Lambda

#### Backend Functions
- **Service**: AWS Lambda
- **Architecture**: x86_64 (baseline), ARM64 (optimized)
- **Memory**: 512 MB average
- **Invocations**: 1,500/month (50 sessions × 30 API calls)
- **Duration**: 200ms average
- **VPC**: Enabled
- **Estimated Cost**: $0.52/month

**Calculator Inputs**:
```
Service: AWS Lambda
Architecture: x86_64
Memory: 512 MB
Invocations: 1,500 per month
Duration: 200 ms average
VPC: Yes
```

#### Document Processing Functions
- **Service**: AWS Lambda
- **Memory**: 1024 MB
- **Invocations**: 80/month (document processing)
- **Duration**: 5,000ms average
- **Estimated Cost**: $0.43/month

**Calculator Inputs**:
```
Service: AWS Lambda
Memory: 1024 MB
Invocations: 80 per month
Duration: 5,000 ms average
VPC: Yes
```

### Amazon Aurora PostgreSQL

#### Database Configuration
- **Service**: Amazon Aurora PostgreSQL-Compatible
- **Version**: Serverless v2
- **ACU Range**: 0.5-2 ACU
- **Average ACU**: 1 ACU
- **Runtime**: 730 hours/month
- **Storage**: 10 GB
- **I/O Operations**: 100,000/month
- **Estimated Cost**: $43.90/month

**Calculator Inputs**:
```
Service: Amazon Aurora PostgreSQL
Type: Serverless v2
Min ACU: 0.5
Max ACU: 2
Average ACU: 1
Storage: 10 GB
I/O operations: 100,000 per month
Multi-AZ: No
```

### Amazon Cognito

#### User Authentication
- **Service**: Amazon Cognito
- **MAU**: 1 user
- **Advanced Security Features**: Disabled for demo
- **Estimated Cost**: $0.01/month

**Calculator Inputs**:
```
Service: Amazon Cognito
MAU: 1
Advanced Security Features: No
```

### Amazon S3

#### Document Storage
- **Service**: Amazon S3
- **Storage Class**: Standard
- **Storage Amount**: 1 GB
- **PUT Requests**: 100/month
- **GET Requests**: 500/month
- **Data Transfer Out**: 1 GB/month
- **Estimated Cost**: $0.13/month

**Calculator Inputs**:
```
Service: Amazon S3
Storage class: Standard
Storage: 1 GB
PUT requests: 100 per month
GET requests: 500 per month
Data transfer out: 1 GB per month
```

### AWS Amplify

#### Frontend Hosting
- **Service**: AWS Amplify
- **Build Minutes**: 10/month
- **Hosting Requests**: 15,000/month (50 sessions × 300 page views)
- **Data Transfer**: 5 GB/month
- **Storage**: 100 MB
- **Estimated Cost**: $0.91/month

**Calculator Inputs**:
```
Service: AWS Amplify
Build minutes: 10 per month
Hosting requests: 15,000 per month
Data transfer: 5 GB per month
Storage: 100 MB
```

### Amazon API Gateway

#### HTTP API
- **Service**: Amazon API Gateway (HTTP API)
- **Requests**: 1,500/month
- **Data Transfer Out**: 0.15 GB/month
- **Estimated Cost**: $0.01/month

**Calculator Inputs**:
```
Service: Amazon API Gateway
Type: HTTP API
Requests: 1,500 per month
Data transfer out: 0.15 GB per month
```

### Amazon VPC

#### NAT Gateway
- **Service**: Amazon VPC NAT Gateway
- **Gateways**: 1
- **Runtime**: 730 hours/month
- **Data Processing**: 2 GB/month
- **Estimated Cost**: $32.94/month

**Calculator Inputs**:
```
Service: Amazon VPC NAT Gateway
Number of gateways: 1
Hours: 730 per month
Data processed: 2 GB per month
```

### Amazon CloudWatch

#### Monitoring and Logging
- **Service**: Amazon CloudWatch
- **Log Ingestion**: 1 GB/month
- **Custom Metrics**: 10 metrics
- **Log Storage**: 1 GB
- **Estimated Cost**: $2.51/month

**Calculator Inputs**:
```
Service: Amazon CloudWatch
Log ingestion: 1 GB per month
Custom metrics: 10
Log storage: 1 GB
```

### **Demo Scenario Total**: ~$180/month

---

## Scenario 2: Production Scenario (10,000 MAU)

**Use Case**: Production deployment baseline  
**MAU**: 10,000 users  
**Sessions**: 200,000 sessions/month  
**AI Interactions**: 2,000,000 interactions/month  
**Documents**: 25,000 documents/month (200,000 pages)

### Amazon Bedrock

#### Foundation Models
- **Service**: Amazon Bedrock Foundation Models
- **Models**: 
  - Claude 3.5 Haiku (90%): 1,800,000 interactions
  - Claude 3.5 Sonnet (10%): 200,000 interactions
- **Input Tokens**: 
  - Haiku: 3,600M tokens (1.8M × 2K tokens)
  - Sonnet: 800M tokens (200K × 4K tokens)
- **Output Tokens**:
  - Haiku: 1,440M tokens (1.8M × 800 tokens)
  - Sonnet: 300M tokens (200K × 1.5K tokens)
- **Cache Hit Rate**: 60%
- **Estimated Cost**: $11,940/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Foundation Models

Claude 3.5 Haiku:
- Input tokens: 3,600,000,000 per month
- Output tokens: 1,440,000,000 per month
- Caching: 60% hit rate

Claude 3.5 Sonnet:
- Input tokens: 800,000,000 per month
- Output tokens: 300,000,000 per month
- Caching: 60% hit rate
```

#### Data Automation (Document Processing)
- **Service**: Amazon Bedrock Data Automation
- **Pages Processed**: 200,000 pages/month
- **Processing Type**: 80% batch (160K pages), 20% real-time (40K pages)
- **Audio Files**: 5,000 files × 15 minutes = 75,000 minutes
- **Video Files**: 200 files × 10 minutes = 2,000 minutes
- **Estimated Cost**: $7,910/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Data Automation
Document pages: 200,000 per month
Batch processing: 160,000 pages
Real-time processing: 40,000 pages
Audio processing: 75,000 minutes per month
Video processing: 2,000 minutes per month
```

#### Guardrails
- **Service**: Amazon Bedrock Guardrails
- **Text Units**: 24,000,000 text units/month
  - Calculation: 2M interactions × 3K avg tokens × 4 chars/token ÷ 1,000
- **Policies**: Content Policy + PII Detection
- **Estimated Cost**: $6,000/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Guardrails
Text units: 24,000,000 per month
Content Policy: Enabled ($0.15 per 1K units)
PII Detection: Enabled ($0.10 per 1K units)
```

#### Knowledge Base
- **Service**: Amazon Bedrock Knowledge Base
- **OCUs**: 2 OCUs (1 search + 1 indexing)
- **Runtime**: 730 hours/month
- **Queries**: 2,000,000 queries/month
- **Vector Storage**: 50 GB
- **Estimated Cost**: $350.40/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Knowledge Base
OCUs: 2
Runtime hours: 730 per month
Queries: 2,000,000 per month
Vector storage: 50 GB
```

#### Embeddings
- **Service**: Amazon Bedrock Embeddings
- **Model**: Titan Embeddings
- **Tokens**: 100,000,000 tokens/month
- **Search Units**: 100,000 search units/month
- **Estimated Cost**: $200/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Embeddings
Model: Titan Embeddings
Search units: 100,000 per month
```

#### AgentCore
- **Service**: Amazon Bedrock AgentCore
- **Runtime**: 730 hours/month
- **vCPU**: 1 vCPU
- **Memory**: 2 GB
- **Gateway Requests**: 2,000,000/month
- **Data Transfer**: 50 GB/month
- **Estimated Cost**: $89.14/month

**Calculator Inputs**:
```
Service: Amazon Bedrock AgentCore
Runtime hours: 730 per month
vCPU: 1
Memory: 2 GB
Gateway requests: 2,000,000 per month
Data transfer: 50 GB per month
```

### AWS Lambda

#### Backend API Functions
- **Service**: AWS Lambda
- **Architecture**: x86_64 (baseline), ARM64 (optimized -20% cost)
- **Functions**: 9 functions
- **Memory**: 512 MB average
- **Invocations**: 6,000,000/month (200K sessions × 30 API calls)
- **Duration**: 200ms average
- **VPC**: Enabled (+50ms cold start)
- **Provisioned Concurrency**: 10 instances for agent_integration
- **Estimated Cost**: $104.50/month

**Calculator Inputs**:
```
Service: AWS Lambda
Architecture: x86_64 (or ARM64 for -20% cost)
Memory: 512 MB
Invocations: 6,000,000 per month
Duration: 200 ms average
VPC: Yes
Provisioned concurrency: 10 instances
```

#### Document Workflow Functions
- **Service**: AWS Lambda
- **Functions**: 4 workflow functions
- **Memory**: 1024 MB average
- **Invocations**: 1,000,000/month
- **Duration**: 5,000ms average (document processing)
- **VPC**: Enabled
- **Estimated Cost**: $1,077.31/month

**Calculator Inputs**:
```
Service: AWS Lambda
Memory: 1024 MB
Invocations: 1,000,000 per month
Duration: 5,000 ms average
VPC: Yes
```

### Amazon Aurora PostgreSQL

#### Production Database
- **Service**: Amazon Aurora PostgreSQL-Compatible
- **Version**: Serverless v2
- **ACU Range**: 2-15 ACU
- **Average ACU**: 8.9 ACU (6,480 ACU-hours ÷ 730 hours)
- **Runtime**: 730 hours/month
- **Storage**: 500 GB
- **I/O Operations**: 200,000,000/month
- **Multi-AZ**: Yes
- **Backup Storage**: 100 GB
- **Estimated Cost**: $878.10/month

**Calculator Inputs**:
```
Service: Amazon Aurora PostgreSQL
Type: Serverless v2
Min ACU: 2
Max ACU: 15
Average ACU: 8.9
Storage: 500 GB
I/O operations: 200,000,000 per month
Multi-AZ: Yes
Backup storage: 100 GB
```

### Amazon Cognito

#### User Authentication
- **Service**: Amazon Cognito
- **MAU**: 10,000 users
- **Advanced Security Features**: Enabled for all users
- **MFA**: Optional
- **Estimated Cost**: $555/month

**Calculator Inputs**:
```
Service: Amazon Cognito
MAU: 10,000
Advanced Security Features: Yes ($0.05 per MAU)
Base pricing: $0.0055 per MAU
```

### Amazon S3

#### Document Storage
- **Service**: Amazon S3
- **Storage Classes**:
  - Standard: 2,400 GB
  - Standard-IA: 500 GB
  - Intelligent Tiering: 300 GB
- **Requests**:
  - PUT: 500,000/month
  - GET: 2,000,000/month
- **Data Transfer Out**: 100 GB/month
- **Cross-Region Replication**: 1,500 GB/month
- **Estimated Cost**: $132.25/month

**Calculator Inputs**:
```
Service: Amazon S3
Standard storage: 2,400 GB
Standard-IA storage: 500 GB
Intelligent Tiering: 300 GB
PUT requests: 500,000 per month
GET requests: 2,000,000 per month
Data transfer out: 100 GB per month
Cross-region replication: 1,500 GB per month
```

### AWS Amplify

#### Frontend Hosting
- **Service**: AWS Amplify
- **Build Minutes**: 150/month
- **Hosting Requests**: 3,000,000/month
- **Data Transfer**: 1,200 GB/month (after 80% CDN cache hit rate)
- **Storage**: 5 GB
- **Estimated Cost**: $182.52/month

**Calculator Inputs**:
```
Service: AWS Amplify
Build minutes: 150 per month
Hosting requests: 3,000,000 per month
Data transfer: 1,200 GB per month
Storage: 5 GB
CDN cache hit rate: 80%
```

### Amazon API Gateway

#### HTTP API
- **Service**: Amazon API Gateway (HTTP API)
- **Requests**: 6,000,000/month
- **Data Transfer Out**: 48 GB/month
- **Average Response Size**: 8 KB
- **Estimated Cost**: $10.32/month

**Calculator Inputs**:
```
Service: Amazon API Gateway
Type: HTTP API
Requests: 6,000,000 per month
Data transfer out: 48 GB per month
```

### Amazon VPC

#### NAT Gateway
- **Service**: Amazon VPC NAT Gateway
- **Gateways**: 1 (single AZ for cost optimization)
- **Runtime**: 730 hours/month
- **Data Processing**: 500 GB/month
- **Estimated Cost**: $54.90/month

**Calculator Inputs**:
```
Service: Amazon VPC NAT Gateway
Number of gateways: 1
Hours: 730 per month
Data processed: 500 GB per month
```

### Amazon CloudWatch

#### Monitoring and Logging
- **Service**: Amazon CloudWatch
- **Log Ingestion**: 50 GB/month
- **Custom Metrics**: 450 metrics
- **Log Storage**: 6 GB
- **CloudTrail Data Events**: 25,000,000 events
- **Estimated Cost**: $126/month

**Calculator Inputs**:
```
Service: Amazon CloudWatch
Log ingestion: 50 GB per month
Custom metrics: 450
Log storage: 6 GB
Data events: 25,000,000 per month
```

### Additional Services

#### Amazon EventBridge
- **Service**: Amazon EventBridge
- **Custom Events**: 1,000,000/month
- **Estimated Cost**: $10/month

**Calculator Inputs**:
```
Service: Amazon EventBridge
Custom events: 1,000,000 per month
```

#### AWS Secrets Manager
- **Service**: AWS Secrets Manager
- **Secrets**: 3 secrets
- **API Calls**: 100,000/month
- **Estimated Cost**: $1.70/month

**Calculator Inputs**:
```
Service: AWS Secrets Manager
Number of secrets: 3
API calls: 100,000 per month
```

#### AWS KMS
- **Service**: AWS Key Management Service
- **Customer Managed Keys**: 2 keys
- **Requests**: 100,000/month
- **Estimated Cost**: $3.44/month

**Calculator Inputs**:
```
Service: AWS KMS
Customer managed keys: 2
Requests: 100,000 per month
```

#### Amazon ECR
- **Service**: Amazon Elastic Container Registry
- **Storage**: 2 GB
- **Data Transfer**: 10 GB/month
- **Estimated Cost**: $0.20/month

**Calculator Inputs**:
```
Service: Amazon ECR
Storage: 2 GB
Data transfer: 10 GB per month
```

### **Production Scenario Total**: ~$28,440/month

---

## Scenario 3: Scale Scenario (100,000 MAU - 10x Growth)

**Use Case**: Enterprise scale deployment  
**MAU**: 100,000 users  
**Sessions**: 2,000,000 sessions/month  
**AI Interactions**: 20,000,000 interactions/month  
**Documents**: 250,000 documents/month (2,000,000 pages)

### Amazon Bedrock

#### Foundation Models (with Provisioned Throughput Optimization)
- **Service**: Amazon Bedrock Foundation Models
- **Models**: 
  - Claude 3.5 Haiku (95%): 19,000,000 interactions
  - Claude 3.5 Sonnet (5%): 1,000,000 interactions
- **Provisioned Throughput**: Enabled for predictable workloads (15% discount)
- **Input Tokens**: 
  - Haiku: 38,000M tokens (19M × 2K tokens)
  - Sonnet: 4,000M tokens (1M × 4K tokens)
- **Output Tokens**:
  - Haiku: 15,200M tokens (19M × 800 tokens)
  - Sonnet: 1,500M tokens (1M × 1.5K tokens)
- **Cache Hit Rate**: 75% (optimized)
- **Estimated Cost**: $101,490/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Foundation Models

Claude 3.5 Haiku (Provisioned Throughput):
- Input tokens: 38,000,000,000 per month
- Output tokens: 15,200,000,000 per month
- Caching: 75% hit rate
- Provisioned throughput: Yes (15% discount)

Claude 3.5 Sonnet (On-Demand):
- Input tokens: 4,000,000,000 per month
- Output tokens: 1,500,000,000 per month
- Caching: 75% hit rate
```

#### Data Automation (Document Processing)
- **Service**: Amazon Bedrock Data Automation
- **Pages Processed**: 2,000,000 pages/month
- **Processing Type**: 95% batch (1.9M pages), 5% real-time (100K pages)
- **Audio Files**: 50,000 files × 15 minutes = 750,000 minutes
- **Video Files**: 2,000 files × 10 minutes = 20,000 minutes
- **Batch Discount**: 10% for high volume
- **Estimated Cost**: $71,190/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Data Automation
Document pages: 2,000,000 per month
Batch processing: 1,900,000 pages (10% discount)
Real-time processing: 100,000 pages
Audio processing: 750,000 minutes per month
Video processing: 20,000 minutes per month
```

#### Guardrails (Optimized)
- **Service**: Amazon Bedrock Guardrails
- **Text Units**: 200,000,000 text units/month
- **Selective Policy Application**: 70% of interactions (optimization)
- **Policies**: Content Policy + PII Detection
- **Estimated Cost**: $42,000/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Guardrails
Text units: 200,000,000 per month
Content Policy: 70% coverage ($0.15 per 1K units)
PII Detection: 70% coverage ($0.10 per 1K units)
```

#### Knowledge Base (Scaled)
- **Service**: Amazon Bedrock Knowledge Base
- **OCUs**: 5 OCUs (3 search + 2 indexing)
- **Runtime**: 730 hours/month
- **Queries**: 20,000,000 queries/month
- **Vector Storage**: 200 GB
- **Estimated Cost**: $876/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Knowledge Base
OCUs: 5
Runtime hours: 730 per month
Queries: 20,000,000 per month
Vector storage: 200 GB
```

#### Embeddings (Scaled)
- **Service**: Amazon Bedrock Embeddings
- **Model**: Titan Embeddings
- **Tokens**: 1,000,000,000 tokens/month
- **Search Units**: 1,000,000 search units/month
- **Estimated Cost**: $2,000/month

**Calculator Inputs**:
```
Service: Amazon Bedrock Embeddings
Model: Titan Embeddings
Search units: 1,000,000 per month
```

#### AgentCore (Scaled)
- **Service**: Amazon Bedrock AgentCore
- **Runtime**: 730 hours/month
- **vCPU**: 2 vCPU
- **Memory**: 4 GB
- **Gateway Requests**: 20,000,000/month
- **Data Transfer**: 500 GB/month
- **Estimated Cost**: $445.70/month

**Calculator Inputs**:
```
Service: Amazon Bedrock AgentCore
Runtime hours: 730 per month
vCPU: 2
Memory: 4 GB
Gateway requests: 20,000,000 per month
Data transfer: 500 GB per month
```

### AWS Lambda (ARM64 Optimized)

#### Backend API Functions
- **Service**: AWS Lambda
- **Architecture**: ARM64 (20% cost savings)
- **Functions**: 9 functions
- **Memory**: 512 MB average (optimized)
- **Invocations**: 60,000,000/month
- **Duration**: 180ms average (optimized)
- **VPC**: Enabled with connection pooling
- **Provisioned Concurrency**: 50 instances for agent_integration
- **Estimated Cost**: $945/month

**Calculator Inputs**:
```
Service: AWS Lambda
Architecture: ARM64
Memory: 512 MB
Invocations: 60,000,000 per month
Duration: 180 ms average
VPC: Yes
Provisioned concurrency: 50 instances
```

#### Document Workflow Functions
- **Service**: AWS Lambda
- **Architecture**: ARM64
- **Functions**: 4 workflow functions
- **Memory**: 1024 MB
- **Invocations**: 10,000,000/month
- **Duration**: 4,500ms average (optimized)
- **VPC**: Enabled
- **Estimated Cost**: $9,720/month

**Calculator Inputs**:
```
Service: AWS Lambda
Architecture: ARM64
Memory: 1024 MB
Invocations: 10,000,000 per month
Duration: 4,500 ms average
VPC: Yes
```

### Amazon Aurora PostgreSQL (I/O Optimized)

#### Enterprise Database
- **Service**: Amazon Aurora PostgreSQL-Compatible
- **Version**: Serverless v2
- **Configuration**: I/O-Optimized
- **ACU Range**: 5-50 ACU
- **Average ACU**: 25 ACU
- **Runtime**: 730 hours/month
- **Storage**: 2,000 GB
- **I/O Operations**: 1,000,000,000/month
- **Multi-AZ**: Yes
- **Read Replicas**: 2 replicas
- **Backup Storage**: 500 GB
- **Estimated Cost**: $5,268/month

**Calculator Inputs**:
```
Service: Amazon Aurora PostgreSQL
Type: Serverless v2 I/O-Optimized
Min ACU: 5
Max ACU: 50
Average ACU: 25
Storage: 2,000 GB
I/O operations: 1,000,000,000 per month
Multi-AZ: Yes
Read replicas: 2
Backup storage: 500 GB
```

### Amazon Cognito (Selective ASF)

#### User Authentication
- **Service**: Amazon Cognito
- **MAU**: 100,000 users
- **Advanced Security Features**: 50% of users (risk-based)
- **MFA**: Enabled for high-risk users
- **Estimated Cost**: $3,275/month

**Calculator Inputs**:
```
Service: Amazon Cognito
MAU: 100,000
Advanced Security Features: 50,000 users ($0.05 per MAU)
Base pricing: 100,000 users ($0.0055 per MAU)
```

### Amazon S3 (Optimized Lifecycle)

#### Document Storage
- **Service**: Amazon S3
- **Storage Classes**:
  - Standard: 10,000 GB
  - Standard-IA: 5,000 GB
  - Glacier Instant Retrieval: 15,000 GB
  - Intelligent Tiering: 5,000 GB
- **Requests**:
  - PUT: 5,000,000/month
  - GET: 20,000,000/month
- **Data Transfer Out**: 1,000 GB/month
- **Cross-Region Replication**: 15,000 GB/month
- **Estimated Cost**: $1,322.50/month

**Calculator Inputs**:
```
Service: Amazon S3
Standard storage: 10,000 GB
Standard-IA storage: 5,000 GB
Glacier Instant Retrieval: 15,000 GB
Intelligent Tiering: 5,000 GB
PUT requests: 5,000,000 per month
GET requests: 20,000,000 per month
Data transfer out: 1,000 GB per month
Cross-region replication: 15,000 GB per month
```

### AWS Amplify (Multi-Region CDN)

#### Frontend Hosting
- **Service**: AWS Amplify
- **Build Minutes**: 300/month
- **Hosting Requests**: 30,000,000/month
- **Data Transfer**: 12,000 GB/month (after 90% CDN cache hit rate)
- **Storage**: 20 GB
- **Multi-Region**: Enabled
- **Estimated Cost**: $1,825.20/month

**Calculator Inputs**:
```
Service: AWS Amplify
Build minutes: 300 per month
Hosting requests: 30,000,000 per month
Data transfer: 12,000 GB per month
Storage: 20 GB
CDN cache hit rate: 90%
Multi-region: Yes
```

### Amazon API Gateway (Volume Discount)

#### HTTP API
- **Service**: Amazon API Gateway (HTTP API)
- **Requests**: 60,000,000/month
- **Volume Discount**: Tier 1 pricing (under 300M requests)
- **Data Transfer Out**: 480 GB/month
- **Average Response Size**: 8 KB
- **Estimated Cost**: $103.20/month

**Calculator Inputs**:
```
Service: Amazon API Gateway
Type: HTTP API
Requests: 60,000,000 per month
Data transfer out: 480 GB per month
Pricing tier: Tier 1 ($1.00 per million)
```

### Amazon VPC (Multi-AZ NAT)

#### NAT Gateway
- **Service**: Amazon VPC NAT Gateway
- **Gateways**: 2 (multi-AZ for high availability)
- **Runtime**: 1,460 hours/month (2 × 730)
- **Data Processing**: 5,000 GB/month
- **Estimated Cost**: $290.70/month

**Calculator Inputs**:
```
Service: Amazon VPC NAT Gateway
Number of gateways: 2
Hours: 1,460 per month (2 × 730)
Data processed: 5,000 GB per month
```

### Amazon CloudWatch (Enterprise Monitoring)

#### Monitoring and Logging
- **Service**: Amazon CloudWatch
- **Log Ingestion**: 500 GB/month
- **Custom Metrics**: 4,500 metrics
- **Log Storage**: 60 GB
- **CloudTrail Data Events**: 250,000,000 events
- **Dashboards**: 10 dashboards
- **Alarms**: 100 alarms
- **Estimated Cost**: $1,260/month

**Calculator Inputs**:
```
Service: Amazon CloudWatch
Log ingestion: 500 GB per month
Custom metrics: 4,500
Log storage: 60 GB
Data events: 250,000,000 per month
Dashboards: 10
Alarms: 100
```

### **Scale Scenario Total**: ~$226,890/month

---

## Network Cost Additions (All Scenarios)

**⚠️ IMPORTANT**: Based on the Network Cost Gap Analysis, add these estimated network costs to each scenario:

### Demo Scenario Network Additions
- **Lambda VPC Data Transfer**: +$2/month
- **Aurora Multi-AZ Transfer**: +$1/month
- **Cross-Service Communication**: +$1/month
- **Total Network Addition**: +$4/month

### Production Scenario Network Additions
- **Lambda VPC Data Transfer**: +$100/month
- **Aurora Multi-AZ Transfer**: +$55/month
- **Bedrock Data Transfer**: +$150/month
- **Cross-Service Communication**: +$45/month
- **Total Network Addition**: +$350/month

### Scale Scenario Network Additions
- **Lambda VPC Data Transfer**: +$1,000/month
- **Aurora Multi-AZ Transfer**: +$550/month
- **Bedrock Data Transfer**: +$1,500/month
- **Cross-Service Communication**: +$450/month
- **Total Network Addition**: +$3,500/month

---

## Summary Table

| Scenario | Base Estimate | Network Addition | **Total Estimate** |
|----------|---------------|------------------|-------------------|
| **Demo (1 User)** | $180/month | +$4/month | **$184/month** |
| **Production (10K MAU)** | $28,440/month | +$350/month | **$28,790/month** |
| **Scale (100K MAU)** | $226,890/month | +$3,500/month | **$230,390/month** |

---

## Calculator Usage Instructions

### Step 1: Access AWS Pricing Calculator
1. Go to https://calculator.aws/
2. Select "Create estimate"
3. Choose region: **us-east-1**

### Step 2: Add Services by Category
Add services in this order to match the calculator structure:

1. **Compute**: Lambda, Aurora
2. **Storage**: S3, ECR
3. **Database**: Aurora (if not added in Compute)
4. **Networking & Content Delivery**: API Gateway, Amplify, VPC
5. **Security, Identity & Compliance**: Cognito, KMS, Secrets Manager
6. **Machine Learning**: Bedrock (all services)
7. **Management & Governance**: CloudWatch, EventBridge

### Step 3: Input Values
- Copy the exact values from the scenario tables above
- Use the "Calculator Inputs" sections for each service
- Pay attention to units (per month, per GB, etc.)

### Step 4: Validate Results
- Compare calculator totals with the summary table
- Account for the network cost additions separately
- Note any discrepancies for further investigation

### Step 5: Save and Share
- Save the estimate with a descriptive name
- Export to PDF or share the link
- Document any assumptions or modifications made

---

## Key Assumptions Reference

**From**: `docs/costs_estimation/reports/assumptions_and_exclusions.md`

### Critical Assumptions
- **MAU Definition**: Monthly Active Users who authenticate at least once
- **Session Pattern**: 20 sessions/month per MAU (healthcare average)
- **AI Interaction Rate**: 10 interactions per session
- **Document Processing**: 2.5 documents/month per MAU, 8 pages average
- **Cache Hit Rate**: 60% baseline, 75% optimized
- **Batch Processing**: 80% baseline, 95% optimized

### Pricing Assumptions
- **Region**: us-east-1 (US East - N. Virginia)
- **Pricing Date**: October 2025
- **Model**: ON DEMAND pricing
- **Currency**: USD

### **[NEEDS REVIEW]** Items
- Bedrock model availability (Claude 3.5 vs 4.5 Haiku)
- Actual user behavior patterns
- Network data transfer volumes
- Document processing complexity distribution

---

## Optimization Notes

### Demo → Production Scaling Factors
- **Users**: 1 → 10,000 (10,000x)
- **Cost**: $184 → $28,790 (156x)
- **Cost per User**: $184 → $2.88 (98% efficiency gain)

### Production → Scale Scaling Factors
- **Users**: 10,000 → 100,000 (10x)
- **Cost**: $28,790 → $230,390 (8x)
- **Cost per User**: $2.88 → $2.30 (20% efficiency gain)

### Key Optimizations at Scale
1. **Provisioned Throughput**: 15% savings on Bedrock
2. **ARM64 Migration**: 20% savings on Lambda
3. **I/O Optimized Aurora**: Better performance per dollar
4. **Selective ASF**: 50% reduction in Cognito costs
5. **Optimized Caching**: 75% hit rate vs 60% baseline
6. **Batch Processing**: 95% vs 80% baseline

---

**Document Version**: 1.0  
**Last Updated**: October 28, 2025  
**Prepared By**: AWS Cost Estimation Team  
**Usage**: Input into AWS Pricing Calculator for validation

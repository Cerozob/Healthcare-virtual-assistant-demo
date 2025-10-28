# Assistant Stack Cost Report

**Report Date:** October 28, 2025  
**Region:** US East (N. Virginia)  
**Scenario:** Production deployment for 10,000 Monthly Active Users (MAU)  
**Pricing Model:** ON DEMAND  

## Executive Summary

The Assistant Stack represents the AI/ML components of the AWSomeBuilder2 healthcare management system, providing virtual assistant capabilities, document processing intelligence, and knowledge management. This stack accounts for the majority of the system's operational costs due to the intensive use of Amazon Bedrock services.

### Key Findings

- **Total Monthly Cost:** $18,579.74
- **Total Annual Cost:** $222,956.88
- **Cost per MAU:** $1.86/month
- **Cost per AI Interaction:** $0.93
- **Primary Cost Driver:** Bedrock Guardrails (32% of stack cost)

## Component Breakdown

### 1. Bedrock Foundation Models

**Service:** Amazon Bedrock Foundation Models  
**Purpose:** Core AI inference for virtual assistant interactions

#### Model Configuration
- **Primary Model:** Claude 3.5 Haiku (90% of interactions)
- **Secondary Model:** Claude 3.5 Sonnet (10% of interactions)
- **Total Interactions:** 2M/month (10K MAU × 20 sessions × 10 interactions)

**[CRITICAL REVIEW REQUIRED]** The original specification mentioned "Claude 4.5 Haiku" which does not exist in current AWS Bedrock offerings. This analysis uses Claude 3.5 Haiku as the closest available model.

#### Usage Patterns
- **Claude 3.5 Haiku (1.8M interactions):**
  - Average input: 2,000 tokens (medical context + query)
  - Average output: 800 tokens (detailed response)
  - Cache hit rate: 60%

- **Claude 3.5 Sonnet (200K interactions):**
  - Average input: 4,000 tokens (complex case analysis)
  - Average output: 1,500 tokens (comprehensive analysis)
  - Cache hit rate: 60%

#### Cost Calculation
```
Claude 3.5 Haiku:
- Input (new): 1.8M × 2K × 40% × $0.0008/1K = $1,152.00
- Input (cached): 1.8M × 2K × 60% × $0.0002/1K = $432.00
- Output: 1.8M × 800 × $0.0032/1K = $4,608.00
- Subtotal: $6,192.00

Claude 3.5 Sonnet:
- Input (new): 200K × 4K × 40% × $0.003/1K = $960.00
- Input (cached): 200K × 4K × 60% × $0.0006/1K = $288.00
- Output: 200K × 1.5K × $0.015/1K = $4,500.00
- Subtotal: $5,748.00

Total Foundation Models: $11,940.00/month
```

**Annual Cost:** $143,280.00

### 2. Bedrock Embeddings

**Service:** Amazon Bedrock Foundation Models (Embeddings)  
**Purpose:** Document vectorization for knowledge base and semantic search

#### Model Configuration
- **Model:** Titan Embeddings (search units pricing)
- **Documents:** 200,000 pages/month for embedding
- **Average Tokens:** 500 tokens per page
- **Total Volume:** 100M tokens/month

**[CRITICAL REVIEW REQUIRED]** The original specification mentioned "Titan Embeddings V2" which requires validation against current AWS Bedrock offerings.

#### Cost Calculation
```
Titan Embeddings:
- Total tokens: 100M tokens/month
- Search units: 100M ÷ 1,000 = 100,000 search units
- Cost: 100,000 × $0.002 = $200.00/month
```

**Annual Cost:** $2,400.00

### 3. Bedrock Knowledge Base

**Service:** Amazon Bedrock Knowledge Base  
**Purpose:** Managed RAG service for medical knowledge retrieval

#### Configuration
- **OCUs:** 2 OCUs (1 search + 1 indexing)
- **Vector Storage:** 50GB (included in OCU pricing)
- **Queries:** 2M queries/month
- **Runtime:** 24/7 operation (730 hours/month)

#### Cost Calculation
```
Knowledge Base:
- OCUs: 2 × 730 hours × $0.24/hour = $350.40/month
- Storage: Included in OCU pricing
- Queries: Included in OCU pricing
```

**Annual Cost:** $4,204.80

### 4. Bedrock Guardrails

**Service:** Amazon Bedrock Guardrails  
**Purpose:** Content filtering, PII detection, and responsible AI safeguards

#### Configuration
- **Policies Enabled:** Content Policy + PII Detection
- **Text Processing Volume:** 2M interactions × 3,000 tokens avg = 6B tokens
- **Text Units:** 6B tokens × 4 chars/token ÷ 1,000 chars/unit = 24M text units

#### Cost Calculation
```
Guardrails:
- Content Policy: 24M text units × $0.15/1K = $3,600.00
- PII Detection: 24M text units × $0.10/1K = $2,400.00
- Total: $6,000.00/month
```

**Annual Cost:** $72,000.00

### 5. Bedrock AgentCore

**Service:** Amazon Bedrock AgentCore  
**Purpose:** Managed runtime for multi-agent virtual assistant system

#### Configuration
- **Runtime:** 730 hours/month (always-on)
- **Compute:** 1 vCPU, 2GB RAM
- **Gateway Requests:** 2M requests/month
- **Data Transfer:** 50GB/month

#### Cost Calculation
```
AgentCore:
- vCPU: 1 × 730 hours × $0.0895 = $65.34
- Memory: 2GB × 730 hours × $0.00945 = $13.80
- Gateway: 2M × $0.000005 = $10.00
- Data Transfer: [NEEDS REVIEW - pricing not available]
- Total: $89.14/month (excluding data transfer)
```

**Annual Cost:** $1,069.68 (excluding data transfer)

### 6. Elastic Container Registry (ECR)

**Service:** Amazon ECR  
**Purpose:** Container image storage for AgentCore deployment

#### Configuration
- **Container Images:** 2GB agent container image
- **Storage Duration:** Continuous (monthly billing)
- **Data Transfer:** 10GB/month (deployments)

#### Cost Calculation
```
ECR:
- Storage: 2GB × $0.10/GB-month = $0.20
- Data Transfer: [NEEDS REVIEW - pricing not available]
- Total: $0.20/month (excluding data transfer)
```

**Annual Cost:** $2.40 (excluding data transfer)

## Cost Summary

### Monthly Breakdown

| Component | Monthly Cost | Percentage | Annual Cost |
|-----------|--------------|------------|-------------|
| Bedrock Foundation Models | $11,940.00 | 64.3% | $143,280.00 |
| Bedrock Guardrails | $6,000.00 | 32.3% | $72,000.00 |
| Bedrock Knowledge Base | $350.40 | 1.9% | $4,204.80 |
| Bedrock Embeddings | $200.00 | 1.1% | $2,400.00 |
| Bedrock AgentCore | $89.14 | 0.5% | $1,069.68 |
| ECR | $0.20 | <0.1% | $2.40 |
| **TOTAL** | **$18,579.74** | **100%** | **$222,956.88** |

### Key Metrics

- **Cost per MAU:** $1.86/month
- **Cost per AI Interaction:** $0.93 (based on 2M interactions/month)
- **Cost per Session:** $9.29 (based on 200K sessions/month)
- **Largest Cost Component:** Bedrock Foundation Models (64.3%)
- **Second Largest:** Bedrock Guardrails (32.3%)

## Usage Assumptions

### Foundation Models
- **Model Mix:** 90% Claude 3.5 Haiku, 10% Claude 3.5 Sonnet
- **Cache Hit Rate:** 60% for both models
- **Average Input Tokens:** 2,000 (Haiku), 4,000 (Sonnet)
- **Average Output Tokens:** 800 (Haiku), 1,500 (Sonnet)
- **Interaction Volume:** 2M interactions/month

### Guardrails
- **Policies:** Content Policy + PII Detection only
- **Text Processing:** All AI interactions processed
- **Average Text per Interaction:** 3,000 tokens (input + output)

### Knowledge Base
- **OCU Configuration:** Minimum 2 OCUs for production
- **Query Volume:** 2M queries/month
- **Storage:** 50GB vector storage

### AgentCore
- **Runtime:** 24/7 operation
- **Resource Allocation:** 1 vCPU, 2GB RAM
- **Gateway Usage:** 2M API requests/month

## Cost Optimization Opportunities

### High-Impact Optimizations

1. **Model Routing Optimization** (Potential Savings: $1,200-$2,400/month)
   - Increase Claude 3.5 Haiku usage from 90% to 95%
   - Implement more intelligent query classification
   - Reduce complex query routing to Sonnet

2. **Prompt Caching Enhancement** (Potential Savings: $800-$1,600/month)
   - Increase cache hit rate from 60% to 75%
   - Implement more aggressive medical knowledge caching
   - Optimize prompt structure for better cache utilization

3. **Guardrails Policy Optimization** (Potential Savings: $1,500-$3,000/month)
   - Implement selective policy application
   - Use client-side pre-filtering for obvious violations
   - Apply expensive policies only to sensitive content

### Medium-Impact Optimizations

1. **Provisioned Throughput** (Potential Savings: 20-30%)
   - Consider provisioned throughput for predictable workloads
   - Evaluate 1-month or 6-month commitments
   - Monitor usage patterns for optimization opportunities

2. **Batch Processing** (Potential Savings: $300-$600/month)
   - Implement batch processing for non-urgent queries
   - Use 50% discount for batch operations where applicable
   - Queue non-critical interactions for batch processing

3. **AgentCore Right-sizing** (Potential Savings: $20-$40/month)
   - Monitor actual vCPU and memory utilization
   - Optimize resource allocation based on usage patterns
   - Consider auto-scaling for variable workloads

### Low-Impact Optimizations

1. **ECR Lifecycle Policies** (Potential Savings: <$5/month)
   - Implement image lifecycle policies
   - Remove old container image versions
   - Optimize image layering and compression

## Scaling Analysis

### 50,000 MAU Scenario (5x Growth)

| Component | Current (10K MAU) | 50K MAU | Scaling Factor |
|-----------|-------------------|---------|----------------|
| Foundation Models | $11,940.00 | $59,700.00 | 5.0x |
| Guardrails | $6,000.00 | $30,000.00 | 5.0x |
| Knowledge Base | $350.40 | $1,051.20 | 3.0x |
| Embeddings | $200.00 | $1,000.00 | 5.0x |
| AgentCore | $89.14 | $267.42 | 3.0x |
| ECR | $0.20 | $0.20 | 1.0x |
| **TOTAL** | **$18,579.74** | **$92,018.82** | **4.95x** |

### 100,000 MAU Scenario (10x Growth)

| Component | Current (10K MAU) | 100K MAU | Scaling Factor |
|-----------|-------------------|----------|----------------|
| Foundation Models | $11,940.00 | $101,490.00 | 8.5x* |
| Guardrails | $6,000.00 | $60,000.00 | 10.0x |
| Knowledge Base | $350.40 | $1,752.00 | 5.0x |
| Embeddings | $200.00 | $2,000.00 | 10.0x |
| AgentCore | $89.14 | $445.70 | 5.0x |
| ECR | $0.20 | $0.20 | 1.0x |
| **TOTAL** | **$18,579.74** | **$165,687.90** | **8.92x** |

*Includes provisioned throughput optimization (15% discount)

## Risk Factors and Considerations

### High-Risk Factors

1. **Model Availability Changes**
   - Risk: Claude model versions may change or be deprecated
   - Mitigation: Monitor AWS Bedrock roadmap and model lifecycle

2. **Usage Pattern Variations**
   - Risk: Actual usage may differ significantly from assumptions
   - Mitigation: Implement comprehensive monitoring and alerting

3. **Pricing Changes**
   - Risk: AWS may adjust Bedrock pricing
   - Mitigation: Regular pricing reviews and budget adjustments

### Medium-Risk Factors

1. **Cache Hit Rate Variations**
   - Risk: Lower cache hit rates increase costs significantly
   - Mitigation: Optimize prompt engineering and caching strategies

2. **Guardrails Policy Requirements**
   - Risk: Compliance requirements may mandate additional policies
   - Mitigation: Budget for additional policy costs

### Low-Risk Factors

1. **Regional Availability**
   - Risk: Service availability in other regions
   - Mitigation: Multi-region deployment planning

## Monitoring and Alerting Recommendations

### Cost Monitoring

1. **Service-Level Budgets**
   - Bedrock Foundation Models: $13,000/month (alert at 90%)
   - Bedrock Guardrails: $6,500/month (alert at 90%)
   - Knowledge Base: $400/month (alert at 90%)
   - Other services: $300/month combined

2. **Usage Metrics**
   - Token usage per interaction (target: <3,000 tokens)
   - Cache hit rate (target: >60%)
   - Model routing efficiency (target: >90% Haiku usage)
   - Guardrails violation rates

3. **Performance Metrics**
   - Response latency (target: <2 seconds)
   - OCU utilization (target: 60-80%)
   - AgentCore resource utilization

### Alert Thresholds

- **Daily spend >$650** (110% of expected daily spend)
- **Token usage >3,500 per interaction** (significant efficiency degradation)
- **Cache hit rate <50%** (caching optimization needed)
- **Guardrails violation rate >5%** (content quality issues)

## Compliance and Security Considerations

### HIPAA Compliance
- All Bedrock services support HIPAA compliance
- Guardrails PII detection helps maintain patient privacy
- Encryption in transit and at rest for all components
- Audit logging through CloudTrail integration

### Data Residency
- All processing occurs in US East (N. Virginia)
- No cross-border data transfer for patient information
- Knowledge Base vectors stored in same region as source data

## Recommendations

### Immediate Actions (0-30 days)
1. **Implement comprehensive cost monitoring** with the recommended budgets and alerts
2. **Validate model names** - confirm Claude 3.5 Haiku vs Claude 4.5 Haiku availability
3. **Establish baseline metrics** for token usage, cache hit rates, and performance

### Short-term Actions (1-3 months)
1. **Optimize prompt caching** to achieve >70% cache hit rate
2. **Implement intelligent model routing** to increase Haiku usage to 95%
3. **Evaluate provisioned throughput** for predictable workloads

### Long-term Actions (3-12 months)
1. **Consider custom model fine-tuning** for healthcare-specific use cases
2. **Evaluate multi-region deployment** for disaster recovery and performance
3. **Implement advanced optimization strategies** based on usage patterns

## Conclusion

The Assistant Stack represents a significant investment in AI capabilities for the healthcare management system, with monthly costs of $18,579.74 for 10,000 MAU. The primary cost drivers are foundation model usage (64.3%) and guardrails processing (32.3%), both essential for providing high-quality, safe AI interactions in a healthcare context.

Key success factors for cost management include:
- Effective prompt engineering and caching strategies
- Intelligent model routing between Haiku and Sonnet
- Selective application of guardrails policies
- Continuous monitoring and optimization

The cost per AI interaction of $0.93 is reasonable for healthcare-grade AI services, considering the compliance requirements, safety measures, and sophisticated capabilities provided by the Amazon Bedrock platform.

---

**Report prepared by:** AWS Cost Estimation Analysis  
**Next review date:** November 28, 2025  
**Contact:** [NEEDS REVIEW - Add appropriate contact information]

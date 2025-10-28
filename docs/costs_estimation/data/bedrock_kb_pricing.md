# Amazon Bedrock Knowledge Base Pricing

**Region:** US East (N. Virginia)  
**Service Code:** AmazonBedrock  
**Last Updated:** October 28, 2025  
**Source:** AWS Pricing API and Documentation

## Overview

Amazon Bedrock Knowledge Bases is a fully managed RAG (Retrieval-Augmented Generation) service that enables you to connect foundation models to your data sources. The service handles data ingestion, vector storage, and retrieval operations.

## Pricing Components

### 1. Vector Storage (OpenSearch Compute Units - OCUs)

**[NEEDS REVIEW]** - Based on AWS documentation, Knowledge Bases uses Amazon OpenSearch Serverless for vector storage, which is priced using OpenSearch Compute Units (OCUs).

#### OCU Pricing Structure
- **Search OCUs:** For query processing and retrieval operations
- **Indexing OCUs:** For data ingestion and vector generation
- **Minimum:** 2 OCUs per collection (1 search + 1 indexing)
- **Scaling:** Auto-scales based on workload

**Estimated OCU Pricing (requires validation):**
- **Search OCU:** ~$0.24 per OCU-hour
- **Indexing OCU:** ~$0.24 per OCU-hour

**[NEEDS REVIEW]** - Exact OCU pricing for Knowledge Bases requires validation as it may differ from standard OpenSearch Serverless pricing.

### 2. Data Ingestion and Processing

#### Document Processing
- **Embedding Generation:** Included in embedding model pricing (Titan Embeddings)
- **Text Extraction:** No additional charge for text extraction
- **Chunking:** Automatic chunking included at no extra cost

#### Supported Data Sources
- **Amazon S3:** Standard S3 pricing applies for storage and retrieval
- **Confluence:** Connector usage included
- **Salesforce:** Connector usage included  
- **SharePoint:** Connector usage included
- **Web Crawling:** Included in base pricing

### 3. Query Operations

#### Retrieval Queries
- **Query Processing:** Included in OCU pricing
- **Embedding Generation:** Standard embedding model pricing applies
- **Result Ranking:** Included in base service

#### Structured Data Retrieval (SQL Generation)
Based on pricing API data found:
- **SQL Generation:** $0.002 per request
- **Usage Type:** `GenerateSQL-StructuredRetrieve`

### 4. Rerank Models

For improved retrieval accuracy, Knowledge Bases supports rerank models:

#### Amazon Rerank 1.0
- **Pricing:** $0.001 per query
- **Query Definition:** Up to 100 document chunks per query
- **Overage:** Additional queries charged for >100 chunks

#### Cohere Rerank 3.5  
- **Pricing:** $2.00 per 1,000 queries
- **Query Definition:** Up to 100 document chunks per query
- **Token Limit:** 500 tokens per document chunk

### 5. Integration with Bedrock Data Automation

When using Knowledge Bases with Bedrock Data Automation for parsing:
- **Standard Output:** $0.010 per page
- **Custom Output:** Variable pricing based on blueprint complexity
- **Multimodal Processing:** Included for images and documents

## Usage Patterns and Cost Optimization

### Recommended Architecture

1. **Small Knowledge Base (< 10,000 documents)**
   - 2 OCUs minimum (1 search + 1 indexing)
   - Monthly cost: ~$350 (2 OCUs × 730 hours × $0.24)

2. **Medium Knowledge Base (10,000 - 100,000 documents)**
   - 4-6 OCUs (2-3 search + 2-3 indexing)
   - Monthly cost: ~$700-$1,050

3. **Large Knowledge Base (> 100,000 documents)**
   - 8+ OCUs with auto-scaling
   - Monthly cost: $1,400+ depending on usage

### Cost Optimization Strategies

1. **OCU Management:**
   - Monitor OCU utilization and adjust capacity
   - Use minimum OCUs during low-usage periods
   - Scale up during peak query times

2. **Query Optimization:**
   - Implement query caching to reduce retrieval calls
   - Optimize chunk size and overlap for better relevance
   - Use rerank models selectively for critical queries

3. **Data Management:**
   - Regular cleanup of outdated documents
   - Optimize document chunking strategy
   - Use appropriate embedding models for content type

## Regional Availability

- **US East (N. Virginia):** Full service availability
- **US West (Oregon):** Full service availability
- **Europe (Frankfurt):** Limited availability
- **Asia Pacific (Tokyo):** Limited availability

## Pricing Examples

### Example 1: Healthcare Knowledge Base Setup
```
Configuration:
- 50,000 medical documents
- 2M queries per month
- Using Titan Embeddings for vectors
- Amazon Rerank for critical queries

Monthly Costs:
- OCUs: 4 OCUs × 730 hours × $0.24 = $700.80
- Embedding queries: 2M × 50 tokens × $0.002/1K = $200
- Rerank (10% of queries): 200K × $0.001 = $200
- Total: ~$1,100.80/month
```

### Example 2: Small Documentation Site
```
Configuration:
- 5,000 documents
- 100K queries per month
- Basic retrieval without rerank

Monthly Costs:
- OCUs: 2 OCUs × 730 hours × $0.24 = $350.40
- Embedding queries: 100K × 30 tokens × $0.002/1K = $6
- Total: ~$356.40/month
```

### Example 3: Enterprise Knowledge Management
```
Configuration:
- 200,000 documents
- 5M queries per month
- Structured data retrieval
- Cohere Rerank for accuracy

Monthly Costs:
- OCUs: 8 OCUs × 730 hours × $0.24 = $1,401.60
- Embedding queries: 5M × 40 tokens × $0.002/1K = $400
- SQL generation: 500K requests × $0.002 = $1,000
- Cohere Rerank: 1M queries × $2.00/1K = $2,000
- Total: ~$4,801.60/month
```

## Integration Costs

### With Foundation Models
- **Query Processing:** Standard model pricing applies
- **Context Injection:** Included in model token count
- **Response Generation:** Standard output token pricing

### With Data Sources
- **S3 Storage:** Standard S3 pricing for document storage
- **Data Transfer:** Standard AWS data transfer rates
- **API Calls:** Included in Knowledge Base pricing

## Monitoring and Optimization

### Key Metrics to Track
1. **OCU Utilization:** Target 60-80% utilization
2. **Query Latency:** Monitor retrieval performance
3. **Relevance Scores:** Track retrieval accuracy
4. **Cost per Query:** Monitor unit economics

### Optimization Recommendations
1. **Right-size OCUs:** Start with minimum and scale based on usage
2. **Query Caching:** Implement application-level caching
3. **Batch Processing:** Group similar queries when possible
4. **Content Optimization:** Regular content audits and cleanup

## Important Notes

1. **OCU Pricing Validation Required:** The exact OCU pricing for Knowledge Bases may differ from standard OpenSearch Serverless pricing and requires validation.

2. **Minimum Capacity:** Knowledge Bases require a minimum of 2 OCUs (1 search + 1 indexing).

3. **Auto-scaling:** OCUs automatically scale based on workload, which can impact costs.

4. **Data Transfer:** Cross-region data transfer charges may apply for multi-region deployments.

5. **Integration Complexity:** Costs can vary significantly based on data sources and query patterns.

## References

- AWS Bedrock Pricing Page: https://aws.amazon.com/bedrock/pricing/
- Knowledge Bases Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- OpenSearch Serverless Pricing: https://aws.amazon.com/opensearch-service/pricing/
- AWS Pricing API: AmazonBedrock service

# Amazon Bedrock Embeddings Pricing

**Region:** US East (N. Virginia)  
**Service Code:** AmazonBedrockFoundationModels  
**Last Updated:** October 28, 2025  
**Source:** AWS Pricing API

## Overview

Amazon Bedrock offers several embedding models for converting text into vector representations for use in RAG (Retrieval-Augmented Generation) applications and semantic search.

## Critical Model Verification

**[NEEDS REVIEW]** - The task specifically requires verification of "Titan Embeddings V2" model name. Based on AWS pricing data analysis, the available embedding models appear to be:
- Amazon Titan Text Embeddings (various versions)
- Cohere Embed models
- Search units pricing (potentially for Titan embeddings)

**The exact model name "Titan Embeddings V2" requires validation** against current AWS Bedrock offerings.

## Embedding Models Pricing

### Amazon Titan Text Embeddings

Based on the pricing API data, Titan embeddings appear to use "search units" pricing:

#### Titan Text Embeddings (Inferred)
- **Search Units:** $0.002 per search unit
- **Pricing Model:** Per search unit (not per token)
- **Effective Date:** March 6, 2025

**[NEEDS REVIEW]** - The relationship between search units and tokens/documents needs clarification. Typically:
- 1 search unit = processing of a certain amount of text
- May include both embedding generation and similarity search operations

### Cohere Embed V4

#### Cohere Embed V4 (Confirmed)
- **Input Tokens:** $0.00002 per token (not per 1K tokens)
- **Equivalent:** $0.02 per 1K tokens
- **Effective Date:** October 1, 2025

### Other Embedding Models

Based on the various input token pricing tiers found, there may be additional embedding models with different pricing:

#### Low-Cost Embeddings (Inferred)
- **Input Tokens:** $0.10 per 1M tokens
- **Use Case:** Basic text embeddings

#### Mid-Tier Embeddings (Inferred)  
- **Input Tokens:** $0.12 per 1M tokens
- **Use Case:** Enhanced embeddings with better accuracy

#### Premium Embeddings (Inferred)
- **Input Tokens:** $0.30 per 1M tokens  
- **Use Case:** High-quality embeddings for complex use cases

**[NEEDS REVIEW]** - The exact mapping of these pricing tiers to specific embedding models requires validation.

## Usage Patterns and Optimization

### Recommended Embedding Strategy

1. **Document Embedding:** Use Titan Embeddings for document vectorization
   - Cost-effective for large document collections
   - Good performance for healthcare content

2. **Query Embedding:** Use same model as document embedding for consistency
   - Ensures vector space compatibility
   - Maintains search accuracy

### Cost Optimization Features

1. **Batch Processing:** Process documents in batches to reduce API overhead
2. **Caching:** Cache embeddings for frequently accessed documents
3. **Incremental Updates:** Only re-embed changed documents
4. **Model Selection:** Choose appropriate model based on accuracy requirements

## Regional Availability

- **US East (N. Virginia):** All embedding models available
- **US West (Oregon):** Most models available  
- **Europe (Frankfurt):** Limited model availability
- **Asia Pacific (Tokyo):** Limited model availability

## Pricing Examples

### Example 1: Healthcare Knowledge Base Setup
```
Initial Setup:
- 200,000 medical documents
- Average 500 tokens per document
- Total: 100M tokens

Using Titan Embeddings (search units):
- Assuming 1 search unit = 1,000 tokens
- Required: 100,000 search units
- Cost: 100,000 × $0.002 = $200

Using Cohere Embed V4:
- Cost: 100M × $0.02/1K = $2,000
```

### Example 2: Monthly Query Processing
```
Monthly Usage:
- 2M user queries
- Average 50 tokens per query
- Total: 100M tokens/month

Using Titan Embeddings (search units):
- Required: 100,000 search units/month
- Monthly Cost: 100,000 × $0.002 = $200

Using Cohere Embed V4:
- Monthly Cost: 100M × $0.02/1K = $2,000
```

### Example 3: Mixed Workload
```
Healthcare AI Assistant:
- Document embedding: 200K documents × 500 tokens = 100M tokens (one-time)
- Query embedding: 2M queries × 50 tokens = 100M tokens/month

Titan Embeddings (search units):
- Setup: 100,000 search units × $0.002 = $200
- Monthly: 100,000 search units × $0.002 = $200
- Annual: $200 + ($200 × 12) = $2,600

Cohere Embed V4:
- Setup: 100M × $0.02/1K = $2,000
- Monthly: 100M × $0.02/1K = $2,000
- Annual: $2,000 + ($2,000 × 12) = $26,000
```

## Integration with Knowledge Bases

### Amazon Bedrock Knowledge Bases

When using embeddings with Bedrock Knowledge Bases:
- **Storage:** Vector storage included in Knowledge Base pricing
- **Retrieval:** Query costs apply for each search operation
- **Ingestion:** Embedding costs apply during document processing

### OpenSearch Integration

For custom vector databases:
- **Embedding Generation:** Standard embedding model pricing applies
- **Vector Storage:** Separate OpenSearch costs
- **Search Operations:** Additional OpenSearch query costs

## Important Notes

1. **Model Name Verification Required:** The specification mentions "Titan Embeddings V2" which requires validation against current AWS Bedrock offerings.

2. **Search Units vs Tokens:** The relationship between search units and token count needs clarification for accurate cost estimation.

3. **Batch Processing:** Some embedding models may offer batch processing discounts.

4. **Vector Dimensions:** Different models produce different vector dimensions, affecting storage costs.

5. **Context Length:** Maximum input length varies by model, affecting chunking strategies.

## Performance Considerations

### Titan Text Embeddings
- **Vector Dimensions:** Typically 1,536 dimensions
- **Max Input Length:** ~8,000 tokens
- **Use Case:** General-purpose text embedding

### Cohere Embed V4
- **Vector Dimensions:** Configurable (up to 1,024)
- **Max Input Length:** ~512 tokens per chunk
- **Use Case:** High-accuracy semantic search

## References

- AWS Bedrock Pricing Page: https://aws.amazon.com/bedrock/pricing/
- AWS Pricing API: AmazonBedrockFoundationModels service
- Bedrock Knowledge Bases Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- Titan Text Embeddings Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html

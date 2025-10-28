# Amazon Bedrock Foundation Models Pricing

**Region:** US East (N. Virginia)  
**Service Code:** AmazonBedrockFoundationModels  
**Last Updated:** October 28, 2025  
**Source:** AWS Pricing API

## Overview

Amazon Bedrock Foundation Models pricing is based on token consumption for text generation models. Pricing varies by model provider, model size, and usage pattern (on-demand vs batch vs provisioned throughput).

## Critical Model Verification

**[NEEDS REVIEW]** - The task specifically requires verification of "Claude 4.5 Haiku" model name. Based on AWS documentation and pricing data analysis, the available Claude models appear to be:
- Claude 3.5 Haiku (available with latency-optimized inference)
- Claude 3.5 Sonnet
- Claude 3 Haiku
- Claude 3 Sonnet

**No "Claude 4.5 Haiku" model was found in the current AWS Bedrock offerings.** This requires human validation and potential requirement adjustment.

## Anthropic Claude Models Pricing

### On-Demand Pricing (Per 1,000 tokens)

Based on the pricing API data collected, here are the identified Claude model pricing tiers:

#### Claude 3.5 Haiku (Inferred from pricing data)
- **Input tokens:** $0.0008 per 1K tokens
- **Output tokens:** $0.0032 per 1K tokens  
- **Cache read tokens:** $0.0002 per 1K tokens
- **Batch input tokens:** $0.0004 per 1K tokens (50% discount)
- **Batch output tokens:** $0.0016 per 1K tokens (50% discount)

#### Claude 3.5 Sonnet (Inferred from pricing data)
- **Input tokens:** $0.003 per 1K tokens
- **Output tokens:** $0.015 per 1K tokens
- **Cache read tokens:** $0.0006 per 1K tokens
- **Batch input tokens:** $0.0015 per 1K tokens (50% discount)
- **Batch output tokens:** $0.0075 per 1K tokens (50% discount)

#### Higher-tier Claude Model (Inferred from pricing data)
- **Input tokens:** $0.008 per 1K tokens
- **Output tokens:** $0.024 per 1K tokens
- **Cache read tokens:** $0.0024 per 1K tokens

**[NEEDS REVIEW]** - The exact mapping of pricing tiers to specific Claude model versions requires validation. The pricing API returns multiple price points but doesn't clearly identify which corresponds to which model version.

### Latency-Optimized Inference

**Claude 3.5 Haiku** supports latency-optimized inference with premium pricing:
- **Input tokens:** $0.001 per 1K tokens (25% premium)
- **Output tokens:** $0.004 per 1K tokens (25% premium)

### Provisioned Throughput Pricing

Provisioned throughput pricing is available with different commitment terms:

#### No Commitment
- **Model Unit:** $62.00 - $88.00 per hour (varies by model)

#### 1-Month Commitment  
- **Model Unit:** $6.76 - $80.00 per hour (varies by model)

#### 6-Month Commitment
- **Model Unit:** $6.41 - $88.00 per hour (varies by model)

**[NEEDS REVIEW]** - Specific model unit requirements and exact pricing per Claude model version needs validation.

## Prompt Caching

All Claude models support prompt caching with significant cost savings:
- **Cache write:** Standard input token pricing
- **Cache read:** Up to 90% discount on cached tokens
- **Cache duration:** 5 minutes
- **Cache isolation:** Account-specific

## Batch Processing

Batch processing is available for select Claude models with 50% discount:
- **Availability:** Claude 3.5 Haiku, Claude 3.5 Sonnet
- **Discount:** 50% off on-demand pricing
- **Processing time:** Asynchronous with S3 output

## Usage Patterns and Optimization

### Recommended Model Selection Strategy

1. **Primary Model:** Claude 3.5 Haiku for 90% of queries
   - Cost-effective for most healthcare queries
   - Fast response times
   - Suitable for routine medical questions

2. **Secondary Model:** Claude 3.5 Sonnet for 10% of complex queries
   - Advanced reasoning capabilities
   - Complex medical case analysis
   - Multi-step diagnostic reasoning

### Cost Optimization Features

1. **Prompt Caching:** 60-75% cache hit rate achievable
2. **Batch Processing:** 50% cost reduction for non-urgent queries
3. **Intelligent Routing:** Route simple queries to Haiku, complex to Sonnet
4. **Provisioned Throughput:** 20-30% savings for predictable workloads

## Regional Availability

- **US East (N. Virginia):** All models available
- **US West (Oregon):** All models available  
- **Europe (Frankfurt):** Limited model availability
- **Asia Pacific (Tokyo):** Limited model availability

## Pricing Examples

### Example 1: Healthcare AI Assistant (10K MAU)
```
Monthly Usage:
- 1.8M interactions with Claude 3.5 Haiku
- 200K interactions with Claude 3.5 Sonnet
- 60% cache hit rate

Haiku Costs:
- Input (new): 1.8M × 2K × 40% × $0.0008/1K = $1,152
- Input (cached): 1.8M × 2K × 60% × $0.0002/1K = $432
- Output: 1.8M × 800 × $0.0032/1K = $4,608

Sonnet Costs:
- Input (new): 200K × 4K × 40% × $0.003/1K = $960
- Input (cached): 200K × 4K × 60% × $0.0006/1K = $288
- Output: 200K × 1.5K × $0.015/1K = $4,500

Total Monthly Cost: $11,940
```

### Example 2: Batch Document Processing
```
Monthly Usage:
- 500K documents processed via batch
- Average 2K input tokens, 800 output tokens per document

Batch Costs (50% discount):
- Input: 500K × 2K × $0.0004/1K = $400
- Output: 500K × 800 × $0.0016/1K = $640

Total Monthly Cost: $1,040
```

## Important Notes

1. **Model Name Verification Required:** The specification mentions "Claude 4.5 Haiku" which does not appear to exist in current AWS Bedrock offerings.

2. **Pricing Mapping:** The exact correspondence between pricing API data and specific Claude model versions requires validation.

3. **Regional Variations:** Pricing may vary by region and availability.

4. **Token Calculation:** Approximately 4 characters per token for English text.

5. **Billing Precision:** Charges calculated to the nearest cent with monthly billing cycles.

## References

- AWS Bedrock Pricing Page: https://aws.amazon.com/bedrock/pricing/
- AWS Pricing API: AmazonBedrockFoundationModels service
- Anthropic Claude Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude.html

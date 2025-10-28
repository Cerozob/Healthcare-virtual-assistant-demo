# Amazon Bedrock AgentCore Pricing

## Overview

Amazon Bedrock AgentCore provides a serverless platform for deploying and scaling AI agents with built-in tools and services. Pricing is consumption-based across multiple components including runtime, memory, gateway services, code interpreter, browser tools, and persistent memory.

**Region**: US East (N. Virginia) - us-east-1  
**Pricing Model**: ON DEMAND  
**Last Updated**: October 2025

## Core Runtime Services

### Runtime Compute
- **vCPU**: $0.0895 per vCPU-Hour
- **Memory**: $0.00945 per GB-Hour

### Gateway Services
- **API Invocations**: $0.000005 per invocation
- **Search API**: $0.000025 per invocation
- **Tool Indexing**: $0.0002 per ToolIndex-Month

## Agent Tools and Services

### Code Interpreter
- **vCPU**: $0.0895 per vCPU-Hour
- **Memory**: $0.00945 per GB-Hour

### Browser Tool
- **vCPU**: $0.0895 per vCPU-Hour
- **Memory**: $0.00945 per GB-Hour

## Memory Services

### Short-Term Memory
- **Events**: $0.00025 per event

### Long-Term Memory Storage
- **Built-in Memory**: $0.00075 per MemoryStored-Month
- **Custom Memory**: $0.00025 per MemoryStored-Month

### Long-Term Memory Retrieval
- **Memory Retrieved**: $0.0005 per memory retrieval operation

## Pricing Examples

### Basic Agent Runtime (1 vCPU, 2GB RAM, 24/7)
```
Monthly Cost:
- vCPU: 1 × 730 hours × $0.0895 = $65.34
- Memory: 2GB × 730 hours × $0.00945 = $13.80
- Total: $79.14/month
```

### API Gateway Usage (2M requests/month)
```
Monthly Cost:
- API Invocations: 2,000,000 × $0.000005 = $10.00
- Search API (10% of requests): 200,000 × $0.000025 = $5.00
- Total: $15.00/month
```

### Memory Services (Healthcare Use Case)
```
Monthly Cost:
- Short-term memory: 2M events × $0.00025 = $500.00
- Built-in memory storage: 10GB × $0.00075 = $0.0075
- Custom memory storage: 50GB × $0.00025 = $0.0125
- Memory retrievals: 500K × $0.0005 = $250.00
- Total: $750.02/month
```

## Cost Optimization Strategies

### Runtime Optimization
1. **Right-sizing**: Monitor vCPU and memory utilization to optimize resource allocation
2. **Auto-scaling**: Use consumption-based pricing to scale resources based on demand
3. **Efficient Code**: Optimize agent code to reduce compute time and memory usage

### Memory Optimization
1. **Memory Type Selection**: Use custom memory ($0.00025) instead of built-in memory ($0.00075) when possible
2. **Retrieval Patterns**: Optimize memory retrieval frequency to reduce costs
3. **Event Batching**: Batch short-term memory events to reduce per-event costs

### Gateway Optimization
1. **API Caching**: Implement caching to reduce API invocation costs
2. **Search Optimization**: Optimize search queries to reduce Search API usage
3. **Tool Indexing**: Minimize tool index updates to reduce indexing costs

## Healthcare-Specific Considerations

### Compliance and Security
- All AgentCore services support encryption in transit and at rest
- Memory services provide secure storage for patient data and medical context
- Gateway services include built-in security features for healthcare compliance

### Typical Usage Patterns
- **Patient Interactions**: High API invocation volume during business hours
- **Medical Context**: Significant long-term memory storage for patient history
- **Code Execution**: Moderate code interpreter usage for medical calculations
- **Document Processing**: Browser tool usage for medical document analysis

## Important Notes

1. **[NEEDS REVIEW]** Pricing effective as of September 2025 - verify current rates
2. **[NEEDS REVIEW]** Data transfer costs between AgentCore and other AWS services not included
3. **[NEEDS REVIEW]** Volume discounts may be available for enterprise usage
4. **[NEEDS REVIEW]** Regional pricing variations should be considered for multi-region deployments
5. **[NEEDS REVIEW]** Integration costs with other Bedrock services (models, knowledge bases) are separate

## Related Services

- **Bedrock Foundation Models**: Required for AI agent capabilities
- **Bedrock Knowledge Base**: Often used with AgentCore for RAG applications
- **Bedrock Guardrails**: Recommended for healthcare compliance
- **Amazon S3**: For storing agent artifacts and logs
- **Amazon CloudWatch**: For monitoring and logging AgentCore usage

## References

- AWS Bedrock AgentCore Documentation
- AWS Pricing Calculator
- Bedrock AgentCore Best Practices Guide

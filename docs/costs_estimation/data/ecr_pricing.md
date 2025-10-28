# Amazon Elastic Container Registry (ECR) Pricing

## Overview

Amazon Elastic Container Registry (ECR) is a fully managed Docker container registry that makes it easy to store, manage, and deploy Docker container images. ECR pricing is based on storage usage and data transfer.

**Region**: US East (N. Virginia) - us-east-1  
**Pricing Model**: ON DEMAND  
**Last Updated**: October 2025

## Storage Pricing

### Container Image Storage
- **Standard Storage**: $0.10 per GB-month
- **Storage Type**: Amazon S3 backend
- **Billing**: Prorated hourly based on actual usage

## Data Transfer Pricing

### Standard Data Transfer
- **[NEEDS REVIEW]** Data transfer pricing follows standard AWS data transfer rates
- **[NEEDS REVIEW]** Inbound data transfer: Typically free
- **[NEEDS REVIEW]** Outbound data transfer: Varies by destination and volume

### Enhanced Security (Dual-Layer Server-Side Encryption)
- **Encryption/Decryption**: $0.0036 per GB (GovCloud regions only)
- **[NEEDS REVIEW]** Standard region encryption costs not available in pricing API

## Free Tier

### AWS Free Tier Benefits
- **[NEEDS REVIEW]** 500 MB-month of storage for one year (new AWS accounts)
- **[NEEDS REVIEW]** Verify current free tier limits

## Pricing Examples

### Small Development Project (2GB container image)
```
Monthly Cost:
- Storage: 2GB × $0.10 = $0.20/month
- Data transfer: Minimal for development use
- Total: ~$0.20/month
```

### Medium Production Application (10GB total images)
```
Monthly Cost:
- Storage: 10GB × $0.10 = $1.00/month
- Data transfer: Depends on deployment frequency and image pulls
- Total: ~$1.00/month + data transfer
```

### Large Enterprise (100GB container registry)
```
Monthly Cost:
- Storage: 100GB × $0.10 = $10.00/month
- Data transfer: Significant for frequent deployments
- Total: ~$10.00/month + data transfer
```

### Healthcare Agent Container (2GB image, frequent deployments)
```
Monthly Cost:
- Storage: 2GB × $0.10 = $0.20/month
- Estimated data transfer: 10GB/month × [NEEDS REVIEW: data transfer rate]
- Total: $0.20/month + data transfer costs
```

## Cost Optimization Strategies

### Storage Optimization
1. **Image Layering**: Use efficient Docker layering to minimize storage
2. **Multi-stage Builds**: Reduce final image size with multi-stage builds
3. **Base Image Selection**: Choose minimal base images (Alpine, distroless)
4. **Lifecycle Policies**: Implement lifecycle policies to delete old images

### Data Transfer Optimization
1. **Regional Deployment**: Deploy ECR in same region as compute resources
2. **VPC Endpoints**: Use VPC endpoints to avoid internet data transfer charges
3. **Image Caching**: Implement image caching strategies in deployment pipelines
4. **Compression**: Use image compression techniques

### Repository Management
1. **Repository Consolidation**: Consolidate related images in fewer repositories
2. **Tag Management**: Use consistent tagging strategies to avoid duplicate images
3. **Scanning Optimization**: Use image scanning efficiently to avoid unnecessary costs

## Healthcare-Specific Considerations

### Compliance and Security
- ECR supports encryption at rest and in transit
- Integration with AWS IAM for fine-grained access control
- Vulnerability scanning for container security
- Audit logging through AWS CloudTrail

### Typical Usage Patterns
- **Agent Containers**: Store AI agent container images (typically 1-5GB each)
- **Microservices**: Store healthcare application microservice images
- **ML Models**: Store containerized machine learning models
- **Development**: Store development and testing container images

## Integration Costs

### Related AWS Services
- **Amazon ECS/EKS**: Container orchestration services that pull from ECR
- **AWS Lambda**: Container image support for Lambda functions
- **AWS Fargate**: Serverless container compute that uses ECR images
- **AWS CodeBuild**: CI/CD service that can push to ECR

## Important Notes

1. **[NEEDS REVIEW]** Pricing effective as of October 2025 - verify current rates
2. **[NEEDS REVIEW]** Data transfer costs depend on usage patterns and destinations
3. **[NEEDS REVIEW]** Volume discounts may be available for enterprise usage
4. **[NEEDS REVIEW]** Cross-region replication costs are additional
5. **[NEEDS REVIEW]** Image scanning costs may apply for vulnerability scanning
6. **[NEEDS REVIEW]** Private registry costs differ from public ECR pricing

## Monitoring and Billing

### Cost Tracking
- Use AWS Cost Explorer to track ECR storage and data transfer costs
- Set up billing alerts for unexpected usage spikes
- Monitor repository sizes and growth trends
- Track data transfer patterns by region and service

### Metrics to Monitor
- **Storage Usage**: GB-months of storage consumed
- **Data Transfer**: GB of data transferred in/out
- **Repository Count**: Number of repositories maintained
- **Image Pull Frequency**: How often images are downloaded

## References

- AWS ECR Pricing Page
- AWS Data Transfer Pricing
- ECR Best Practices Guide
- Container Image Optimization Guide

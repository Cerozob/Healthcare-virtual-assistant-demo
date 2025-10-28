# Amazon S3 Pricing Data (US East - N. Virginia)

**Source**: AWS Pricing API  
**Region**: us-east-1 (US East - N. Virginia)  
**Date Retrieved**: October 28, 2025  
**Service Code**: AmazonS3

## Storage Pricing

### Standard Storage (General Purpose)
- **First 50 TB/month**: $0.023 per GB-month
- **Next 450 TB/month**: $0.022 per GB-month  
- **Over 500 TB/month**: $0.021 per GB-month

### Standard-IA (Infrequent Access)
- **All tiers**: $0.0125 per GB-month

### One Zone-IA (Infrequent Access)
- **All tiers**: $0.01 per GB-month

### Glacier Instant Retrieval
- **All tiers**: $0.004 per GB-month

### Intelligent Tiering
- **Frequent Access Tier**: 
  - First 50 TB/month: $0.023 per GB-month
  - Next 450 TB/month: $0.022 per GB-month
  - Over 500 TB/month: $0.021 per GB-month
- **Infrequent Access Tier**: $0.0125 per GB-month
- **Archive Instant Access Tier**: $0.004 per GB-month
- **Archive Access Tier**: $0.0036 per GB-month
- **Deep Archive Access Tier**: $0.00099 per GB-month
- **Monitoring Fee**: $0.0025 per 1,000 objects monitored

## Request Pricing

### PUT, COPY, POST, LIST Requests (Tier 1)
- **Price**: $0.005 per 1,000 requests
- **Unit**: Per 1,000 requests

### GET and Other Requests (Tier 2)  
- **Price**: $0.0004 per 1,000 requests
- **Unit**: Per 1,000 requests
- **Note**: This is $0.004 per 10,000 requests

## Data Transfer Pricing

**[NEEDS REVIEW]** - Data transfer pricing not found in S3 service pricing. This is typically handled by:
- CloudFront for CDN distribution
- EC2 data transfer pricing for general internet egress
- Standard AWS data transfer rates apply:
  - First 1 GB/month: Free
  - Next 9.999 TB/month: ~$0.09 per GB
  - Next 40 TB/month: ~$0.085 per GB
  - Next 100 TB/month: ~$0.07 per GB
  - Over 150 TB/month: ~$0.05 per GB

## Cross-Region Replication Pricing

**[NEEDS REVIEW]** - Cross-region replication pricing not explicitly found in API results. Typically includes:
- Storage costs in destination region
- Request costs for replication
- Data transfer costs between regions

## Lifecycle Transition Pricing

**[NEEDS REVIEW]** - Lifecycle transition pricing not found in API results. Typical transitions:
- Standard to Standard-IA: $0.01 per 1,000 objects
- Standard to Glacier: $0.05 per 1,000 objects
- Standard to Deep Archive: $0.05 per 1,000 objects

## Additional Features

### Versioning
- **Cost**: Same as storage pricing for each version
- **Note**: Each object version is billed separately

### Access Logging
- **Cost**: Standard storage and request pricing applies to log files
- **Note**: No additional charges for enabling access logging

### Inventory
- **[NEEDS REVIEW]** - Inventory pricing not found in API results

### Analytics
- **[NEEDS REVIEW]** - Analytics pricing not found in API results

## Notes and Assumptions

1. **Pricing Effective Date**: October 1, 2025
2. **Currency**: USD
3. **Billing Period**: Monthly
4. **Minimum Storage Duration**: 
   - Standard-IA: 30 days minimum
   - Glacier Instant Retrieval: 90 days minimum
5. **Minimum Object Size**:
   - Standard-IA: 128 KB minimum billable size
   - Glacier Instant Retrieval: 128 KB minimum billable size

## Missing Data Requiring Review

The following pricing components were not found in the API results and require manual verification:

1. **Data Transfer Out to Internet**: Standard AWS data transfer rates apply
2. **Cross-Region Replication**: Includes storage, requests, and data transfer costs
3. **Lifecycle Transitions**: Per-object transition fees
4. **S3 Inventory**: Monthly inventory report generation costs
5. **S3 Analytics**: Storage class analysis costs
6. **S3 Select**: Query-in-place pricing
7. **S3 Batch Operations**: Bulk operation pricing
8. **S3 Object Lambda**: Transformation request pricing

## Validation Required

**[NEEDS REVIEW]** The following items require human validation:
- Data transfer pricing methodology and rates
- Cross-region replication cost structure
- Lifecycle transition fees
- Additional feature pricing not captured in API results
- Minimum storage duration and object size requirements
- Free tier allowances and limitations

## API Query Details

- **Service Code**: AmazonS3
- **Filters Applied**: 
  - Storage classes: General Purpose, Infrequent Access, Archive Instant Retrieval, Intelligent-Tiering
  - Request types: Tier1 (PUT/POST/COPY/LIST), Tier2 (GET/other)
  - Location: US East (N. Virginia)
- **Output Options**: OnDemand pricing terms only
- **Date Retrieved**: October 28, 2025

# Amazon Bedrock Data Automation (BDA) Pricing Data (US East - N. Virginia)

**Source**: AWS Pricing API  
**Region**: us-east-1 (US East - N. Virginia)  
**Date Retrieved**: October 28, 2025  
**Service Code**: AmazonBedrock  
**Operation**: InvokeDataAutomationAsync

## Document Processing (Pages)

### Standard Output
- **Price**: $0.01 per page processed
- **Use Case**: Basic document extraction with standard fields
- **Included Fields**: Up to 30 fields per page

### Custom Output
- **Price**: $0.04 per page processed
- **Use Case**: Advanced document extraction with custom schemas
- **Included Fields**: Up to 30 fields per page
- **Additional Fields**: $0.0005 per field above 30 fields per page

## Image Processing

### Standard Output
- **Price**: $0.003 per image processed
- **Use Case**: Basic image analysis and text extraction
- **Included Fields**: Up to 30 fields per image

### Custom Output
- **Price**: $0.005 per image processed
- **Use Case**: Advanced image analysis with custom extraction
- **Included Fields**: Up to 30 fields per image
- **Additional Fields**: $0.0005 per field above 30 fields per image

## Audio Processing

### Standard Output
- **Price**: $0.006 per minute processed
- **Use Case**: Basic audio transcription and analysis
- **Included Fields**: Up to 30 fields per minute

### Custom Output
- **Price**: $0.009 per minute processed
- **Use Case**: Advanced audio analysis with custom extraction
- **Included Fields**: Up to 30 fields per minute
- **Additional Fields**: $0.0005 per field above 30 fields per minute

## Video Processing

### Standard Output
- **Price**: $0.05 per minute processed
- **Use Case**: Basic video analysis and content extraction
- **Included Fields**: Up to 30 fields per minute

### Custom Output
- **Price**: $0.084 per minute processed
- **Use Case**: Advanced video analysis with custom extraction
- **Included Fields**: Up to 30 fields per minute
- **Additional Fields**: $0.0005 per field above 30 fields per minute

## Pricing Comparison: Standard vs Custom

| Content Type | Standard Output | Custom Output | Premium |
|--------------|----------------|---------------|---------|
| **Documents** | $0.01/page | $0.04/page | 4x |
| **Images** | $0.003/image | $0.005/image | 1.67x |
| **Audio** | $0.006/minute | $0.009/minute | 1.5x |
| **Video** | $0.05/minute | $0.084/minute | 1.68x |

## Additional Field Pricing

All content types have the same additional field pricing structure:
- **Included Fields**: 30 fields per unit (page/image/minute)
- **Additional Fields**: $0.0005 per field above 30 fields
- **Billing Unit**: Per page, per image, or per minute depending on content type

## Batch Processing Discounts

**[NEEDS REVIEW]** - Batch processing discounts not found in API results. Typically:
- Volume discounts may apply for large batch jobs
- Asynchronous processing may have different pricing tiers
- Enterprise customers may have negotiated rates

## Use Case Pricing Examples

### Healthcare Document Processing (Production Estimate)
Based on task requirements for medical document processing:

**Scenario**: 25,000 documents/month, 8 pages average, custom output
- **Documents**: 25,000 documents × 8 pages = 200,000 pages
- **Standard Processing**: 200,000 pages × $0.01 = $2,000/month
- **Custom Processing**: 200,000 pages × $0.04 = $8,000/month

### Medical Audio Processing
**Scenario**: 5,000 audio files/month, 15 minutes average, standard output
- **Audio Processing**: 5,000 files × 15 minutes × $0.006 = $450/month
- **With Custom Output**: 5,000 files × 15 minutes × $0.009 = $675/month

### Medical Video Processing
**Scenario**: 200 video files/month, 10 minutes average, standard output
- **Video Processing**: 200 files × 10 minutes × $0.05 = $100/month
- **With Custom Output**: 200 files × 10 minutes × $0.084 = $168/month

### Combined Healthcare Workflow (Monthly)
- **Documents**: 200,000 pages × $0.04 = $8,000
- **Audio**: 75,000 minutes × $0.006 = $450
- **Video**: 2,000 minutes × $0.05 = $100
- **Total**: $8,550/month

## Field Optimization Strategies

### Standard Output (30 fields included)
- Ideal for basic extraction needs
- Cost-effective for simple document types
- Suitable for standardized forms and documents

### Custom Output with Field Management
- Monitor field usage to optimize costs
- Design schemas to stay within 30-field limit when possible
- Additional fields cost $0.0005 each, so 100 extra fields = $0.05 per unit

### Field Cost Impact Examples
- **50 fields per page**: Base cost + (20 × $0.0005) = Base + $0.01
- **100 fields per page**: Base cost + (70 × $0.0005) = Base + $0.035
- **200 fields per page**: Base cost + (170 × $0.0005) = Base + $0.085

## Processing Mode Considerations

### Real-time Processing
- Immediate results for urgent medical documents
- Standard pricing applies
- Higher priority in processing queue

### Batch Processing
- **[NEEDS REVIEW]** - Potential discounts for batch jobs
- Lower priority processing
- Suitable for historical document processing
- May offer 10-20% cost savings (requires validation)

## Content Type Optimization

### Most Cost-Effective: Images
- $0.003 per image (standard) or $0.005 (custom)
- Best for simple forms, receipts, single-page documents

### Moderate Cost: Documents and Audio
- Documents: $0.01-$0.04 per page
- Audio: $0.006-$0.009 per minute
- Good balance of cost and information density

### Highest Cost: Video
- $0.05-$0.084 per minute
- Most expensive but provides rich multimodal content
- Consider if video analysis is essential

## Notes and Assumptions

1. **Pricing Effective Date**: October 28, 2025
2. **Currency**: USD
3. **Billing Period**: Per unit processed (page/image/minute)
4. **Field Limit**: 30 fields included in base price
5. **Processing Type**: Asynchronous processing via InvokeDataAutomationAsync
6. **Output Format**: JSON structured data extraction

## Missing Data Requiring Review

The following pricing components were not found in the API results and require manual verification:

1. **Batch Processing Discounts**: Volume discounts for large batch jobs
2. **Real-time vs Batch Pricing**: Different pricing tiers for processing priority
3. **Data Transfer Costs**: Costs for input/output data transfer
4. **Storage Costs**: Temporary storage during processing
5. **Failed Processing Charges**: Whether failed jobs incur charges
6. **Enterprise Pricing**: Volume discounts for enterprise customers

## Validation Required

**[NEEDS REVIEW]** The following items require human validation:
- Batch processing discount rates and thresholds
- Real-time processing premium charges
- Data transfer and storage costs during processing
- Failed job billing policies
- Enterprise volume discount structures
- Integration costs with other AWS services

## Healthcare-Specific Considerations

### HIPAA Compliance
- BDA supports HIPAA-compliant processing
- No additional charges for HIPAA compliance
- Encryption and audit logging included

### Medical Document Types
- **Lab Reports**: Typically 1-2 pages, standard output sufficient
- **Medical Records**: 5-15 pages, may require custom output
- **Insurance Forms**: Standardized, standard output recommended
- **Radiology Reports**: 2-5 pages, custom output for structured data

### Processing Volume Planning
- **Peak Processing**: Consider batch processing for cost optimization
- **Real-time Needs**: Emergency documents may require immediate processing
- **Archive Processing**: Historical documents suitable for batch processing

## API Query Details

- **Service Code**: AmazonBedrock
- **Filters Applied**: 
  - Usage Type: Contains "DataAutomation"
  - Location: US East (N. Virginia)
  - Operation: InvokeDataAutomationAsync
- **Output Options**: OnDemand pricing terms only
- **Product Family**: Amazon Bedrock
- **Date Retrieved**: October 28, 2025

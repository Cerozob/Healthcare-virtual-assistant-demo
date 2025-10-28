# AWS Amplify Pricing - US East (N. Virginia)

**Region**: us-east-1  
**Service Code**: AWSAmplify  
**Data Retrieved**: 2025-06-20  
**Pricing Effective Date**: 2025-05-01

## Pricing Components

### 1. Build Minutes

Build compute pricing varies by instance size:

| Instance Type | vCPU | Memory | Price per Minute | Use Case |
|---------------|------|--------|------------------|----------|
| **Standard8GB** | 4 | 7 GB | **$0.01** | Standard builds (default) |
| Large16GB | 8 | 15 GB | $0.025 | Large projects |
| Xlarge72GB | 32 | 72 GB | $0.10 | Very large monorepos |

**Production Assumption**: Using Standard8GB instance type for typical React/Vite builds.

---

### 2. Hosting Compute

Amplify Hosting uses serverless compute for SSR and dynamic content:

| Component | Unit | Price | Description |
|-----------|------|-------|-------------|
| **Request Count** | Per 1M requests | **$0.30** | HTTP requests served |
| **Request Duration** | Per GB-Hour | **$0.20** | Compute time (GB-seconds × $0.0000555556) |

**Note**: For static sites (like our React SPA), request duration is minimal or zero.

---

### 3. Data Transfer Out

| Component | Unit | Price | Notes |
|-----------|------|-------|-------|
| **Data Transfer Out** | Per GB | **$0.15** | Data served to users |

**CDN Integration**: Amplify includes CloudFront CDN automatically. Pricing includes CDN delivery.

---

### 4. Storage

| Component | Unit | Price | Description |
|-----------|------|-------|-------------|
| **Build Artifacts** | Per GB-month | **$0.023** | Stored build outputs |

---

### 5. Optional Features

| Feature | Unit | Price | Notes |
|---------|------|-------|-------|
| **WAF Integration** | Per month | **$15.00** | AWS WAF for Amplify Hosting |

**[NEEDS REVIEW]**: Confirm if WAF is required for production deployment.

---

## Free Tier

AWS Amplify includes a free tier:
- **Build minutes**: 1,000 minutes/month
- **Hosting**: 15 GB served/month
- **Storage**: 5 GB stored/month

**[NEEDS REVIEW]**: Confirm if free tier applies to production accounts or only new accounts.

---

## Production Usage Assumptions (10K MAU)

### Build Usage
- **Build frequency**: 10 builds/month (CI/CD deployments)
- **Build duration**: 15 minutes per build (React + Vite)
- **Instance type**: Standard8GB (4 vCPU, 7 GB)
- **Total build minutes**: 150 minutes/month

**[NEEDS REVIEW]**: Validate build frequency and duration against actual CI/CD patterns.

### Hosting Usage
- **Monthly Active Users (MAU)**: 10,000 users
- **Sessions per user**: 20 sessions/month
- **Pages per session**: 15 pages
- **Total requests**: 10,000 × 20 × 15 = **3,000,000 requests/month**

**[NEEDS REVIEW]**: Validate session and page view assumptions against analytics data.

### Data Transfer
- **Average page size**: 2 MB (including assets)
- **Total data transfer**: 3M requests × 2 MB = **6,000 GB/month** (6 TB)
- **CDN cache hit rate**: 80% (assumed)
- **Actual data transfer from origin**: 6,000 GB × 20% = **1,200 GB/month**

**[NEEDS REVIEW]**: Validate page size and cache hit rate assumptions.

### Storage
- **Build artifacts**: 500 MB per build
- **Retention**: Keep last 10 builds
- **Total storage**: 500 MB × 10 = **5 GB**

**[NEEDS REVIEW]**: Confirm build artifact size and retention policy.

---

## Cost Calculation (Production - 10K MAU)

| Component | Calculation | Monthly Cost |
|-----------|-------------|--------------|
| **Build Minutes** | 150 min × $0.01/min | $1.50 |
| **Hosting Requests** | 3M requests × $0.30/1M | $0.90 |
| **Hosting Compute** | Minimal (static site) | $0.00 |
| **Data Transfer Out** | 1,200 GB × $0.15/GB | $180.00 |
| **Storage** | 5 GB × $0.023/GB | $0.12 |
| **WAF (optional)** | 1 × $15.00/month | **[NEEDS REVIEW]** $0.00 or $15.00 |
| **TOTAL (without WAF)** | | **$182.52** |
| **TOTAL (with WAF)** | | **$197.52** |

**Annual Cost**: $2,190.24 - $2,370.24

---

## Optimization Opportunities

1. **CDN Caching**: Increase cache hit rate from 80% to 90%
   - Potential savings: 600 GB × $0.15 = $90/month
   
2. **Asset Optimization**: Reduce page size from 2 MB to 1.5 MB
   - Potential savings: 25% reduction = $45/month

3. **Build Optimization**: Reduce build time from 15 min to 10 min
   - Potential savings: 50 min × $0.01 = $0.50/month (minimal)

---

## Scaling Considerations

| Scenario | MAU | Requests/Month | Data Transfer | Monthly Cost |
|----------|-----|----------------|---------------|--------------|
| Baseline | 10,000 | 3M | 1,200 GB | $182.52 |
| Growth (5x) | 50,000 | 15M | 6,000 GB | $909.00 |
| Scale (10x) | 100,000 | 30M | 12,000 GB | $1,809.00 |
| Enterprise (50x) | 500,000 | 150M | 60,000 GB | $9,046.50 |

**Note**: Costs scale linearly with usage. No volume discounts available for Amplify.

---

## References

- AWS Amplify Pricing: https://aws.amazon.com/amplify/pricing/
- Pricing data retrieved via AWS Pricing API on 2025-06-20
- Effective date: 2025-05-01

---

## Review Checklist

- [ ] Validate build frequency and duration
- [ ] Confirm session and page view assumptions
- [ ] Verify page size and CDN cache hit rate
- [ ] Decide on WAF requirement
- [ ] Confirm free tier applicability
- [ ] Validate build artifact size and retention

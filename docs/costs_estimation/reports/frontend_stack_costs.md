# Frontend Stack Cost Report - AWS Amplify

**Report Date**: October 28, 2025  
**Stack**: Frontend Stack (AWS Amplify Hosting)  
**Region**: us-east-1 (US East - N. Virginia)  
**Baseline Scenario**: 10,000 Monthly Active Users (MAU)  
**Pricing Model**: ON DEMAND

---

## Executive Summary

The Frontend Stack leverages AWS Amplify for hosting the React-based healthcare management application. This report provides a detailed cost breakdown for production deployment serving 10,000 monthly active users.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Monthly Cost** | $182.52 |
| **Annual Cost** | $2,190.24 |
| **Cost per MAU** | $0.018 |
| **Cost per Session** | $0.0009 |
| **Primary Cost Driver** | Data Transfer (98.6%) |

---

## Production Usage Assumptions

### User Activity Patterns

Based on healthcare application usage patterns and client requirements:

- **Monthly Active Users (MAU)**: 10,000 users
- **Sessions per user**: 20 sessions/month
- **Pages per session**: 15 pages (navigation through patient records, forms, chat interface)
- **Total page views**: 3,000,000 requests/month
- **Average session duration**: 20-30 minutes

### Build and Deployment

- **Build frequency**: 10 builds/month (daily deployments during business days)
- **Build duration**: 15 minutes per build (TypeScript compilation, Vite optimization)
- **Build instance**: Standard8GB (4 vCPU, 7 GB memory)
- **Total build minutes**: 150 minutes/month

### Content Delivery

- **Average page size**: 2 MB (React SPA with AWS Cloudscape components, medical images)
- **Total data volume**: 6,000 GB/month (6 TB)
- **CDN cache hit rate**: 80% (CloudFront caching for static assets)
- **Origin data transfer**: 1,200 GB/month (20% of total after CDN caching)

### Storage

- **Build artifact size**: 500 MB per build
- **Retention policy**: Keep last 10 builds
- **Total storage**: 5 GB

---

## Cost Breakdown by Component

### 1. Build Minutes

**Purpose**: CI/CD pipeline for application deployments

| Item | Quantity | Unit Price | Monthly Cost |
|------|----------|------------|--------------|
| Build minutes (Standard8GB) | 150 minutes | $0.01/minute | **$1.50** |

**Calculation**:
```
10 builds/month × 15 minutes/build × $0.01/minute = $1.50
```

**Notes**:
- Uses Standard8GB instance (4 vCPU, 7 GB) - adequate for React/Vite builds
- Build time includes TypeScript compilation, asset optimization, and deployment
- Free tier: 1,000 minutes/month (not applicable for production accounts)

---

### 2. Hosting Requests

**Purpose**: Serving HTTP requests to users

| Item | Quantity | Unit Price | Monthly Cost |
|------|----------|------------|--------------|
| HTTP requests | 3,000,000 requests | $0.30/1M requests | **$0.90** |

**Calculation**:
```
10,000 MAU × 20 sessions × 15 pages = 3,000,000 requests
3,000,000 requests × $0.30/1M = $0.90
```

**Notes**:
- Static site (React SPA) - minimal compute duration charges
- Includes both cached and origin requests
- Request duration charges: $0.00 (static content)

---

### 3. Data Transfer Out

**Purpose**: Delivering content to end users via CloudFront CDN

| Item | Quantity | Unit Price | Monthly Cost |
|------|----------|------------|--------------|
| Data transfer (after CDN) | 1,200 GB | $0.15/GB | **$180.00** |

**Calculation**:
```
Total data: 3,000,000 requests × 2 MB = 6,000 GB
CDN cache hit rate: 80%
Origin transfer: 6,000 GB × 20% = 1,200 GB
Cost: 1,200 GB × $0.15/GB = $180.00
```

**Notes**:
- CloudFront CDN integrated automatically with Amplify
- 80% cache hit rate reduces origin data transfer by 4,800 GB
- Page size includes HTML, JavaScript bundles, CSS, images, and fonts

---

### 4. Storage

**Purpose**: Storing build artifacts and deployment versions

| Item | Quantity | Unit Price | Monthly Cost |
|------|----------|------------|--------------|
| Build artifact storage | 5 GB | $0.023/GB-month | **$0.12** |

**Calculation**:
```
500 MB/build × 10 builds retained = 5 GB
5 GB × $0.023/GB-month = $0.12
```

**Notes**:
- Retains last 10 builds for rollback capability
- Includes source maps and deployment metadata
- Free tier: 5 GB/month (not applicable for production accounts)

---

## Monthly Cost Summary

| Component | Monthly Cost | % of Total |
|-----------|--------------|------------|
| Build Minutes | $1.50 | 0.8% |
| Hosting Requests | $0.90 | 0.5% |
| Data Transfer Out | $180.00 | 98.6% |
| Storage | $0.12 | 0.1% |
| **TOTAL** | **$182.52** | **100%** |

---

## Annual Cost Projection

| Period | Cost |
|--------|------|
| **Monthly** | $182.52 |
| **Quarterly** | $547.56 |
| **Annual** | $2,190.24 |

---

## Cost per User Metrics

| Metric | Calculation | Value |
|--------|-------------|-------|
| **Cost per MAU** | $182.52 ÷ 10,000 users | $0.018/user |
| **Cost per Session** | $182.52 ÷ 200,000 sessions | $0.0009/session |
| **Cost per Page View** | $182.52 ÷ 3,000,000 pages | $0.00006/page |
| **Cost per GB Delivered** | $182.52 ÷ 6,000 GB | $0.030/GB |

---

## Optimization Opportunities

### High-Impact Optimizations

#### 1. Increase CDN Cache Hit Rate (90% → 95%)

**Current**: 80% cache hit rate  
**Target**: 90% cache hit rate  
**Impact**: Reduce origin data transfer from 1,200 GB to 600 GB

**Savings Calculation**:
```
Current: 1,200 GB × $0.15 = $180.00
Optimized: 600 GB × $0.15 = $90.00
Monthly savings: $90.00 (50% reduction)
Annual savings: $1,080.00
```

**Implementation**:
- Configure aggressive cache headers (Cache-Control: max-age=31536000 for static assets)
- Use content hashing for cache busting (Vite does this automatically)
- Implement service worker for client-side caching
- Use CloudFront cache behaviors for different content types

---

#### 2. Reduce Page Size (2 MB → 1.5 MB)

**Current**: 2 MB average page size  
**Target**: 1.5 MB average page size (25% reduction)  
**Impact**: Reduce total data transfer from 6,000 GB to 4,500 GB

**Savings Calculation**:
```
Current: 1,200 GB × $0.15 = $180.00
Optimized: 900 GB × $0.15 = $135.00
Monthly savings: $45.00 (25% reduction)
Annual savings: $540.00
```

**Implementation**:
- Enable image optimization (WebP format, lazy loading)
- Implement code splitting and dynamic imports
- Use tree shaking to eliminate unused code
- Compress assets with Brotli/Gzip
- Minimize bundle size through dependency analysis

---

### Medium-Impact Optimizations

#### 3. Optimize Build Time (15 min → 10 min)

**Current**: 15 minutes per build  
**Target**: 10 minutes per build (33% reduction)  
**Impact**: Reduce build minutes from 150 to 100

**Savings Calculation**:
```
Current: 150 min × $0.01 = $1.50
Optimized: 100 min × $0.01 = $1.00
Monthly savings: $0.50 (33% reduction)
Annual savings: $6.00
```

**Implementation**:
- Enable build caching (dependencies, TypeScript compilation)
- Optimize Vite configuration
- Use parallel builds where possible
- Reduce unnecessary build steps

---

### Combined Optimization Impact

| Optimization | Monthly Savings | Annual Savings | Implementation Effort |
|--------------|-----------------|----------------|----------------------|
| CDN Cache (80% → 90%) | $90.00 | $1,080.00 | Medium |
| Page Size (2 MB → 1.5 MB) | $45.00 | $540.00 | High |
| Build Time (15 → 10 min) | $0.50 | $6.00 | Low |
| **TOTAL** | **$135.50** | **$1,626.00** | |

**Optimized Monthly Cost**: $47.02 (74% reduction)  
**Optimized Annual Cost**: $564.24

---

## Scaling Analysis

### Cost Projection by User Growth

| Scenario | MAU | Requests/Month | Data Transfer | Monthly Cost | Cost/MAU |
|----------|-----|----------------|---------------|--------------|----------|
| **Baseline** | 10,000 | 3M | 1,200 GB | $182.52 | $0.018 |
| **Growth (5x)** | 50,000 | 15M | 6,000 GB | $909.00 | $0.018 |
| **Scale (10x)** | 100,000 | 30M | 12,000 GB | $1,809.00 | $0.018 |
| **Enterprise (50x)** | 500,000 | 150M | 60,000 GB | $9,046.50 | $0.018 |

**Scaling Characteristics**:
- **Linear scaling**: Costs scale proportionally with user growth
- **No volume discounts**: AWS Amplify does not offer tiered pricing
- **Consistent cost per MAU**: $0.018/user regardless of scale
- **Build costs remain constant**: Only 10 builds/month regardless of user count

---

### Scaling Inflection Points

| Threshold | Consideration | Recommendation |
|-----------|---------------|----------------|
| **50K MAU** | $900/month | Consider CloudFront directly for better caching control |
| **100K MAU** | $1,800/month | Evaluate alternative hosting (S3 + CloudFront) |
| **500K MAU** | $9,000/month | Mandatory migration to S3 + CloudFront for cost efficiency |

---

## Alternative Hosting Comparison

### S3 + CloudFront vs Amplify

For high-scale deployments, consider migrating to S3 + CloudFront:

| Component | Amplify (100K MAU) | S3 + CloudFront (100K MAU) | Savings |
|-----------|-------------------|---------------------------|---------|
| Hosting | $9.00 | $0.00 (S3 static hosting) | $9.00 |
| Data Transfer | $1,800.00 | $1,020.00 (CloudFront pricing) | $780.00 |
| Storage | $0.12 | $0.69 (S3 Standard) | -$0.57 |
| **TOTAL** | **$1,809.12** | **$1,020.69** | **$788.43** |

**Break-even point**: ~50K MAU  
**Recommendation**: Migrate to S3 + CloudFront at 50K+ MAU for 40-45% cost savings

---

## Monitoring and Alerting

### Cost Monitoring Recommendations

1. **AWS Budget Configuration**
   - Monthly budget: $200
   - Alert thresholds: 80% ($160), 90% ($180), 100% ($200)
   - Notification: Email to finance and engineering teams

2. **Usage Metrics to Track**
   - Data transfer volume (GB/day)
   - Request count (requests/hour)
   - CDN cache hit rate (%)
   - Average page size (MB)
   - Build frequency and duration

3. **Cost Anomaly Detection**
   - Enable AWS Cost Anomaly Detection
   - Threshold: $50 increase over 7-day average
   - Alert on unexpected traffic spikes

4. **Performance Metrics**
   - CloudFront cache hit ratio (target: >80%)
   - Page load time (target: <2 seconds)
   - Build success rate (target: >95%)

---

## Assumptions and Exclusions

### Included in Estimate

✅ Build minutes for CI/CD deployments  
✅ Hosting compute for serving requests  
✅ Data transfer out via CloudFront CDN  
✅ Storage for build artifacts  
✅ CloudFront CDN integration (included in Amplify pricing)

### Excluded from Estimate

❌ Custom domain SSL certificates (free with AWS Certificate Manager)  
❌ AWS WAF for web application firewall ($15/month if required)  
❌ Route 53 DNS hosting ($0.50/hosted zone + $0.40/1M queries)  
❌ Third-party monitoring tools (Datadog, New Relic)  
❌ Development/staging environments (separate cost)  
❌ Data transfer IN (free)  
❌ Free tier benefits (not applicable for production accounts)

### Key Assumptions

- **User behavior**: 20 sessions/month, 15 pages/session per user
- **Page size**: 2 MB average (includes all assets)
- **CDN efficiency**: 80% cache hit rate
- **Build frequency**: 10 builds/month (daily deployments)
- **Build duration**: 15 minutes per build
- **Region**: us-east-1 (pricing may vary by region)
- **Pricing date**: October 2025 (subject to AWS pricing changes)

---

## Risk Factors and Mitigation

### Cost Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Traffic spike (2x) | +$180/month | Medium | Implement rate limiting, CDN caching |
| Larger page sizes | +$90/month | Medium | Asset optimization, monitoring |
| Increased build frequency | +$5/month | Low | Build optimization, caching |
| CDN cache miss rate increase | +$180/month | Low | Cache header optimization |

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Build failures | Deployment delays | Automated testing, rollback capability |
| CDN cache invalidation | Increased costs | Versioned assets, cache-busting |
| Regional outages | Service unavailability | Multi-region deployment (additional cost) |

---

## Recommendations

### Immediate Actions (Month 1)

1. ✅ **Implement aggressive CDN caching** (save $90/month)
   - Configure cache headers for static assets
   - Use content hashing for cache busting
   - Monitor cache hit rate daily

2. ✅ **Enable asset optimization** (save $45/month)
   - Implement image lazy loading
   - Enable WebP image format
   - Use code splitting for JavaScript bundles

3. ✅ **Set up cost monitoring** (prevent overruns)
   - Configure AWS Budgets with alerts
   - Enable Cost Anomaly Detection
   - Track daily data transfer metrics

### Short-term Actions (Months 2-3)

4. ✅ **Optimize build pipeline** (save $0.50/month)
   - Enable build caching
   - Optimize Vite configuration
   - Reduce build frequency if possible

5. ✅ **Implement performance monitoring**
   - Track page load times
   - Monitor CDN performance
   - Analyze user behavior patterns

### Long-term Actions (Months 4-6)

6. ✅ **Evaluate hosting alternatives** (at 50K+ MAU)
   - Compare S3 + CloudFront costs
   - Plan migration strategy
   - Test performance in staging

7. ✅ **Implement advanced caching strategies**
   - Service worker for offline support
   - Client-side caching
   - API response caching

---

## Compliance and Security

### HIPAA Compliance

- **Data encryption**: All data transfer encrypted via HTTPS (TLS 1.2+)
- **Access control**: AWS IAM for deployment access
- **Audit logging**: CloudTrail logs all API calls
- **Data residency**: us-east-1 region (US-based)

**Note**: AWS Amplify is HIPAA-eligible when configured with appropriate BAA.

### Security Considerations

- **WAF integration**: Optional ($15/month) - recommended for production
- **DDoS protection**: AWS Shield Standard (included)
- **SSL/TLS**: Free certificates via AWS Certificate Manager
- **Authentication**: Cognito integration (separate cost)

---

## Conclusion

The Frontend Stack using AWS Amplify provides a cost-effective hosting solution for the healthcare management application at **$182.52/month** for 10,000 MAU. The primary cost driver is data transfer (98.6%), which can be significantly reduced through CDN optimization and asset compression.

### Key Takeaways

1. **Affordable baseline**: $0.018 per MAU is competitive for healthcare applications
2. **Optimization potential**: 74% cost reduction possible through caching and asset optimization
3. **Linear scaling**: Costs scale predictably with user growth
4. **Migration threshold**: Consider S3 + CloudFront at 50K+ MAU for better economics
5. **Low operational overhead**: Fully managed service reduces DevOps costs

### Next Steps

1. Implement high-impact optimizations (CDN caching, asset optimization)
2. Set up cost monitoring and alerting
3. Validate usage assumptions against actual analytics data
4. Plan for scaling beyond 50K MAU

---

## References

- **Pricing Data Source**: AWS Pricing API via MCP server
- **Pricing File**: `docs/costs_estimation/data/amplify_pricing.md`
- **Requirements**: Requirements 2.1, 10.1, 10.2
- **Design Document**: `.kiro/specs/aws-cost-estimation/design.md`
- **AWS Amplify Pricing**: https://aws.amazon.com/amplify/pricing/
- **CloudFront Pricing**: https://aws.amazon.com/cloudfront/pricing/

---

**Report Version**: 1.0  
**Last Updated**: October 28, 2025  
**Prepared By**: AWS Cost Estimation Team  
**Review Status**: Ready for stakeholder review

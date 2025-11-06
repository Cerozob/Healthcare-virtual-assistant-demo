# Client Requirements Summary - AWSomeBuilder2

## Usage Assumptions (From Meeting Notes)

### User Base & Scale

- **Total Users**: 100,000 registered users in the system
- **Active Users**: 10,000 monthly active users (10% of total)
- **Concurrent Load**: 30,000 requests per minute during peak hours
- **Geographic**: LATAM region, Spanish language primary (supported and working)

### Medical Workflow Patterns

- **Doctor Sessions**: 20 interactions per doctor per session
- **Session Duration**: 15-30 minutes typical, maximum 1 hour
- **Peak Hours**: Business hours for medical facilities
- **Use Case**: Reduce doctor documentation time from 2-3 minutes to seconds

### Data Characteristics

- **Document Types**: Medical documents, images, audio files
- **Processing**: Bedrock Data Automation + Lambda for file processing
- **Storage**: Medical records with HIPAA compliance requirements
- **Token Usage**: ~30 tokens per user message, 100-2000 tokens per LLM reply

## Technical Architecture Decisions

### Database Strategy

- **Migration Path**: On-premise SQL Server/PostgreSQL → Aurora PostgreSQL
- **Rationale**: DMS compatibility, Babelfish mention for SQL Server migration
- **Vector Storage**: Aurora PostgreSQL with pgvector (chosen over S3 vectors)

### AI/ML Services

- **Document Processing**: Bedrock Data Automation + Lambda for file processing
- **Knowledge Base**: Aurora PostgreSQL vectors with pgvector
- **Model Selection**: Bedrock models with Spanish language support (confirmed working)
- **Guardrails**: PII/PHI protection for medical data
- **No Comprehend Medical or HealthScribe**: Only BDA and Lambda processing

### Security & Compliance

- **HIPAA Compliance**: All services must be HIPAA eligible
- **Authentication**: Cognito Standard tier only (no Active Directory integration)
- **Authorization**: Custom Lambda authorizer for API access
- **Data Residency**: AWS us-east-1 region

## Feedback from Stakeholder Meetings

### CEO (Jose) - Business Focus

- **ROI Measurement**: How to measure impact vs current manual processes
- **Automation Value**: Reduce medical documentation time significantly
- **Scaling Questions**: Cost implications of growth beyond 10K active users

### CISO (Sergio) - Security Focus

- **Authentication**: Cognito Standard tier only (no AD integration)
- **Authorization**: Custom Lambda authorizer for API access control
- **Compliance**: PII/PHI handling, audit trails
- **Billing Model**: Active users only (not all registered users)

### Innovation Lead (Paola) - Technical Focus

- **Concurrency**: 30,000 RPM capacity requirement
- **Model Selection**: Why Bedrock vs OpenAI, cost control per identity
- **Language Support**: Spanish language model performance
- **Metrics**: Custom metrics for Bedrock usage tracking

### CTO (Jacayce) - Implementation Focus

- **Technology Stack**: React frontend (confirmed)
- **Development Process**: GitHub repository with GitHub Actions
- **Deployment**: Amplify builds (~5 minutes per build, 4 builds/month for weekly prod deployments)
- **Staging**: Multiple environment support

## Cost Control Requirements

### Budget Constraints

- **Cost Monitoring**: Per-identity cost tracking requested
- **Scaling Economics**: Cost per active user analysis needed (10K active users, not 100K total)
- **Growth Planning**: Budget for 5x user growth scenario

### Optimization Priorities

1. **Database Costs**: Aurora scaling optimization critical
2. **AI Model Costs**: Token usage monitoring (~30 input, 100-2000 output tokens per interaction)
3. **Lambda Costs**: Custom authorization and file processing functions
4. **Amplify Costs**: 4 builds per month (5 minutes each)
5. **Storage Costs**: Medical document lifecycle management

## Compliance & Security Requirements

### HIPAA Compliance Checklist (From Notes)

- ✅ KMS encryption
- ✅ Secrets Manager
- ✅ IAM roles and policies
- ✅ CloudWatch monitoring
- ✅ Cognito authentication
- ✅ CloudFormation IaC
- ✅ ECR container registry
- ✅ Systems Manager Parameter Store
- ✅ S3 secure storage
- ✅ API Gateway
- ✅ Lambda functions
- ✅ Bedrock AI services
- ✅ Aurora database
- ✅ DMS migration tools
- ✅ DataSync file migration

### Additional Security Considerations

- **Authentication**: Cognito Essentials tier for user management
- **Authorization**: Lambda-based custom authorization logic
- **Network Security**: VPC configuration per architecture
- **Audit Logging**: CloudTrail, CloudWatch comprehensive logging
- **Data Encryption**: At rest and in transit for all medical data

## Implementation Phases

### Phase 1: Core Infrastructure

- Database migration and setup
- Basic authentication and security
- Core API endpoints

### Phase 2: AI Integration

- Bedrock services implementation
- Document processing pipeline
- Virtual assistant capabilities

### Phase 3: Optimization & Scale

- Performance optimization
- Cost optimization implementation
- Advanced monitoring and alerting

## Success Metrics

### Performance Metrics

- **Response Time**: API responses < 500ms
- **Availability**: 99.9% uptime for medical operations
- **Concurrency**: Handle 30,000 RPM without degradation

### Business Metrics

- **Time Savings**: Reduce doctor documentation time by 80%+
- **User Adoption**: 10,000 active users within 6 months
- **Cost Efficiency**: Cost per active user optimization

### Technical Metrics

- **Token Usage**: Bedrock model efficiency tracking
- **Cache Hit Rate**: API and response caching effectiveness
- **Database Performance**: Aurora ACU utilization optimization

## Risk Factors

### Technical Risks

- **Scaling**: Aurora auto-scaling behavior under load
- **Token Usage**: Variable LLM response lengths (100-2000 tokens) affecting costs
- **Lambda Cold Starts**: Authorization and processing function performance

### Business Risks

- **Cost Overruns**: Bedrock usage exceeding budget due to variable token usage
- **Adoption**: User adoption rate affecting ROI
- **Compliance**: HIPAA audit requirements

### Mitigation Strategies

- **Cost Controls**: Budgets, alerts, and automatic scaling limits based on active users
- **Performance Testing**: Load testing before production (30K RPM capacity)
- **Compliance Review**: Regular security and compliance audits

## Cost Calculation Assumptions & Estimates

### Usage Patterns & Scaling Scenarios

#### Single User Baseline (1 Active User)

- **Monthly Interactions**: 20 interactions per session, 1 session per month
- **Token Usage**: 30 input tokens + 565 output tokens per interaction (average)
- **Total Monthly Tokens**: 11,900 tokens (600 input + 11,300 output)
- **Lambda Invocations**: 40 per month (API calls + authorization)
- **Database Usage**: Minimal Aurora PostgreSQL usage
- **Storage**: ~1MB medical documents per user

#### Current Scale (10,000 Active Users)

- **Monthly Interactions**: 200,000 total interactions
- **Token Usage**: 119M tokens monthly (6M input + 113M output)
- **Lambda Invocations**: 400,000 per month
- **Aurora PostgreSQL**: db.r8g.large instance (~$265/month)
- **Storage**: ~10GB medical documents + vector storage

#### 5x Growth Scale (50,000 Active Users)

- **Monthly Interactions**: 1,000,000 total interactions
- **Token Usage**: 595M tokens monthly (30M input + 565M output)
- **Lambda Invocations**: 2,000,000 per month
- **Aurora PostgreSQL**: db.r8g.2xlarge instance (~$815/month)
- **Storage**: ~50GB medical documents + vector storage

### AWS Service Pricing (US East 1)

#### Amazon Bedrock Models Comparison

**Amazon Nova Pro (Current Requirement)**

- **Input Tokens**: $0.0008 per 1K tokens
- **Output Tokens**: $0.0032 per 1K tokens
- **Cache Read**: $0.0002 per 1K tokens
- **Cache Write**: $0.00 per 1K tokens (free)
- **Batch Processing**: Same pricing as on-demand
- **Latency**: Standard performance
- **Context Window**: 300K tokens

**Claude Haiku 4.5 (Previous Model)**

- **Input Tokens**: $0.001 per 1K tokens (+25% vs Nova Pro)
- **Output Tokens**: $0.005 per 1K tokens (+56% vs Nova Pro)
- **Cache Read**: $0.0001 per 1K tokens (-50% vs Nova Pro)
- **Cache Write**: $0.00125 per 1K tokens (paid vs free)
- **Batch Processing**: 50% discount available
- **Latency**: Optimized for speed
- **Context Window**: 200K tokens

#### Model Selection Analysis

| Feature | Nova Pro | Claude Haiku 4.5 | Winner |
|---------|----------|------------------|---------|
| **Input Cost** | $0.80/1M | $1.00/1M | **Nova Pro (-20%)** |
| **Output Cost** | $3.20/1M | $5.00/1M | **Nova Pro (-36%)** |
| **Cache Read** | $0.20/1M | $0.10/1M | Claude (-50%) |
| **Cache Write** | Free | $1.25/1M | **Nova Pro (free)** |
| **Context Window** | 300K | 200K | **Nova Pro (+50%)** |
| **Overall Cost** | **Lower** | Higher | **Nova Pro (~30% savings)** |

#### Cost Impact Analysis (10K Users Scenario)

```
Nova Pro (Current):
- Input: 6M × $0.0008 = $4.80
- Output: 113M × $0.0032 = $361.60
- Cache: Minimal (free writes)
- Total: $366.40/month

Claude Haiku 4.5 (Alternative):
- Input: 6M × $0.001 = $6.00
- Output: 113M × $0.005 = $565.00
- Cache: 6M × $0.00125 = $7.50 (writes)
- Total: $578.50/month

Monthly Savings with Nova Pro: $212.10 (37% reduction)
Annual Savings: $2,545.20
```

**Additional Services**

- **Guardrails**: $0.15 per 1K text units
- **Data Automation**: $0.003 per image processed

#### AWS Lambda

- **Requests**: $0.0000002 per request
- **Compute (x86)**: $0.0000166667 per GB-second (first 6B GB-seconds)
- **Authorization Lambda**: ~512MB, 1 second average execution

#### Amazon Aurora PostgreSQL

- **db.r8g.large**: $0.359 per hour ($265.16/month)
- **db.r8g.xlarge**: $0.718 per hour ($530.32/month)
- **db.r8g.2xlarge**: $1.104 per hour ($815.04/month)
- **Storage**: $0.10 per GB-month
- **I/O**: $0.20 per 1M requests

#### Amazon Cognito Standard

- **Monthly Active Users**: $0.0055 per MAU (first 50K)
- **Additional Tiers**: $0.0046 per MAU (50K-950K)

#### AWS Amplify

- **Build Minutes**: $0.01 per build minute
- **Hosting**: $0.15 per GB served
- **Storage**: $0.023 per GB stored

### Cost Estimates by Scenario

#### Single User Monthly Cost

- **Bedrock (Nova Pro)**: $0.038 (0.6K input + 11.3K output tokens)
- **Lambda**: $0.0001 (40 requests × 512MB × 1s)
- **Aurora**: $8.84 (shared db.r8g.large, allocated portion)
- **Cognito**: $0.0055 (1 MAU)
- **Storage**: $0.001 (1MB documents)
- **Total per user**: ~$8.88

#### Current Scale (10K Users) Monthly Cost

- **Bedrock (Nova Pro)**: $379.20 (6M input + 113M output tokens)
- **Guardrails**: $17.85 (119K text units processed)
- **Lambda**: $5.33 (400K requests + compute)
- **Aurora PostgreSQL**: $265.16 (db.r8g.large + storage)
- **Cognito**: $55.00 (10K MAU)
- **Amplify**: $2.00 (4 builds/month × 5 minutes)
- **S3 Storage**: $2.30 (10GB documents)
- **Total Monthly**: ~$726.84
- **Cost per Active User**: ~$0.073

#### 5x Growth (50K Users) Monthly Cost

- **Bedrock (Nova Pro)**: $1,896.00 (30M input + 565M output tokens)
- **Guardrails**: $89.25 (595K text units processed)
- **Lambda**: $26.67 (2M requests + compute)
- **Aurora PostgreSQL**: $815.04 (db.r8g.2xlarge + storage)
- **Cognito**: $253.00 (50K MAU)
- **Amplify**: $2.00 (4 builds/month × 5 minutes)
- **S3 Storage**: $11.50 (50GB documents)
- **Total Monthly**: ~$3,093.46
- **Cost per Active User**: ~$0.062

### Cost Optimization Opportunities

**Immediate**: Prompt engineering (-29%), response caching (-20-30%), ARM Lambda (-20%)
**Medium-term**: Batch processing (-50%), Aurora Reserved Instances (-30-40%), Nova Lite for simple queries (-75%)
**Advanced**: Provisioned throughput, multi-model routing, S3 Intelligent Tiering

- **Compression**: Optimize document storage and vector embeddings

### Alternative Deployment Options

#### Option 1: Full AWS Implementation (Current Estimates)

- **Backend**: AWS Lambda + API Gateway + Aurora PostgreSQL
- **Frontend**: AWS Amplify with build pipeline
- **Total Cost**: $726.84/month (10K users)

#### Option 2: Hybrid with Existing Infrastructure

- **Backend**: Existing PostgreSQL + Existing API Server
- **Frontend**: AWS Amplify with build pipeline
- **AI Services**: Bedrock + Guardrails only
- **Cost Savings**: -$270.16/month (Aurora + Lambda)
- **Total Cost**: $451.35/month (10K users) - **38% savings**

#### Option 3: Minimal AWS Integration

- **Backend**: Existing PostgreSQL + Existing API Server
- **Frontend**: External build + Amplify hosting only
- **AI Services**: Bedrock + Guardrails only
- **Cost Savings**: -$272.16/month (backend + builds)
- **Total Cost**: $449.35/month (10K users) - **38% savings**

| Deployment Option | Monthly Cost (10K) | Savings | Primary Trade-off |
|-------------------|-------------------|---------|-------------------|
| **Full AWS** | $726.84 | Baseline | Complete cloud-native solution |
| **Hybrid Backend** | $451.35 | -38% | Database migration required |
| **Minimal AWS** | $449.35 | -38% | External CI/CD process needed |

### Nova Pro Benefits Summary

**Cost Impact**: 37% lower AI costs ($212/month savings at 10K users)
**Technical**: Larger context window (300K vs 200K tokens), better Spanish support
**Operational**: Free cache writes, simplified billing, better cost predictability

### Key Cost Drivers & Risks

#### Primary Cost Drivers (by impact)

1. **Bedrock Token Usage** (50-55% of total costs) - *Reduced with Nova Pro*
2. **Aurora PostgreSQL** (35-40% of total costs)
3. **Cognito MAU** (8-10% of total costs)
4. **Lambda + Other Services** (2-5% of total costs)

#### Cost Risk Factors

- **Variable Token Usage**: Output tokens range 100-2000, affecting predictability
- **User Growth**: Non-linear scaling of Aurora instance requirements
- **Peak Load**: 30K RPM capacity may require provisioned throughput
- **Document Volume**: Medical document storage growth over time

#### Billing Model Assumptions

- **Active Users Only**: Cognito charges only for monthly active users
- **On-Demand Pricing**: No reserved instances or savings plans included
- **Standard Support**: No premium support costs included
- **Single Region**: All costs assume us-east-1 deployment

---

**Sources**:

- `awsomebuilder2_notes.md` - Meeting notes and feedback
- Stakeholder feedback sessions (Jose, Sergio, Paola, Jacayce)
- Technical architecture decisions and HIPAA compliance checklist
- AWS Pricing API data (November 2025)

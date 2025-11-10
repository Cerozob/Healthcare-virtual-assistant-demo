# Client Requirements Summary - AWSomeBuilder2

[Go to AWS Calculator](https://calculator.aws/#/estimate?id=302ce00e8bf779b754a1d5b4088c1a57d2ddbee2)

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

- **Authentication**: Cognito Standard tier for user management
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

---

**Sources**:

- `awsomebuilder2_notes.md` - Meeting notes and feedback
- Stakeholder feedback sessions (Jose, Sergio, Paola, Jacayce)
- Technical architecture decisions and HIPAA compliance checklist
- AWS Pricing API data (November 2025)

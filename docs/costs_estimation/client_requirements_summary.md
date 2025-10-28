# Client Requirements Summary - AWSomeBuilder2

## Usage Assumptions (From Meeting Notes)

### User Base & Scale
- **Total Users**: 100,000 registered users in the system
- **Active Users**: 10,000 monthly active users (10% of total)
- **Concurrent Load**: 30,000 requests per minute during peak hours
- **Geographic**: LATAM region, Spanish language primary

### Medical Workflow Patterns
- **Doctor Sessions**: 20 interactions per doctor per session
- **Session Duration**: 15-30 minutes typical, maximum 1 hour
- **Peak Hours**: Business hours for medical facilities
- **Use Case**: Reduce doctor documentation time from 2-3 minutes to seconds

### Data Characteristics
- **Document Types**: Medical documents, images, audio files
- **Processing**: Automated document analysis and classification
- **Storage**: Medical records with HIPAA compliance requirements
- **Language**: Spanish (LATAM) - affects tokenization and model selection

## Technical Architecture Decisions

### Database Strategy
- **Migration Path**: On-premise SQL Server/PostgreSQL → Aurora PostgreSQL
- **Rationale**: DMS compatibility, Babelfish mention for SQL Server migration
- **Vector Storage**: Aurora PostgreSQL with pgvector (cost-effective vs OpenSearch)

### AI/ML Services
- **Document Processing**: Bedrock Data Automation → Comprehend Medical pipeline
- **Knowledge Base**: Aurora PostgreSQL vectors (not OpenSearch Serverless)
- **Model Selection**: Bedrock models with Spanish language support
- **Guardrails**: PII/PHI protection for medical data

### Security & Compliance
- **HIPAA Compliance**: All services must be HIPAA eligible
- **Authentication**: Cognito integration (mentioned in feedback)
- **Data Residency**: AWS us-east-1 region
- **Firewall**: Palo Alto firewall integration mentioned

## Feedback from Stakeholder Meetings

### CEO (Jose) - Business Focus
- **ROI Measurement**: How to measure impact vs current manual processes
- **Automation Value**: Reduce medical documentation time significantly
- **Scaling Questions**: Cost implications of growth beyond 10K active users

### CISO (Sergio) - Security Focus
- **Authentication**: Active Directory integration via SAML/Cognito
- **Network Security**: Palo Alto firewall, WAF rules
- **Compliance**: PII/PHI handling, audit trails
- **Manual Processes**: Current authentication workflows to be automated

### Innovation Lead (Paola) - Technical Focus
- **Concurrency**: 30,000 RPM capacity requirement
- **Model Selection**: Why Bedrock vs OpenAI, cost control per identity
- **Language Support**: Spanish language model performance
- **Metrics**: Custom metrics for Bedrock usage tracking

### CTO (Jacayce) - Implementation Focus
- **Technology Stack**: React/Vue frontend preferences
- **Development Process**: GitHub, Jenkins integration
- **API Design**: Internal API authentication processes
- **Staging**: Multiple environment support

## Cost Control Requirements

### Budget Constraints
- **Cost Monitoring**: Per-identity cost tracking requested
- **Scaling Economics**: Cost per active user analysis needed
- **Growth Planning**: Budget for 5x user growth scenario

### Optimization Priorities
1. **Database Costs**: Aurora scaling optimization critical
2. **AI Model Costs**: Token usage monitoring and optimization
3. **API Costs**: Request volume optimization through caching
4. **Storage Costs**: Medical document lifecycle management

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
- **Active Directory**: SAML integration with on-premise AD
- **Network Security**: VPC configuration, firewall rules
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
- **Spanish Language**: Model performance in Spanish vs English
- **Scaling**: Aurora auto-scaling behavior under load
- **Integration**: Active Directory SAML complexity

### Business Risks
- **Cost Overruns**: Bedrock usage exceeding budget
- **Adoption**: User adoption rate affecting ROI
- **Compliance**: HIPAA audit requirements

### Mitigation Strategies
- **Cost Controls**: Budgets, alerts, and automatic scaling limits
- **Performance Testing**: Load testing before production
- **Compliance Review**: Regular security and compliance audits

---

**Sources**: 
- `awsomebuilder2_notes.md` - Meeting notes and feedback
- Stakeholder feedback sessions (Jose, Sergio, Paola, Jacayce)
- Technical architecture decisions and HIPAA compliance checklist

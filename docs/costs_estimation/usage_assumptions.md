# Healthcare Management System - Usage Assumptions

## User Base & Activity Patterns

### Active Users

- **10,000 doctors** (daily and monthly active users)
- **Work Schedule**: 8 hours per workday, 20 workdays per month (160 hours monthly)
- **Patient Appointments**: 20 minutes per appointment
- **Daily Throughput**: 3 appointments per hour × 8 hours = 24 appointments per doctor per day
- **Monthly Throughput**: 24 appointments × 20 workdays = 480 appointments per doctor per month

### System-Wide Volume

- **Total Monthly Appointments**: 10,000 doctors × 480 appointments = 4,800,000 appointments
- **Peak Load Capacity**: 30,000 API requests per minute (existing requirement)
- **Peak Periods**: Working hours on weekdays (20 days × 8 hours = 160 peak hours monthly)

## AI Assistant Usage Patterns

### Chatbot Interactions

- **Interactions per Appointment**: 5 chatbot interactions per appointment
- **Doctor Messages**: 2 paragraphs average (150 tokens per message)
- **Model Responses**: 600 tokens average per response
- **Token Usage per Appointment**:
  - Input: 5 × 150 = 750 tokens
  - Output: 5 × 600 = 3,000 tokens

### Monthly AI Usage (System-Wide)

- **Total Appointments**: 4,800,000 appointments monthly
- **Input Tokens**: 4,800,000 × 750 = 3.6 billion tokens monthly
- **Output Tokens**: 4,800,000 × 3,750 = 18 billion tokens monthly
- **Total Token Usage**: 21.6 billion tokens monthly

## Document Processing Patterns

### Document Upload & Processing

- **Documents per Appointment**: 1 document (5 pages average)
- **File Size**: 2.5MB average per document
- **Monthly Documents**: 4,800,000 documents
- **Monthly Storage**: 4,800,000 × 2.5MB = 12TB of new documents monthly

### Bedrock Data Automation Processing

- **Processing per Document**: 5-page document → 50KB extracted data
- **Lambda Processing**: 3 seconds compute time per document (document extraction)
- **Knowledge Base Ingestion**: Original + processed documents synced when available
- **Monthly Processing Volume**: 4,800,000 documents × 3 seconds = 14,400,000 seconds (4,000 hours)

## API & Compute Usage

### API Gateway Requests

- **Peak Load**: 30,000 requests per minute (existing system capacity)
- **Peak Hours**: 160 hours monthly (20 workdays × 8 hours)
- **Virtual Assistant**: Additional requests bypass API, use Lambda directly

### Lambda Compute Patterns

- **Virtual Assistant**: 2 Lambda invocations per chatbot interaction
- **Compute Duration**:
  - Document Extraction: 3 seconds per document
  - Other Lambda calls (API, virtual assistant): 400ms average per call
- **Monthly Lambda Calls**:
  - Chatbot: 4,800,000 appointments × 5 interactions × 2 calls = 48,000,000 calls
  - Document Processing: 4,800,000 documents × 1 call = 4,800,000 calls
  - **Total**: 52,800,000 Lambda invocations monthly

### Database I/O Operations

- **API Requests**: All API calls access RDS database
- **Lambda Calls**: All Lambda invocations access RDS database
- **Total I/O**: API requests + Lambda calls = Database operations

## Infrastructure Scaling Requirements

### Storage Requirements

- **New Documents**: 12TB monthly
- **Processed Data**: 4,800,000 × 50KB = 240GB monthly
- **Knowledge Base**: Original + processed documents
- **Growth Pattern**: Cumulative storage increases monthly

### Compute Requirements

- **Lambda Memory**: Assume 512MB per function
- **Lambda Duration**:
  - Virtual Assistant: 400ms × 48M calls = 19.2M seconds monthly
  - Document Processing: 3s × 4.8M docs = 14.4M seconds monthly
  - **Total**: 33.6M seconds (9,333 hours) monthly

### Database Load

- **Concurrent Users**: Up to 10,000 during peak hours
- **I/O Operations**: 52.8M+ operations monthly (Lambda + API calls)
- **Storage Growth**: Patient data, document metadata, chat history

## Key Assumptions from Client Requirements

### From Previous Analysis

- **Web App Size**: 4.7MB (from demo)
- **Page Size**: 1MB per page visit
- **Build Frequency**: Weekly deployments (4 builds monthly, 5 minutes each)
- **Authentication**: Cognito Standard tier (10K free tier applies)
- **Geographic**: LATAM region, Spanish language support
- **Compliance**: HIPAA-eligible services required

### Cost Control Factors

- **Billing Model**: Active users only (10K, not 100K registered)
- **Peak vs Average**: Design for 30K RPM, average usage much lower
- **Token Variability**: Model responses 100-2000 tokens (using 750 average)
- **Caching Strategy**: Potential for response caching to reduce costs

## Calculated Monthly Totals

### User Activity

- **Active Doctors**: 10,000
- **Total Appointments**: 4,800,000
- **Chatbot Interactions**: 24,000,000

### Data Processing

- **Documents Processed**: 4,800,000
- **Document Storage**: 12TB new monthly
- **AI Tokens**: 21.6 billion total

### Compute Usage

- **Lambda Invocations**: 52,800,000
- **Lambda Compute Time**: 33.6M seconds (9,333 hours)
  - Document Processing: 14.4M seconds (4,000 hours)
  - Virtual Assistant: 19.2M seconds (5,333 hours)
- **Database I/O**: 52.8M+ operations

### Infrastructure Load

- **Peak API Load**: 30,000 RPM capacity
- **Peak Hours**: 160 hours monthly
- **Storage Growth**: 12TB+ monthly cumulative

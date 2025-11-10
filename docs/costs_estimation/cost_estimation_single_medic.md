# Healthcare Management System - AWS Cost Estimation (Single Medic)

## Cost Calculator
*[Link to interactive cost calculator will be placed here]*

---

## Frontend Component

### AWS Amplify

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Build Minutes | | |
| Data Transfer | | |
| Storage | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Build Minutes: $X.XX × Y minutes = $Z.ZZ
* Data Transfer: $X.XX × Y GB = $Z.ZZ
* Storage: $X.XX × Y GB = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Cognito

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Monthly Active Users | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Monthly Active Users: $X.XX × Y MAU = $Z.ZZ
* **Total: $Z.ZZ**

---

## Backend Component

### Amazon API Gateway

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| API Requests | | |
| Data Transfer | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* API Requests: $X.XX × Y requests = $Z.ZZ
* Data Transfer: $X.XX × Y GB = $Z.ZZ
* **Total: $Z.ZZ**

### AWS Lambda

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Requests | | |
| Compute (GB-seconds) | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Requests: $X.XX × Y requests = $Z.ZZ
* Compute: $X.XX × Y GB-seconds = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon RDS Aurora

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Instance (allocated) | | |
| Storage (allocated) | | |
| I/O Operations | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Instance (allocated): $X.XX ÷ Y users = $Z.ZZ
* Storage (allocated): $X.XX ÷ Y users = $Z.ZZ
* I/O Operations: $X.XX ÷ Y users = $Z.ZZ
* **Total: $Z.ZZ**

---

## Document Workflow Component

### Amazon S3

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Standard Storage | | |
| PUT Requests | | |
| GET Requests | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Standard Storage: $X.XX × Y GB = $Z.ZZ
* PUT Requests: $X.XX × (Y requests ÷ 1K) = $Z.ZZ
* GET Requests: $X.XX × (Y requests ÷ 1K) = $Z.ZZ
* **Total: $Z.ZZ**

### AWS Lambda (Document Processing)

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Requests | | |
| Compute (GB-seconds) | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Requests: $X.XX × Y requests = $Z.ZZ
* Compute: $X.XX × Y GB-seconds = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Bedrock Data Automation

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Document Analysis | | |
| Image Processing | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Document Analysis: $X.XX × Y pages = $Z.ZZ
* Image Processing: $X.XX × Y images = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon EventBridge

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Custom Events | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions - Note: Likely free tier]*

##### Calculations
* Custom Events: Free (< 1M events)
* **Total: $0.00**

---

## Virtual Assistant Component

### Amazon Bedrock Guardrails

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Text Units Processed | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Text Units Processed: $X.XX × (Y units ÷ 1K) = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Bedrock Model Calls

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Input Tokens | | |
| Output Tokens | | |
| Cache Reads | | |
| Cache Writes | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Input Tokens: $X.XX × (Y tokens ÷ 1K) = $Z.ZZ
* Output Tokens: $X.XX × (Y tokens ÷ 1K) = $Z.ZZ
* Cache Reads: $X.XX × (Y tokens ÷ 1K) = $Z.ZZ
* Cache Writes: $X.XX × (Y tokens ÷ 1K) = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Bedrock AgentCore Runtime

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Agent Invocations | | |
| Compute Time | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Agent Invocations: $X.XX × Y invocations = $Z.ZZ
* Compute Time: $X.XX × Y seconds = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Bedrock AgentCore Gateway

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| API Calls | | |
| Data Processing | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* API Calls: $X.XX × Y calls = $Z.ZZ
* Data Processing: $X.XX × Y MB = $Z.ZZ
* **Total: $Z.ZZ**

### Amazon Bedrock Knowledge Bases

#### Estimated Single Medic

| Item | Usage | Monthly Cost |
|------|-------|--------------|
| Storage | | |
| Vector Queries | | |
| Ingestion | | |
| **Total** | | |

##### Detail
*[Description of usage patterns and assumptions]*

##### Calculations
* Storage: $X.XX × Y GB = $Z.ZZ
* Vector Queries: $X.XX × Y queries = $Z.ZZ
* Ingestion: $X.XX × Y documents = $Z.ZZ
* **Total: $Z.ZZ**

---

## Cost Summary

### Total Monthly Costs

| Component | Single Medic |
|-----------|--------------|
| **Frontend** | |
| **Backend** | |
| **Document Workflow** | |
| **Virtual Assistant** | |
| **Other Services** | ~$0 |
| **TOTAL** | |

### Key Assumptions
* Single doctor usage
* Shared infrastructure costs allocated proportionally
* Minimal document processing
* Basic AI assistant usage

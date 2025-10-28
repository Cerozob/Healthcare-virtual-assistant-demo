# Amazon Bedrock Guardrails Pricing

**Region:** US East (N. Virginia)  
**Service Code:** AmazonBedrock  
**Last Updated:** October 28, 2025  
**Source:** AWS Pricing API

## Overview

Amazon Bedrock Guardrails provides responsible AI safeguards for generative AI applications. It evaluates user inputs and model responses based on use case-specific policies, providing an additional layer of protection beyond native model safeguards.

## Pricing Model

Guardrails pricing is based on **text units** processed, where:
- **1 text unit = up to 1,000 characters**
- Text inputs longer than 1,000 characters are processed as multiple text units
- Each policy type is charged separately and can be enabled independently

## Policy Types and Pricing

### 1. Content Policy
**Purpose:** Filters harmful content (hate speech, violence, sexual content, etc.)

- **Text Processing:** $0.15 per 1,000 text units
- **Image Processing:** $0.75 per 1,000 images processed
- **Usage Type:** `ContentPolicyUnitsConsumed` / `ContentPolicyImageUnitsConsumed`

### 2. Topic Policy  
**Purpose:** Blocks or allows specific topics based on business requirements

- **Text Processing:** $0.15 per 1,000 text units
- **Usage Type:** `TopicPolicyUnitsConsumed`

### 3. Word Policy (Denied Words)
**Purpose:** Filters specific words or phrases

- **Text Processing:** $0.00 per 1,000 text units (FREE)
- **Usage Type:** `WordPolicyUnitsConsumed`

### 4. Sensitive Information Policy (PII Detection)
**Purpose:** Detects and redacts personally identifiable information

- **Free Tier:** $0.00 per 1,000 text units (limited usage)
- **Paid Tier:** $0.10 per 1,000 text units (after free tier)
- **Usage Types:** `SensitiveInformationPolicyFreeUnitsConsumed` / `SensitiveInformationPolicyPaidUnitsConsumed`

### 5. Contextual Grounding Policy
**Purpose:** Validates model responses against reference sources for accuracy

- **Text Processing:** $0.10 per 1,000 text units
- **Usage Type:** `ContextualGroundingPolicyUnitsConsumed`
- **Note:** Charges based on combined characters from source, query, and model response

### 6. Automated Reasoning Policy
**Purpose:** Provides provably truthful responses through logical reasoning

- **Text Processing:** $0.17 per 1,000 text units
- **Usage Type:** `AutomatedReasoningPolicyUnitsConsumed`

## Text Unit Calculation

### Character Count Examples
```
Example 1: "Hello, how are you?" (19 characters) = 1 text unit
Example 2: 5,600 character input = 6 text units (5,600 ÷ 1,000 = 5.6, rounded up to 6)
Example 3: Exactly 1,000 characters = 1 text unit
```

### Multi-Policy Processing
If multiple policies are enabled, each policy is charged separately:
```
Input: 2,000 characters with Content + PII policies enabled
- Content Policy: 2 text units × $0.15/1K = $0.0003
- PII Policy: 2 text units × $0.10/1K = $0.0002
- Total: $0.0005
```

## Healthcare Use Case Pricing

### Recommended Policy Configuration for Healthcare
1. **Content Policy:** Filter harmful content
2. **PII Detection:** Protect patient information (HIPAA compliance)
3. **Contextual Grounding:** Ensure medical accuracy
4. **Topic Policy:** Block inappropriate medical topics

### Healthcare Pricing Example
```
Configuration: All recommended policies enabled
Average interaction: 3,000 characters (input + output)
Text units per interaction: 3

Cost per interaction:
- Content Policy: 3 × $0.15/1K = $0.00045
- PII Detection: 3 × $0.10/1K = $0.00030
- Contextual Grounding: 3 × $0.10/1K = $0.00030
- Topic Policy: 3 × $0.15/1K = $0.00045
Total per interaction: $0.0015
```

## Usage Patterns and Optimization

### Cost Optimization Strategies

1. **Selective Policy Application:**
   - Apply expensive policies (Automated Reasoning) only to critical interactions
   - Use free policies (Word Policy) where appropriate
   - Enable PII detection only for sensitive content

2. **Text Optimization:**
   - Minimize unnecessary text in prompts and responses
   - Use efficient prompt engineering to reduce token count
   - Implement client-side pre-filtering for obvious violations

3. **Policy Layering:**
   - Start with free/cheap policies (Word Policy, Content Policy)
   - Apply expensive policies (Automated Reasoning) only when needed
   - Use contextual grounding selectively for fact-checking

## Regional Availability

- **US East (N. Virginia):** All policies available
- **US West (Oregon):** All policies available
- **Europe (Frankfurt):** Limited policy availability
- **Asia Pacific (Tokyo):** Limited policy availability

## Pricing Examples

### Example 1: Customer Support Chatbot
```
Configuration:
- Content Policy + PII Detection enabled
- 10,000 interactions/month
- Average 1,500 characters per interaction

Monthly Cost:
- Text units: 10,000 × 2 = 20,000 text units
- Content Policy: 20,000 × $0.15/1K = $3.00
- PII Detection: 20,000 × $0.10/1K = $2.00
- Total: $5.00/month
```

### Example 2: Healthcare AI Assistant (Production)
```
Configuration:
- All policies enabled (Content, PII, Contextual Grounding, Topic)
- 2M interactions/month (10K MAU × 20 sessions × 10 interactions)
- Average 3,000 characters per interaction (input + output)

Monthly Cost:
- Text units: 2M × 3 = 6M text units
- Content Policy: 6M × $0.15/1K = $900
- PII Detection: 6M × $0.10/1K = $600
- Contextual Grounding: 6M × $0.10/1K = $600
- Topic Policy: 6M × $0.15/1K = $900
- Total: $3,000/month
```

### Example 3: Document Processing with Image Analysis
```
Configuration:
- Content Policy for text and images
- PII Detection for documents
- 100K documents/month with 2K characters each
- 50K images/month

Monthly Cost:
- Text processing: 100K × 2 = 200K text units
- Content Policy (text): 200K × $0.15/1K = $30
- PII Detection: 200K × $0.10/1K = $20
- Content Policy (images): 50K × $0.75/1K = $37.50
- Total: $87.50/month
```

### Example 4: High-Accuracy Medical System
```
Configuration:
- All policies including Automated Reasoning
- 500K medical queries/month
- Average 4,000 characters per interaction

Monthly Cost:
- Text units: 500K × 4 = 2M text units
- Content Policy: 2M × $0.15/1K = $300
- PII Detection: 2M × $0.10/1K = $200
- Contextual Grounding: 2M × $0.10/1K = $200
- Topic Policy: 2M × $0.15/1K = $300
- Automated Reasoning: 2M × $0.17/1K = $340
- Total: $1,340/month
```

## Integration Considerations

### With Foundation Models
- **Processing Order:** Guardrails can process input before model inference and/or output after model response
- **Token Impact:** Guardrails processing doesn't affect model token counts
- **Latency:** Each policy adds processing time (typically 50-200ms per policy)

### With Third-Party Models
- **Universal Compatibility:** Guardrails work with any model via ApplyGuardrail API
- **External Models:** Can be used with OpenAI, Google Gemini, etc.
- **Agent Frameworks:** Compatible with Strands Agents and other frameworks

### With Bedrock AgentCore
- **Native Integration:** Guardrails automatically apply to AgentCore deployments
- **Policy Inheritance:** Policies configured at the guardrail level apply to all agent interactions
- **Performance:** Optimized for low-latency agent responses

## Monitoring and Optimization

### Key Metrics to Track
1. **Text Units Processed:** Monitor usage across all policies
2. **Policy Violation Rates:** Track how often each policy triggers
3. **Cost per Interaction:** Monitor unit economics
4. **Processing Latency:** Track impact on response times

### Cost Management Best Practices
1. **Policy Auditing:** Regularly review which policies are necessary
2. **Usage Analytics:** Monitor text unit consumption patterns
3. **Threshold Management:** Set appropriate sensitivity levels
4. **Batch Processing:** Group similar content when possible

## Important Notes

1. **Policy Independence:** Each policy is optional and charged separately
2. **Character Counting:** Includes all characters (spaces, punctuation, etc.)
3. **Rounding:** Text units are rounded up (1,001 characters = 2 text units)
4. **Free Tier:** Some policies have free tiers (Word Policy, limited PII detection)
5. **Image Processing:** Separate pricing for image content analysis
6. **Contextual Grounding:** Charges based on combined source + query + response text

## References

- AWS Bedrock Pricing Page: https://aws.amazon.com/bedrock/pricing/
- Bedrock Guardrails Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html
- AWS Pricing API: AmazonBedrock service
- Responsible AI Best Practices: https://aws.amazon.com/machine-learning/responsible-ai/

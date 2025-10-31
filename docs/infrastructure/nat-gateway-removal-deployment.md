# NAT Gateway Removal - Deployment Guide

## Pre-Deployment Checklist

### 1. Verify Current State
```bash
# Check current NAT Gateway usage
aws ec2 describe-nat-gateways --region us-east-1

# Check current VPC configuration
aws ec2 describe-vpcs --region us-east-1 --filters "Name=tag:Name,Values=*Healthcare*"

# Verify Lambda functions are not in VPC
aws lambda list-functions --region us-east-1 | grep -A 5 -B 5 healthcare
```

### 2. Backup Current Configuration
```bash
# Export current CDK state
cdk synth > backup-before-nat-removal.yaml

# Document current costs
aws ce get-cost-and-usage --time-period Start=2025-10-01,End=2025-10-30 \
  --granularity MONTHLY --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Deployment Steps

### Step 1: Deploy Infrastructure Changes
```bash
# Deploy the backend stack with NAT Gateway removal
cdk deploy AWSomeBuilder2-BackendStack

# Expected changes:
# - Remove NAT Gateway
# - Change subnets to PRIVATE_ISOLATED
# - Add VPC Endpoints (S3, Secrets Manager, SSM, RDS)
```

### Step 2: Verify VPC Endpoints
```bash
# Check VPC endpoints were created
aws ec2 describe-vpc-endpoints --region us-east-1 \
  --filters "Name=vpc-id,Values=$(aws ec2 describe-vpcs --filters 'Name=tag:Name,Values=*Healthcare*' --query 'Vpcs[0].VpcId' --output text)"

# Expected endpoints:
# - S3 (Gateway)
# - Secrets Manager (Interface)
# - SSM (Interface) 
# - RDS (Interface)
```

### Step 3: Test Database Connectivity
```bash
# Test RDS Data API access
aws rds-data execute-statement \
  --resource-arn "$(aws ssm get-parameter --name /healthcare/database/cluster-arn --query Parameter.Value --output text)" \
  --secret-arn "$(aws ssm get-parameter --name /healthcare/database/secret-arn --query Parameter.Value --output text)" \
  --database healthcare \
  --sql "SELECT 1 as test"
```

### Step 4: Test Lambda Functions
```bash
# Test each Lambda function
aws lambda invoke --function-name healthcare-patients \
  --payload '{"httpMethod":"GET","path":"/patients"}' \
  response.json && cat response.json

aws lambda invoke --function-name healthcare-medics \
  --payload '{"httpMethod":"GET","path":"/medics"}' \
  response.json && cat response.json
```

### Step 5: Verify Cost Changes
```bash
# Check NAT Gateway is removed
aws ec2 describe-nat-gateways --region us-east-1 \
  --filters "Name=state,Values=available"

# Should return empty or no healthcare-related NAT Gateways
```

## Post-Deployment Verification

### 1. Application Testing
- [ ] Frontend loads correctly
- [ ] API endpoints respond
- [ ] Database queries work
- [ ] File uploads/downloads work
- [ ] AgentCore functionality works

### 2. Monitoring Setup
```bash
# Set up CloudWatch alarms for VPC endpoint usage
aws cloudwatch put-metric-alarm \
  --alarm-name "VPC-Endpoint-Errors" \
  --alarm-description "Monitor VPC endpoint errors" \
  --metric-name ErrorCount \
  --namespace AWS/VPC \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### 3. Cost Monitoring
- Monitor AWS Cost Explorer for NAT Gateway charges (should be $0)
- Monitor VPC Endpoint charges (should be ~$21/month)
- Verify overall cost reduction

## Rollback Procedure

If issues are detected, rollback with:

```bash
# 1. Revert infrastructure changes
git checkout HEAD~1 infrastructure/stacks/backend_stack.py

# 2. Deploy rollback
cdk deploy AWSomeBuilder2-BackendStack

# 3. Verify NAT Gateway is restored
aws ec2 describe-nat-gateways --region us-east-1
```

## Expected Outcomes

### Cost Impact
- **Immediate**: NAT Gateway charges stop (~$45-55/month savings)
- **New Costs**: VPC Endpoints (~$21/month)
- **Net Savings**: ~$24-34/month ($288-408/year)

### Performance Impact
- **Database**: No change (isolated subnets)
- **Lambda**: No change (not in VPC)
- **AgentCore**: No change (managed service)

### Security Impact
- **Improved**: Database in isolated subnets
- **Improved**: No internet gateway access for database
- **Maintained**: Same access controls via VPC endpoints

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check VPC endpoints are in correct subnets
   - Verify security group rules
   - Ensure RDS Data API is enabled

2. **Lambda Function Errors**
   - Lambda functions should NOT be affected (they're not in VPC)
   - Check IAM permissions for AWS service access

3. **VPC Endpoint DNS Resolution**
   - Ensure `enable_dns_hostnames=True` and `enable_dns_support=True`
   - Check VPC endpoint policy allows access

### Monitoring Commands
```bash
# Check VPC endpoint status
aws ec2 describe-vpc-endpoints --region us-east-1

# Monitor VPC endpoint metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPC \
  --metric-name PacketDropCount \
  --start-time 2025-10-30T00:00:00Z \
  --end-time 2025-10-30T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Success Criteria

- [ ] All application functionality works
- [ ] NAT Gateway charges eliminated
- [ ] VPC Endpoints operational
- [ ] Database connectivity maintained
- [ ] No performance degradation
- [ ] Cost savings achieved

---

**Next Steps**: Monitor for 48 hours, then update cost estimation documentation with actual savings.

#!/bin/bash

# Document Workflow Testing Script
# Tests the complete document processing pipeline

set -e

echo "🧪 Healthcare Document Workflow Testing"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "apps/frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Get stack outputs
echo "📋 Getting stack information..."

RAW_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name AWSomeBuilder2-DocumentWorkflowStack \
    --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -z "$RAW_BUCKET" ]; then
    echo "❌ Error: Could not get raw bucket name from CloudFormation stack"
    echo "💡 Make sure the DocumentWorkflowStack is deployed"
    exit 1
fi

echo "✅ Found raw bucket: $RAW_BUCKET"

# Create test documents directory
TEST_DIR="test-documents"
mkdir -p "$TEST_DIR"

echo "📄 Creating test documents..."

# Create a sample medical document
cat > "$TEST_DIR/patient-record-001.txt" << 'EOF'
PATIENT MEDICAL RECORD

Patient Name: John Doe
Patient ID: P001
Date of Birth: 1985-03-15
Date of Visit: 2024-10-19

CHIEF COMPLAINT:
Patient presents with chest pain and shortness of breath.

HISTORY OF PRESENT ILLNESS:
45-year-old male with a 2-day history of chest pain, described as sharp and radiating to the left arm. Associated with shortness of breath and diaphoresis. No previous cardiac history.

PHYSICAL EXAMINATION:
- Vital Signs: BP 140/90, HR 95, RR 22, Temp 98.6°F
- Cardiovascular: Regular rate and rhythm, no murmurs
- Pulmonary: Clear to auscultation bilaterally
- Extremities: No edema

ASSESSMENT AND PLAN:
1. Chest pain - rule out acute coronary syndrome
   - Order EKG and cardiac enzymes
   - Start aspirin 325mg
   - Monitor in observation unit

2. Hypertension
   - Start lisinopril 10mg daily
   - Follow up in 2 weeks

DISPOSITION:
Patient admitted to observation unit for cardiac monitoring.

Dr. Sarah Smith, MD
Internal Medicine
EOF

# Create a sample lab report
cat > "$TEST_DIR/lab-report-001.txt" << 'EOF'
LABORATORY REPORT

Patient: John Doe (P001)
Date Collected: 2024-10-19 08:00 AM
Date Reported: 2024-10-19 10:30 AM

COMPLETE BLOOD COUNT:
- WBC: 7.2 K/uL (Normal: 4.0-11.0)
- RBC: 4.5 M/uL (Normal: 4.2-5.4)
- Hemoglobin: 14.2 g/dL (Normal: 12.0-16.0)
- Hematocrit: 42% (Normal: 36-46)
- Platelets: 250 K/uL (Normal: 150-450)

BASIC METABOLIC PANEL:
- Glucose: 95 mg/dL (Normal: 70-100)
- BUN: 18 mg/dL (Normal: 7-20)
- Creatinine: 1.0 mg/dL (Normal: 0.6-1.2)
- Sodium: 140 mEq/L (Normal: 136-145)
- Potassium: 4.0 mEq/L (Normal: 3.5-5.1)

CARDIAC ENZYMES:
- Troponin I: 0.02 ng/mL (Normal: <0.04)
- CK-MB: 2.1 ng/mL (Normal: 0.0-6.3)

INTERPRETATION:
All values within normal limits. Cardiac enzymes negative for myocardial infarction.

Lab Director: Dr. Michael Johnson, MD
EOF

# Create a sample prescription
cat > "$TEST_DIR/prescription-001.txt" << 'EOF'
PRESCRIPTION

Patient: John Doe
DOB: 03/15/1985
Address: 123 Main St, Anytown, ST 12345

Date: 10/19/2024

Rx:
1. Lisinopril 10mg tablets
   Sig: Take 1 tablet by mouth daily
   Disp: #30 tablets
   Refills: 2

2. Aspirin 81mg tablets
   Sig: Take 1 tablet by mouth daily
   Disp: #90 tablets
   Refills: 3

Dr. Sarah Smith, MD
DEA: BS1234567
NPI: 1234567890
EOF

echo "✅ Test documents created in $TEST_DIR/"

# Upload test documents
echo "📤 Uploading test documents to S3..."

for file in "$TEST_DIR"/*.txt; do
    filename=$(basename "$file")
    echo "   Uploading $filename..."
    
    aws s3 cp "$file" "s3://$RAW_BUCKET/documents/$filename" \
        --metadata "patient-id=P001,document-type=medical-record,test=true"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $filename uploaded successfully"
    else
        echo "   ❌ Failed to upload $filename"
    fi
done

echo ""
echo "🔍 Monitoring workflow execution..."
echo "You can monitor the workflow in the AWS Console:"
echo ""
echo "1. 📊 CloudWatch Logs:"
echo "   - BDA Trigger: /aws/lambda/healthcare-bda-trigger"
echo "   - Data Extraction: /aws/lambda/healthcare-data-extraction"
echo ""
echo "2. 📁 S3 Buckets:"
echo "   - Raw: $RAW_BUCKET"
echo "   - Processed: (check CloudFormation outputs)"
echo ""
echo "3. 🎯 EventBridge:"
echo "   - Rule: healthcare-bda-completion"
echo ""
echo "4. 🤖 Bedrock Data Automation:"
echo "   - Check Bedrock console for processing status"
echo ""

# Wait a bit and check for processed files
echo "⏳ Waiting 30 seconds for initial processing..."
sleep 30

echo "🔍 Checking for processed files..."
PROCESSED_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name AWSomeBuilder2-DocumentWorkflowStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ProcessedBucketName`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$PROCESSED_BUCKET" ]; then
    echo "📁 Processed bucket: $PROCESSED_BUCKET"
    aws s3 ls "s3://$PROCESSED_BUCKET/" --recursive || echo "No processed files yet (this is normal for initial processing)"
else
    echo "ℹ️  Processed bucket name not found in outputs (check manually)"
fi

echo ""
echo "✅ Document workflow test initiated!"
echo "📝 Test files uploaded. Check AWS Console for processing results."
echo ""
echo "🧹 Cleanup:"
echo "   To remove test files: rm -rf $TEST_DIR"
echo "   To remove from S3: aws s3 rm s3://$RAW_BUCKET/documents/ --recursive"

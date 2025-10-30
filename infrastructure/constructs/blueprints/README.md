# BDA Medical Blueprints

This directory contains JSON blueprint definitions for AWS Bedrock Data Automation (BDA) medical document processing.

## Blueprint Files

### 1. medical-record-blueprint.json
**Purpose**: Extract structured data from medical records (PDFs, Word documents)

**Key Fields**:
- **Enhanced PII/PHI Detection**: Comprehensive extraction of personally identifiable and protected health information
  - Patient demographics (name, DOB, age, gender)
  - Government IDs (passport, national ID, social security number)
  - Contact information (phone, email, address, emergency contacts)
  - Medical identifiers (MRN, insurance numbers)
  - Employment information
  - Fallback field for unclassified PII/PHI
- Medical information (diagnoses with ICD codes, medications, allergies)
- Vital signs and physical measurements
- Symptoms and treatment plans

**Document Types**: PDF, DOC, DOCX

### 2. medical-image-blueprint.json
**Purpose**: Extract information from medical images

**Key Fields**:
- **Enhanced PII/PHI Detection**: Extraction of personal information visible in medical images
  - Patient demographics (name, DOB, age, gender)
  - Contact information (phone, address)
  - Medical identifiers and facility information
  - Fallback field for unclassified PII/PHI
- Image analysis (type, body part, anatomical view)
- Medical findings and abnormalities
- Measurements and quality assessment

**Document Types**: JPEG, PNG, TIFF, DICOM

### 3. medical-audio-blueprint.json
**Purpose**: Transcribe and extract data from medical audio recordings

**Key Fields**:
- **Enhanced PII/PHI Detection**: Extraction of personal information from audio content
  - Patient demographics (name, DOB, age, gender)
  - Contact information (phone, address)
  - Government and medical identifiers
  - Insurance information
  - Fallback field for unclassified PII/PHI
- Medical content (transcript summary, chief complaint, symptoms)
- Physical examination findings
- Assessment and treatment plan
- Medications discussed

**Document Types**: MP3, WAV, MP4, M4A

**Features**:
- Speaker diarization
- Medical terminology recognition
- Confidence thresholds

### 4. medical-video-blueprint.json
**Purpose**: Extract information from medical videos

**Key Fields**:
- **Enhanced PII/PHI Detection**: Extraction of personal information from video content
  - Patient demographics (name, DOB, age, gender)
  - Contact information (phone, address)
  - Medical identifiers and healthcare provider names
  - Fallback field for unclassified PII/PHI
- Video analysis (type, procedure classification)
- Visual observations and key frames
- Audio transcription and medical content
- Procedure steps and outcomes

**Document Types**: MP4, AVI, MOV, WMV

**Features**:
- Frame extraction
- Object detection
- Audio transcription

## Blueprint Structure

Each blueprint follows the AWS BDA JSON structure:

```json
{
  "name": "unique_blueprint_name",
  "description": "Blueprint description",
  "fields": [
    {
      "name": "field_name",
      "description": "Natural language explanation of the field",
      "type": "string|number|boolean|array",
      "inferenceType": "inferred",
      "granularity": "frame|segment" // for video fields only
    }
  ]
}
```

## Field Types

- **string**: For text-based values
- **number**: For numerical values  
- **boolean**: For true/false values
- **array**: For fields that can have multiple values

## Inference Type

All fields use `"inferenceType": "inferred"` which means BDA infers the field value based on the information present in the document.

## Video Granularity

For video blueprints, fields can include a `granularity` option:
- **frame**: Extract information from specific frames
- **segment**: Extract information from video segments

## Usage in CDK

The blueprints are automatically loaded by the `BDABlueprintsConstruct`:

```python
from infrastructure.constructs.bda_blueprints_construct import BDABlueprintsConstruct

# Create blueprints
bda_blueprints = BDABlueprintsConstruct(self, "BDABlueprints")

# Get blueprint ARNs
medical_record_arn = bda_blueprints.get_blueprint_arn("medical_record")
all_arns = bda_blueprints.get_all_blueprint_arns()

# Get project and profile ARNs
project_arn = bda_blueprints.get_project_arn()
profile_arn = bda_blueprints.get_profile_arn()
```

## Enhanced PII/PHI Detection

All blueprints have been enhanced with comprehensive PII/PHI detection capabilities to ensure HIPAA compliance and data privacy protection.

### Detected PII/PHI Categories

**Personal Identifiers:**
- Full names (patient, healthcare providers, emergency contacts)
- Date of birth (multiple formats supported)
- Age and gender/sex
- Government identification numbers (passport, national ID, social security)
- Contact information (phone numbers with country codes, email addresses, physical addresses)

**Medical Identifiers:**
- Medical record numbers (MRN)
- Patient identifiers and account numbers
- Health insurance numbers and policy information
- Healthcare facility information

**Employment & Financial:**
- Employer information
- Bank account numbers
- Credit card numbers (if present in medical billing contexts)

**Biometric & Technical:**
- Biometric identifiers (fingerprints, facial recognition data, genetic information)
- Device identifiers and serial numbers
- IP addresses and geolocation data
- Web URLs containing personal information

**Fallback Detection:**
Each blueprint includes an `other_pii_phi` field with the instruction: "Look for any other Unclassified PIIs/PHIs not captured in the above fields" to ensure comprehensive coverage of any PII/PHI that doesn't fit standard categories.

### Multi-Language Support

The enhanced detection works across multiple languages and formats, including:
- Spanish medical documents (as shown in sample: "Ana Isabel Castillo Jiménez", "Femenino", etc.)
- Various date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
- International phone number formats with country codes
- Different naming conventions for government IDs across countries

## Customization

To modify a blueprint:

1. Edit the corresponding JSON file
2. Update field definitions as needed
3. Deploy the CDK stack to apply changes

To add a new blueprint:

1. Create a new JSON file in this directory
2. Add it to the `blueprint_files` dictionary in `bda_blueprints_construct.py`
3. Update the lambda environment variables if needed

## Language Support

All blueprints are configured for Spanish (`"language": "es"`) but can be modified to support other languages by changing the language field and updating field descriptions accordingly.

## Medical Specialties

Blueprints can be tagged with specific medical specialties:
- `general` - General medicine
- `radiology` - Radiology and imaging
- `cardiology` - Cardiovascular medicine
- `oncology` - Cancer treatment
- `pediatrics` - Pediatric medicine

This helps with organization and specialized processing requirements.

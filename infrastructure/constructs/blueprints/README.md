# BDA Medical Blueprints

This directory contains JSON blueprint definitions for AWS Bedrock Data Automation (BDA) medical document processing.

## Blueprint Files

### 1. medical-record-blueprint.json
**Purpose**: Extract structured data from medical records (PDFs, Word documents)

**Key Fields**:
- Patient information (name, DOB, MRN, contact info)
- Diagnoses with ICD codes
- Medications and dosages
- Allergies and vital signs
- Symptoms and treatment plans

**Document Types**: PDF, DOC, DOCX

### 2. medical-image-blueprint.json
**Purpose**: Extract information from medical images

**Key Fields**:
- Image type (X-ray, MRI, CT, etc.)
- Body part and anatomical view
- Medical findings and abnormalities
- Measurements and quality assessment
- Patient identifiers (anonymized)

**Document Types**: JPEG, PNG, TIFF, DICOM

### 3. medical-audio-blueprint.json
**Purpose**: Transcribe and extract data from medical audio recordings

**Key Fields**:
- Full transcript with speaker identification
- Chief complaint and symptoms
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
- Video type (procedure, consultation, etc.)
- Key frames with timestamps
- Visual observations
- Audio transcription
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

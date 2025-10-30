# Synthetic Medical Data Generator

Generates realistic synthetic patient profiles and medical documents in Latin American Spanish using AWS Bedrock and Strands framework.

## Features

- Realistic patient profiles with Latin American naming conventions
- Medical document generation (clinical histories, lab results, prescriptions)
- Multimodal AI analysis of scanned medical documents
- Structured output using Pydantic models
- End-to-end processing with fault tolerance

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Generate 5 patients
python medical_records_generator.py

# Generate with custom count
python medical_records_generator.py --count 20
```

## Configuration

Edit `config.json` for your settings:

```json
{
  "bedrock": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "region": "us-east-1"
  },
  "generation": {
    "language": "es-LA",
    "document_types": ["historia_clinica", "resultados_laboratorio", "receta_medica"]
  }
}
```

## Data Sources

1. **MIMIC IV FHIR Data**: Download from PhysioNet
2. **Healthcare CSV**: Demographic data file
3. **Scanned Documents**: Reference documents for multimodal analysis

## Output Structure

```text
output/
├── patient_uuid1/
│   ├── patient_uuid1_profile.json
│   ├── reference_scan.jpg
│   └── *.pdf documents
└── generation_summary.json
```

## Technologies

- AWS Bedrock for AI generation
- Strands framework for structured output
- Pydantic models for type safety
- Multimodal document analysis

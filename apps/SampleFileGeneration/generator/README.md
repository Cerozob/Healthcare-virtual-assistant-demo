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

## Token Handling

The generator handles large context windows and token limits automatically:

- **Automatic Chunking**: Large documents are split into manageable chunks
- **Context Preservation**: Important context is maintained across chunks
- **Error Recovery**: Graceful handling of token limit errors with retry logic
- **Progress Tracking**: Real-time feedback on generation progress

### Best Practices

- Keep reference documents under 100KB for optimal performance
- Use structured data sources (JSON, CSV) for demographic information
- Monitor token usage in CloudWatch logs
- Adjust `max_tokens` in config.json based on document complexity

## Usage Guide

### Basic Usage

```bash
# Generate default number of patients (5)
python medical_records_generator.py

# Generate specific number
python medical_records_generator.py --count 20

# Use custom configuration
python medical_records_generator.py --config custom_config.json
```

### Advanced Configuration

Edit `config.json` to customize generation:

```json
{
  "bedrock": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "region": "us-east-1",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "generation": {
    "language": "es-LA",
    "document_types": [
      "historia_clinica",
      "resultados_laboratorio",
      "receta_medica",
      "orden_examen"
    ],
    "include_scans": true,
    "output_format": "pdf"
  },
  "data_sources": {
    "mimic_path": "data/mimic-iv-clinical-database-demo-on-fhir-2.1.0",
    "healthcare_csv": "data/healthcare_dataset.csv",
    "reference_scans": "data/lbmaske"
  }
}
```

### Output Processing

Generated files are organized by patient UUID:

```text
output/
├── patient_uuid1/
│   ├── patient_uuid1_profile.json      # Patient demographics and metadata
│   ├── reference_scan.jpg              # Scanned document reference
│   ├── historia_clinica.pdf            # Clinical history
│   ├── resultados_laboratorio.pdf      # Lab results
│   └── receta_medica.pdf               # Prescription
└── generation_summary.json             # Overall generation statistics
```

### Error Handling

The generator includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Token Limits**: Automatic content chunking and retry
- **Invalid Data**: Validation and fallback to default values
- **File I/O**: Graceful handling of missing or corrupted files

Check logs in `output/generation.log` for detailed error information.

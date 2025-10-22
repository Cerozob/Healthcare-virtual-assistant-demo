# Synthetic Medical Data Generator

A Python application that generates realistic synthetic patient profiles and medical documents in Latin American Spanish using AWS Bedrock foundation models through the Strands framework with structured output and multimodal capabilities.

## Overview

This generator combines multiple data sources and advanced AI capabilities to create comprehensive synthetic medical data:

- **MIMIC IV FHIR data**: Real medical patterns from de-identified hospital data
- **Healthcare CSV datasets**: Demographic information for realistic patient profiles
- **Scanned Medical Documents**: Reference documents for multimodal AI analysis
- **AWS Bedrock**: AI-powered content generation with structured output validation
- **Strands Framework**: Type-safe, validated responses using Pydantic models

## Features

- 🏥 **Realistic Patient Profiles**: Generates comprehensive patient information with Latin American naming conventions, addresses, and medical history
- 📄 **Medical Document Generation**: Creates PDF documents including clinical histories, lab results, and prescriptions
- 🌎 **Latin American Spanish**: All content generated in appropriate medical Spanish terminology
- 🔄 **End-to-End Processing**: Efficient one-patient-at-a-time generation for memory optimization and fault tolerance
- ✅ **Structured Output**: Type-safe, validated responses using Pydantic models - no JSON parsing errors
- �️ **Muxltimodal Capabilities**: Analyzes scanned medical documents to generate similar synthetic patients
- 📋 **Complete Packages**: Each patient includes original reference scan + generated documents
- 🎯 **Enhanced Realism**: Patients based on real medical document patterns for higher quality synthetic data
- 📊 **Flexible Output**: Organized file structure with JSON profiles and PDF documents

## Installation

### Prerequisites

- Python 3.8 or higher
- AWS account with Bedrock access
- AWS credentials configured (via AWS CLI, environment variables, or IAM roles)

### Install Dependencies

```bash
cd apps/SampleFileGeneration/generator
pip install -r requirements.txt
```

### AWS Configuration

Ensure your AWS credentials are configured with access to Amazon Bedrock:

```bash
aws configure
```

Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

## Configuration

### Configuration File

The generator uses a JSON configuration file. You can use the provided schema for validation and documentation:

```bash
# View the complete schema with examples and documentation
cat config.json.schema
```

Create your configuration file with your specific settings:

```json
{
  "data_sources": {
    "fhir_dir": "path/to/mimic-iv-fhir-data",
    "csv_path": "path/to/healthcare_dataset.csv",
    "template_dir": "path/to/pdf/templates"
  },
  "output": {
    "base_dir": "output",
    "organize_by_patient": true
  },
  "bedrock": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "inference_profile_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "region": "us-east-1",
    "max_tokens": 4096,
    "temperature": 0.7,
    "use_inference_profile": false
  },
  "generation": {
    "language": "es-LA",
    "batch_size": 10,
    "document_types": ["historia_clinica", "resultados_laboratorio", "receta_medica"]
  },
  "validation": {
    "max_retries": 3,
    "enable_coherence_check": true
  }
}
```

#### Bedrock Model Configuration

The generator supports two ways to access Bedrock models:

##### Option 1: Direct Model Access (default)

```json
{
  "bedrock": {
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "use_inference_profile": false,
    "region": "us-east-1"
  }
}
```

##### Option 2: Inference Profile (recommended for production)

```json
{
  "bedrock": {
    "inference_profile_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "use_inference_profile": true,
    "region": "us-east-1"
  }
}
```

##### Inference Profiles Benefits

- **Cross-region resilience**: Automatically routes requests to available regions
- **Higher throughput**: Better performance and availability
- **Cost optimization**: Potential cost savings through intelligent routing
- **Simplified management**: Single identifier for multiple regions

Available inference profiles include:

- `us.anthropic.claude-3-5-sonnet-20241022-v2:0`
- `us.anthropic.claude-3-5-haiku-20241022-v1:0`
- `us.anthropic.claude-3-opus-20240229-v1:0`
- `us.meta.llama-3-2-90b-instruct-v1:0`

For the complete list, see the [AWS Bedrock Inference Profiles documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html).

## Usage

### Basic Usage

Generate 5 patients with structured output and multimodal capabilities:

```bash
python medical_records_generator.py
```

### Advanced Usage

```bash
# Generate 20 patients with structured output and multimodal input
python medical_records_generator.py --count 20

# Use custom configuration file
python medical_records_generator.py --config my_config.json

# Enable debug logging to see multimodal analysis details
python medical_records_generator.py --count 5 --log-level DEBUG

# Test structured output functionality
python test_structured_output.py

# See usage examples and capabilities
python example_usage.py
```

### Command Line Options

- `--count, -c`: Number of patients to generate (default: 5)
- `--config`: Path to configuration file (default: config.json)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--recover-only`: Only recover incomplete patients from intermediate storage

### Testing and Examples

- `test_structured_output.py`: Test structured output and multimodal capabilities
- `example_usage.py`: Comprehensive usage examples and demonstrations

## Output Structure

The generator creates organized output with the following structure:

```text
output/
├── generation_summary.json          # Batch generation summary
├── patient_uuid1/                   # Patient-specific directory
│   ├── patient_uuid1_profile.json   # Patient profile data (structured)
│   ├── reference_scan.jpg           # 🆕 Original reference medical scan
│   ├── patient_uuid1_historia_clinica_20241021_143022.pdf
│   ├── patient_uuid1_resultados_laboratorio_20241021_143023.pdf
│   └── patient_uuid1_receta_medica_20241021_143024.pdf
├── patient_uuid2/
│   └── ...
└── generator.log                    # Application logs
```

### Patient Profile Format

Each patient profile is saved as JSON with the following structure:

```json
{
  "patient_id": "uuid",
  "personal_info": {
    "nombre_completo": "María Elena García Rodríguez",
    "primer_nombre": "María",
    "segundo_nombre": "Elena",
    "primer_apellido": "García",
    "segundo_apellido": "Rodríguez",
    "fecha_nacimiento": "15/03/1985",
    "edad": 39,
    "sexo": "F",
    "tipo_documento": "DNI",
    "numero_documento": "12345678",
    "direccion": {
      "calle": "Calle 25",
      "numero": "1234",
      "ciudad": "Buenos Aires",
      "provincia": "Buenos Aires",
      "codigo_postal": "1000",
      "pais": "Argentina"
    },
    "telefono": "+54 1123456789",
    "email": "maria.garcia@gmail.com"
  },
  "medical_history": {
    "conditions": [...],
    "medications": [...],
    "procedures": [...]
  },
  "lab_results": [...],
  "source_scan": "reference_scan.jpg",  // 🆕 Reference scan used for generation
  "generated_documents": [...]
}
```

## Data Sources

### Required Data Files

1. **MIMIC IV FHIR Data**: Download from [PhysioNet](https://physionet.org/content/mimic-iv-fhir/2.1.0/)
   - Extract to `apps/SampleFileGeneration/data/mimic-iv-clinical-database-demo-on-fhir-2.1.0/fhir/`

2. **Healthcare Dataset CSV**: Demographic data file
   - Place at `apps/SampleFileGeneration/data/healthcare_dataset.csv`

3. **Scanned Medical Documents**: Reference documents for multimodal AI analysis
   - Place in `apps/SampleFileGeneration/data/lbmaske/`
   - Supported formats: .jpg, .jpeg, .png, .pdf
   - **How it works**: AI analyzes these scans to extract medical patterns and generates similar synthetic patients
   - **Benefits**: Higher realism, better medical coherence, learning from real document structures

### Data Privacy

- All generated data is synthetic and contains no real patient information
- MIMIC IV data is de-identified and publicly available
- Generated profiles use fictional names and contact information

## Core Technologies

### Structured Output with Pydantic Models

The generator uses validated Pydantic models for all AI responses:

- **`PatientProfile`**: Complete patient data structure with validation
- **`DocumentNarratives`**: All document types in structured format
- **`ScannedDocumentAnalysis`**: Analysis results from multimodal input
- **Benefits**: No JSON parsing errors, type safety, guaranteed data structure

### Multimodal AI Capabilities

The system analyzes scanned medical documents to generate similar patients:

1. **Document Analysis**: Extracts patient info, conditions, medications, lab values
2. **Pattern Learning**: AI learns from real medical document structures
3. **Similar Generation**: Creates synthetic patients with similar characteristics
4. **Reference Preservation**: Copies original scan to patient output folder

### Enhanced Workflow

```text
Reference Scan → AI Analysis → Similar Patient Generation → Document Creation → Complete Package
```

## Supported Document Types

- `historia_clinica`: Complete clinical history
- `resultados_laboratorio`: Laboratory results report
- `receta_medica`: Medical prescription
- `informe_medico`: General medical report

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**

   ```text
   Error: Unable to locate credentials
   ```

   Solution: Configure AWS credentials using `aws configure` or environment variables

2. **Bedrock Model Access**

   ```text
   Error: Access denied to model
   ```

   Solution: Request access to the Bedrock model in the AWS console

3. **Missing Data Files**

   ```text
   Error: FHIR data directory not found
   ```

   Solution: Download and extract MIMIC IV FHIR data to the correct location

4. **Memory Issues**

   ```text
   Error: Out of memory
   ```

   Solution: Reduce batch size in configuration or generate fewer patients

5. **Inference Profile Not Found**

   ```text
   Error: Inference profile not found
   ```

   Solution: Verify the inference profile ID is correct and available in your region. Check the [AWS documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html) for available profiles.

6. **Invalid Configuration**

   ```text
   Error: model_id is required when use_inference_profile=False
   ```

   Solution: Ensure either `model_id` (for direct model access) or `inference_profile_id` (for inference profiles) is properly configured based on the `use_inference_profile` setting.

### Logging

The application logs to both console and `generator.log` file. Use `--log-level DEBUG` for detailed troubleshooting information.

### Performance Tips

- Each patient is processed end-to-end individually for optimal memory usage and fault tolerance
- **Structured output** eliminates JSON parsing errors and improves reliability
- **Batch document generation** creates all narratives in a single API call
- **Multimodal analysis** is cached per scan to avoid repeated processing
- Consider using Bedrock's Haiku model for faster, less expensive generation
- FHIR data is loaded once per session and reused for all patients
- Failed patients don't affect the generation of subsequent patients

## Development

### Project Structure

```text
generator/
├── __init__.py                    # Package initialization
├── models.py                     # 🆕 Pydantic models for structured output
├── bedrock_agent.py              # 🔄 AWS Bedrock integration with multimodal support
├── data_loaders.py               # Data loading utilities
├── document_generator.py         # 🔄 PDF document generation with structured input
├── profile_generator.py          # 🔄 Patient profile generation with multimodal
├── medical_records_generator.py  # 🔄 Main application (simplified)
├── test_structured_output.py     # 🆕 Test script for new capabilities
├── example_usage.py              # 🆕 Usage examples and demonstrations
├── config.json                   # Configuration file
├── config.json.schema            # JSON Schema with documentation and examples
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── README_STRUCTURED_OUTPUT.md   # 🆕 Detailed technical documentation
└── IMPLEMENTATION_SUMMARY.md     # 🆕 Implementation summary
```

### Adding New Document Types

1. Add the document type to `config.json` in `generation.document_types`
2. Implement document-specific content creation in `document_generator.py`
3. Add appropriate prompts in `bedrock_agent.py`

### Extending Data Sources

1. Create new loader class in `data_loaders.py`
2. Integrate with `profile_generator.py`
3. Update configuration schema

## License

This project is part of the AWSome Builder healthcare application and follows the same licensing terms.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review application logs in `generator.log`
3. Ensure all data sources are properly configured
4. Verify AWS Bedrock access and permissions

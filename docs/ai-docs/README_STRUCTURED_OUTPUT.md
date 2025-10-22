# Synthetic Medical Data Generator

This document describes the synthetic medical data generator with structured output and multimodal capabilities.

## 🚀 Core Features

### 1. Structured Output with Pydantic Models

The generator now uses Pydantic models to ensure type-safe, validated responses from the AI agent. This eliminates JSON parsing errors and provides guaranteed data structure.

#### Key Models

- **`PatientProfile`**: Complete patient data structure with personal info, medical history, and lab results
- **`PersonalInfo`**: Personal details in Latin American format (two surnames, DD/MM/YYYY dates)
- **`MedicalHistory`**: Medical conditions, medications, and procedures
- **`DocumentNarratives`**: All document types in one structured response
- **`ScannedDocumentAnalysis`**: Analysis results from scanned medical documents

#### Benefits

- ✅ **No JSON parsing errors** - guaranteed valid structure
- ✅ **Type safety** - validated data types and constraints
- ✅ **Better error handling** - clear validation messages
- ✅ **Consistent data format** - standardized across all outputs

### 2. Multimodal Input Capabilities

The generator can now analyze scanned medical documents and use them as reference for generating similar but unique synthetic patients.

#### How It Works

1. **Random Scan Selection**: Automatically selects a random scanned document from the `lbmaske` directory
2. **Document Analysis**: AI analyzes the scan to extract:
   - Document type (historia clínica, laboratorio, etc.)
   - Patient information (if visible)
   - Medical conditions mentioned
   - Medications listed
   - Laboratory values
   - Key medical findings
3. **Similar Patient Generation**: Creates a new synthetic patient with similar characteristics
4. **Reference Preservation**: Copies the original scan to the patient's output folder

#### Benefits

- 🎯 **Higher Realism**: Patients based on real document patterns
- 📋 **Better Context**: Generated content matches actual medical document styles
- 🔄 **Learning from Examples**: AI learns from real medical documents
- 📁 **Complete Packages**: Each patient includes original scan + generated documents

## 📁 Enhanced Output Structure

Each generated patient now includes:

```
patient_12345678-abcd-1234-5678-123456789abc/
├── patient_12345678-abcd-1234-5678-123456789abc_profile.json    # Patient profile
├── reference_scan.jpg                                            # Original reference scan
├── patient_12345678-abcd-1234-5678-123456789abc_historia_clinica_20241021_143022.pdf
├── patient_12345678-abcd-1234-5678-123456789abc_resultados_laboratorio_20241021_143025.pdf
└── patient_12345678-abcd-1234-5678-123456789abc_receta_medica_20241021_143028.pdf
```

## 🔧 Usage

### Quick Start

```bash
# Generate 5 patients with structured output and multimodal input
python medical_records_generator.py --count 5

# Run example to see all capabilities
python example_usage.py

# Test structured output functionality
python test_structured_output.py
```

### Programmatic Usage

```python
from profile_generator import PatientProfileGenerator
from models import PatientProfile

# Initialize generator with template directory
profile_generator = PatientProfileGenerator(
    fhir_loader=fhir_loader,
    csv_loader=csv_loader,
    agent=agent,
    template_dir="lbmaske"  # Directory with scanned documents
)

# Generate patient (automatically uses reference scans)
profile = profile_generator.generate_profile()

# Access structured data
print(f"Patient: {profile['personal_info']['nombre_completo']}")
print(f"Reference scan: {profile.get('source_scan', 'None')}")
```

## 🧪 Testing

Run the test script to verify functionality:

```bash
cd apps/SampleFileGeneration/generator
python test_structured_output.py
```

This will test:
- Structured output generation
- Multimodal document analysis
- End-to-end patient generation with reference scans

## 📊 Configuration

Update your `config.json` to include the template directory:

```json
{
  "data_sources": {
    "fhir_dir": "data/fhir",
    "csv_path": "data/demographics.csv",
    "template_dir": "lbmaske"  // Directory with scanned medical documents
  },
  "bedrock": {
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "region": "us-east-1",
    "use_inference_profile": false,
    "max_tokens": 4096,
    "temperature": 0.7
  }
}
```

## 🔍 Data Validation

All generated data is validated using Pydantic models:

- **Age**: Must be between 0-120 years
- **Gender**: Must be 'M' or 'F'
- **Dates**: Must be in DD/MM/YYYY format
- **Document IDs**: Must be valid UUIDs
- **Lab values**: Must include units and reference ranges

## 🚨 Error Handling

The system includes robust error handling:

- **Scan Analysis Failures**: Falls back to demographic-only generation
- **Validation Errors**: Clear error messages with field-specific details
- **Model Failures**: Graceful degradation with logging
- **File Operations**: Proper cleanup and recovery mechanisms

## 🎯 Quality Improvements

The new system provides:

1. **Better Medical Coherence**: AI learns from real medical documents
2. **Consistent Formatting**: Standardized data structures
3. **Improved Realism**: Generated content matches real document patterns
4. **Enhanced Traceability**: Each patient linked to source reference scan
5. **Reduced Errors**: Structured output eliminates parsing failures

## 🎯 Default Behavior

The system always uses:

- **Structured Output**: All AI responses are validated Pydantic models
- **Multimodal Input**: Reference scans are automatically used when available
- **Complete Packages**: Each patient includes original scan + generated documents
- **Type Safety**: All data structures are validated and type-safe

## 📈 Performance Considerations

- **Batch Processing**: Document narratives generated in single API call
- **Caching**: FHIR data cached for performance
- **Parallel Processing**: Multiple document types generated concurrently
- **Memory Efficient**: Streaming PDF generation for large documents

## 🛠️ Troubleshooting

### Common Issues

1. **No scanned documents found**
   - Ensure `template_dir` exists and contains image files
   - Check file permissions
   - Verify supported formats: .jpg, .jpeg, .png, .pdf

2. **Validation errors**
   - Check Pydantic model constraints
   - Verify data types match expected formats
   - Review error messages for specific field issues

3. **Multimodal analysis fails**
   - Verify image file is readable
   - Check file size (should be < 20MB)
   - Ensure image quality is sufficient for OCR

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- Scan selection process
- Document analysis results
- Structured output validation
- API call details

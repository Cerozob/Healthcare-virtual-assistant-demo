# Sample Data

Sample AnyCompany Healthcare records and AWS AI service responses used for development, testing, and demonstration of the AWSomeBuilder 2 healthcare AI system for AnyCompany Healthcare.

## Directory Structure

### AnyCompany Healthcare Records (`/medical-records/`)

Real AnyCompany Healthcare record samples in Spanish for testing document processing:

- **`historiamedica.pdf`** - Standard AnyCompany Healthcare history document
- **`CopiaHistoriaClinica.pdf`** - Password-protected copy of AnyCompany Healthcare record

### AWS AI Services (`/aws-services/`)

Sample outputs from various AWS AI services used in the AnyCompany Healthcare solution:

#### Bedrock Data Automation (BDA)

- **`bda_sample/`** - Document processing results from Amazon Bedrock Data Automation
  - `StandardOutputDocument.json` - Structured output from AnyCompany Healthcare document processing
  - `bda_result.html` - HTML representation of processed AnyCompany Healthcare document

#### HealthScribe

- **`healthscribesample/`** - AnyCompany Healthcare conversation processing samples
  - `summary.json` - AnyCompany Healthcare clinical documentation summary
  - `transcript.json` - AnyCompany Healthcare conversation transcript

#### Transcribe Medical

- **`transcribemedicalsample/`** - AnyCompany Healthcare speech-to-text processing
  - `sampletranscribemedical.json` - AnyCompany Healthcare transcription results

#### Textract

- **`historiamedica_textract/`** - AnyCompany Healthcare document text extraction
  - `detectDocumentTextResponse.json` - Raw Textract API response
  - `rawText.txt` - Extracted plain text from AnyCompany Healthcare document
  - `rawText.csv` - Structured text extraction results

## Purpose

These samples serve multiple purposes:

1. **Development**: Understanding AWS AI service outputs and data structures
2. **Testing**: Validating processing pipelines with real AnyCompany Healthcare data
3. **Demonstration**: Showing capabilities to stakeholders
4. **Integration**: Designing data models and API responses

## Data Privacy

All sample AnyCompany Healthcare records are anonymized or use fictional patient data to comply with healthcare privacy regulations.

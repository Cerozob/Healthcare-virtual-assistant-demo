# Datos de Muestra

Registros médicos de muestra y respuestas de servicios de IA de AWS utilizados para desarrollo, pruebas y demostración del sistema de IA médica para el cuidado de la salud.

## Estructura de Directorios

### Registros Médicos (`/medical-records/`)

Muestras reales de registros médicos en español para pruebas de procesamiento de documentos:

- **`historiamedica.pdf`** - Documento estándar de historia clínica
- **`CopiaHistoriaClinica.pdf`** - Copia protegida con contraseña de registro médico

### Plantillas y Protocolos en Español

Nuevos archivos de datos de muestra en español:

- **`protocolos-medicos-espanol.json`** - Protocolos médicos completos en español con especialidades, síntomas, exámenes y tratamientos
- **`plantillas-laboratorio-espanol.json`** - Plantillas de resultados de laboratorio con terminología médica en español
- **`proveedores-departamentos-espanol.json`** - Información de proveedores médicos y departamentos hospitalarios en español

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

## Propósito

Estas muestras sirven múltiples propósitos:

1. **Desarrollo**: Comprensión de salidas de servicios de IA de AWS y estructuras de datos
2. **Pruebas**: Validación de pipelines de procesamiento con datos médicos reales
3. **Demostración**: Mostrar capacidades a las partes interesadas
4. **Integración**: Diseño de modelos de datos y respuestas de API

## Privacidad de Datos

Todos los registros médicos de muestra están anonimizados o utilizan datos ficticios de pacientes para cumplir con las regulaciones de privacidad en el cuidado de la salud.

## Uso de las Plantillas en Español

Las nuevas plantillas en español proporcionan:

- **Terminología médica apropiada**: Términos médicos profesionales utilizados en América Latina
- **Nombres latinoamericanos**: Nombres comunes de pacientes y proveedores médicos
- **Protocolos médicos completos**: Guías de tratamiento con síntomas, exámenes y tratamientos en español
- **Estructura de departamentos**: Organización hospitalaria típica con nombres en español

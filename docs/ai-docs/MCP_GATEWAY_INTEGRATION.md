# MCP Gateway Integration Improvement

## Overview

Removed redundant custom patient lookup tool and enhanced the information retrieval agent to use MCP Gateway tools directly for all patient identification and database operations.

## What Was Changed

### ❌ Removed: Custom Patient Lookup Tool
- **File**: `agents/tools/patient_lookup.py` (deleted)
- **Problem**: Redundant AI-only identification without actual database lookup
- **Issue**: Duplicated functionality that MCP Gateway already provides

### ✅ Enhanced: Information Retrieval Agent
- **Enhanced system prompt** with explicit patient identification strategies
- **Direct use of MCP Gateway tools** for all database operations
- **Intelligent multi-method patient search** using existing APIs

## MCP Gateway Tools Available

Based on `infrastructure/schemas/lambda_tool_schemas.py`, the following tools are available:

### 1. `patients_api` - Complete Patient Management
```python
# Actions available:
- "list": Search/list patients with pagination
- "get": Get specific patient by patient_id  
- "create": Create new patient record
- "update": Update existing patient
- "delete": Remove patient record

# Patient data includes:
- patient_id (UUID)
- full_name
- email  
- date_of_birth
- phone
- created_at, updated_at
```

### 2. `medics_api` - Medical Staff Management
```python
# Actions: list, get, create, update, delete
# Data: medic_id, full_name, specialty, license_number, email, phone
```

### 3. `exams_api` - Medical Exam Types
```python
# Actions: list, get, create, update, delete  
# Data: exam_id, exam_name, exam_type, description, duration_minutes
```

### 4. `reservations_api` - Appointment Management
```python
# Actions: list, get, create, update, delete, check_availability
# Data: reservation_id, patient_id, medic_id, exam_id, reservation_date, status
```

### 5. `files_api` - Medical Document Management
```python
# Actions: list, upload, delete, classify
# Data: file_id, filename, patient_id, file_type, s3_key, classification
```

## Patient Identification Strategies

The information retrieval agent now uses multiple strategies via MCP Gateway:

### 1. Name-Based Search
```python
# Use patients_api with list action
{
    "action": "list",
    "pagination": {"limit": 50, "offset": 0}
}
# Then search through full_name field in results
```

### 2. ID-Based Lookup  
```python
# Use patients_api with get action for UUIDs
{
    "action": "get", 
    "patient_id": "1d621da0-f89e-4691-8f56-5022bb20dcca"
}
```

### 3. Cross-Reference Search
```python
# Use reservations_api to find recent patients
{
    "action": "list",
    "date_from": "2024-11-01",
    "pagination": {"limit": 20}
}
# Then use patient_id to get full patient details
```

### 4. Multi-API Correlation
```python
# Combine multiple APIs for comprehensive patient context:
# 1. Find patient via patients_api
# 2. Get their appointments via reservations_api  
# 3. Get their files via files_api
# 4. Get their assigned doctors via medics_api
```

## Benefits of This Approach

### 1. **No Code Duplication**
- ❌ **Before**: Custom AI tool + MCP Gateway tools (redundant)
- ✅ **After**: Only MCP Gateway tools (single source of truth)

### 2. **Real Database Integration**
- ❌ **Before**: AI identification without database verification
- ✅ **After**: Direct database lookup and verification via MCP

### 3. **Comprehensive Patient Data**
- ❌ **Before**: Limited to extracted text information
- ✅ **After**: Full patient records, appointments, files, medical history

### 4. **Consistent API Usage**
- ❌ **Before**: Mixed custom tools + MCP tools
- ✅ **After**: Uniform MCP Gateway API usage throughout

### 5. **Better Error Handling**
- ❌ **Before**: AI extraction could fail silently
- ✅ **After**: Database errors are explicit and actionable

## Enhanced System Prompt

The information retrieval agent now has explicit instructions for:

- **Natural Language Analysis**: Extract patient identifiers from conversation
- **Multi-Method Search**: Try name, ID, cédula, contextual references
- **API Strategy**: Use appropriate MCP Gateway actions for each search type
- **Result Correlation**: Combine data from multiple APIs for complete context
- **Fallback Handling**: Try alternative search methods if first attempt fails

## Example Patient Identification Flow

### User Query: "Find medical history for Juan Pérez"

**Agent Process:**
1. **Analyze Query**: Extract "Juan Pérez" as patient name
2. **Search Strategy**: Use `patients_api` list action
3. **API Call**: 
   ```python
   {
       "action": "list",
       "pagination": {"limit": 50, "offset": 0}
   }
   ```
4. **Filter Results**: Search for "Juan Pérez" in `full_name` field
5. **Get Patient ID**: Extract `patient_id` from matching result
6. **Get Medical Files**: Use `files_api` with `patient_id` filter
7. **Get Appointments**: Use `reservations_api` with `patient_id` filter
8. **Return Comprehensive Data**: Patient info + files + appointment history

### User Query: "Patient ID 1d621da0-f89e-4691-8f56-5022bb20dcca"

**Agent Process:**
1. **Analyze Query**: Detect UUID format
2. **Direct Lookup**: Use `patients_api` get action
3. **API Call**:
   ```python
   {
       "action": "get",
       "patient_id": "1d621da0-f89e-4691-8f56-5022bb20dcca"
   }
   ```
4. **Get Related Data**: Use patient_id for files, appointments, etc.
5. **Return Complete Profile**: All patient-related information

## File Organization Integration

The multimodal uploader now works seamlessly with MCP Gateway patient data:

1. **Patient Identification**: Info retrieval agent identifies patient via MCP
2. **File Organization**: Uses `patient_id` from database for S3 organization
3. **Database Recording**: Files recorded via `files_api` for tracking
4. **Cross-Reference**: Files linked to patient records in database

This creates a complete, integrated system where patient identification, file storage, and database management all work together through the MCP Gateway.

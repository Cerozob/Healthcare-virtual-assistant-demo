# Frontend Debug Features

This document explains the debug features added to troubleshoot patient identification issues in the chat interface.

## Problem

The chat was showing "Agent identified patient: undefined (undefined)" even though the agent was working correctly and identifying patients properly. This suggests a data flow issue between the backend and frontend.

## Debug Features Added

### 1. Console Debug Logging

Comprehensive console logging has been added throughout the chat flow:

#### Chat Service Logging
- **📤 CHAT SERVICE REQUEST** - Logs outgoing requests to the agent
- **📥 CHAT SERVICE RESPONSE** - Logs incoming responses from the agent
- **🔄 FORMATTED RESPONSE** - Logs the final formatted response

#### API Client Logging
- **📤 API REQUEST** - Logs HTTP requests with headers and body
- **📥 API RESPONSE** - Logs HTTP responses with status and data
- **📊 Parsed data** - Shows the parsed JSON response

#### Chat Page Logging
- **🔍 CHAT RESPONSE DEBUG** - Complete response analysis
- **🎯 PATIENT IDENTIFICATION DEBUG** - Patient data structure analysis
- **❌ PATIENT IDENTIFICATION FAILED** - Detailed failure analysis

### 2. Debug Panel UI Component

A collapsible debug panel has been added to the chat interface:

- **Location**: Bottom of the chat page
- **Toggle**: Click "Show Debug Panel" to expand
- **Sections**:
  - Last Chat Response (JSON)
  - Last Chat Request (JSON)
  - Patient Context from Response (JSON)
  - Selected Patient State (JSON)
  - Debug Instructions

### 3. Debug Information Tracking

The chat page now tracks debug information in state:
```typescript
const [debugInfo, setDebugInfo] = useState({
  lastResponse: null,
  lastRequest: null,
  patientContext: null
});
```

## How to Debug Patient Identification Issues

### Step 1: Open Browser DevTools
1. Press F12 or right-click → Inspect
2. Go to the Console tab
3. Send a message that should identify a patient

### Step 2: Check Console Logs
Look for these log groups in order:

1. **📤 CHAT SERVICE REQUEST**
   - Verify the message is being sent correctly
   - Check if patient context is included in the request

2. **📤 API REQUEST**
   - Verify the HTTP request is being made
   - Check the request URL and headers

3. **📥 API RESPONSE**
   - Check the HTTP response status (should be 200)
   - Verify the response contains data

4. **📥 CHAT SERVICE RESPONSE**
   - Check if `patient_context` exists in the response
   - Verify `patient_found` is true
   - Check if `patient_data` exists and has the right structure

5. **🔍 CHAT RESPONSE DEBUG**
   - Detailed analysis of the complete response
   - Patient context breakdown

6. **🎯 PATIENT IDENTIFICATION DEBUG** or **❌ PATIENT IDENTIFICATION FAILED**
   - Shows whether patient identification succeeded or failed
   - Detailed analysis of patient data structure

### Step 3: Use Debug Panel
1. Scroll to the bottom of the chat page
2. Click "Show Debug Panel"
3. Expand the sections to see:
   - **Last Chat Response**: The complete response from the agent
   - **Patient Context**: The patient_context object from the response
   - **Selected Patient State**: The current patient in the UI state

### Step 4: Analyze the Data

#### Common Issues and Solutions

**Issue: "undefined (undefined)" in system message**
- **Cause**: `patient_data.full_name` or `patient_data.patient_id` is undefined
- **Debug**: Check the "Patient Context from Response" section
- **Solution**: Verify the agent is returning the correct field names

**Issue: No patient context in response**
- **Cause**: Agent didn't identify a patient or patient_context is missing
- **Debug**: Check if `patient_found` is false in the response
- **Solution**: Check agent logs to see why patient wasn't identified

**Issue: Patient context exists but patient_data is empty**
- **Cause**: Agent found a patient but didn't populate patient_data
- **Debug**: Check if `patient_data` object exists and has content
- **Solution**: Check agent code for patient data population

**Issue: Wrong patient selected**
- **Cause**: Patient ID matching logic issue
- **Debug**: Compare `patient_data.patient_id` with expected patient ID
- **Solution**: Check patient lookup logic in the agent

## Expected Log Flow

When everything works correctly, you should see:

```
📤 CHAT SERVICE REQUEST
   • message length: 25
   • sessionId: healthcare_session_20251028_103015

📤 API REQUEST [POST] http://localhost:3001/v1/agent-integration/chat
   • Status: 200 OK

📥 API RESPONSE [200]
   • patient_context: { patient_found: true, patient_data: {...} }

🔍 CHAT RESPONSE DEBUG
   • Patient context exists: true
   • patient_found: true
   • patient_data exists: true
   • patient_id: "12345678"
   • full_name: "Juan Pérez"

🎯 PATIENT IDENTIFICATION DEBUG
   • Patient found in response
   • patient_id: "12345678" string
   • full_name: "Juan Pérez" string
```

## Troubleshooting Tips

1. **Clear browser cache** if you see stale data
2. **Check network tab** in DevTools for failed requests
3. **Verify agent is running** and accessible
4. **Check agent logs** for backend issues
5. **Test with different patients** to isolate the issue
6. **Use the debug panel** to see the exact data structure

## Removing Debug Features

For production deployment, you can:

1. **Keep console logs** but reduce log level
2. **Remove debug panel** by commenting out the `<DebugPanel>` component
3. **Set environment variable** to disable debug logging:
   ```bash
   export REACT_APP_DEBUG_LOGGING=false
   ```

## Debug Environment Variables

Add these to your `.env` file for debug control:

```bash
# Enable/disable debug logging
REACT_APP_DEBUG_LOGGING=true

# Enable/disable debug panel
REACT_APP_DEBUG_PANEL=true

# Log level (error, warn, info, debug)
REACT_APP_LOG_LEVEL=debug
```

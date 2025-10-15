# Scheduling System API Reference

## Overview
This document provides a comprehensive reference for the automated scheduling system APIs, including protocol management, scheduling actions, and reservation management.

## Base URLs
- Protocol Management: `/api/v1/protocols`
- Scheduling Actions: `/api/v1/scheduling` (Bedrock Agent action groups)
- Reservation Management: `/api/v1/reservations`

---

## Protocol Management API

### List Protocols
**Endpoint:** `GET /protocols`

**Query Parameters:**
- `is_active` (boolean, default: true) - Filter by active status
- `limit` (integer, default: 50) - Number of results
- `offset` (integer, default: 0) - Pagination offset

**Response:**
```json
{
  "protocols": [
    {
      "protocol_id": "uuid",
      "name": "Chest Pain Protocol",
      "description": "Protocol for patients presenting with chest pain symptoms",
      "symptoms": ["chest pain", "chest discomfort", "pressure in chest"],
      "recommended_exams": ["ECG", "Chest X-Ray", "Blood Test - Complete Panel"],
      "recommended_treatments": ["Cardiology consultation", "Stress test if needed"],
      "priority_level": 3,
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### Get Protocol
**Endpoint:** `GET /protocols/{protocol_id}`

**Response:**
```json
{
  "protocol": {
    "protocol_id": "uuid",
    "name": "Chest Pain Protocol",
    "description": "Protocol for patients presenting with chest pain symptoms",
    "symptoms": ["chest pain", "chest discomfort"],
    "recommended_exams": ["ECG", "Chest X-Ray"],
    "recommended_treatments": ["Cardiology consultation"],
    "priority_level": 3,
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### Create Protocol
**Endpoint:** `POST /protocols`

**Request Body:**
```json
{
  "name": "New Protocol",
  "description": "Protocol description",
  "symptoms": ["symptom1", "symptom2"],
  "recommended_exams": ["Exam 1", "Exam 2"],
  "recommended_treatments": ["Treatment 1"],
  "priority_level": 2,
  "is_active": true
}
```

**Response:**
```json
{
  "message": "Protocol created successfully",
  "protocol": {
    "protocol_id": "uuid",
    "name": "New Protocol",
    "description": "Protocol description",
    "priority_level": 2,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### Update Protocol
**Endpoint:** `PUT /protocols/{protocol_id}`

**Request Body:** (all fields optional)
```json
{
  "name": "Updated Protocol Name",
  "description": "Updated description",
  "symptoms": ["updated symptom list"],
  "recommended_exams": ["updated exam list"],
  "recommended_treatments": ["updated treatment list"],
  "priority_level": 3,
  "is_active": true
}
```

**Response:**
```json
{
  "message": "Protocol updated successfully",
  "protocol": {
    "protocol_id": "uuid",
    "name": "Updated Protocol Name",
    "description": "Updated description",
    "priority_level": 3,
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### Match Protocols
**Endpoint:** `POST /protocols/match`

**Request Body:**
```json
{
  "symptoms": ["chest pain", "shortness of breath", "fatigue"]
}
```

**Response:**
```json
{
  "matched_protocols": [
    {
      "protocol_id": "uuid",
      "name": "Chest Pain Protocol",
      "description": "Protocol for patients presenting with chest pain symptoms",
      "recommended_exams": ["ECG", "Chest X-Ray"],
      "recommended_treatments": ["Cardiology consultation"],
      "priority_level": 3,
      "match_score": 0.67,
      "matched_symptoms": [
        {
          "patient_symptom": "chest pain",
          "protocol_symptom": "chest pain"
        }
      ],
      "total_matches": 1
    }
  ],
  "count": 1,
  "input_symptoms": ["chest pain", "shortness of breath", "fatigue"]
}
```

### Recommend Exams
**Endpoint:** `POST /protocols/recommend`

**Request Body:**
```json
{
  "symptoms": ["chest pain", "shortness of breath"],
  "patient_id": "uuid" // optional
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "exam_name": "ECG",
      "protocols": [
        {
          "protocol_name": "Chest Pain Protocol",
          "protocol_id": "uuid",
          "match_score": 0.67
        }
      ],
      "priority_score": 3,
      "match_score": 0.67,
      "exam_details": {
        "exam_id": "uuid",
        "name": "ECG",
        "description": "Electrocardiogram to measure heart electrical activity",
        "category": "Cardiology",
        "duration_minutes": 20,
        "preparation_instructions": "Avoid caffeine 2 hours before test"
      }
    }
  ],
  "count": 1,
  "matched_protocols": [...],
  "input_symptoms": ["chest pain", "shortness of breath"],
  "patient_id": "uuid"
}
```

---

## Scheduling Actions API (Bedrock Agent)

### Schedule Exam
**Endpoint:** `POST /schedule-exam`

**Request Body:**
```json
{
  "content": {
    "patient_id": "uuid",
    "exam_id": "uuid",
    "medic_id": "uuid",
    "start_time": "2024-01-20T10:00:00Z",
    "protocol_id": "uuid", // optional
    "notes": "Patient reports chest pain",
    "auto_scheduled": false
  }
}
```

**Response:**
```json
{
  "statusCode": 201,
  "body": {
    "message": "Exam scheduled successfully",
    "reservation": {
      "reservation_id": "uuid",
      "patient_id": "uuid",
      "medic_id": "uuid",
      "exam_id": "uuid",
      "start_time": "2024-01-20T10:00:00Z",
      "end_time": "2024-01-20T10:20:00Z",
      "status": "scheduled"
    }
  }
}
```

### Check Availability
**Endpoint:** `POST /check-availability`

**Request Body:**
```json
{
  "content": {
    "exam_id": "uuid",
    "medic_id": "uuid", // optional - if not provided, checks all qualified medics
    "start_time": "2024-01-20T10:00:00Z",
    "end_time": "2024-01-20T10:30:00Z" // optional - calculated from exam duration
  }
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "available": true,
    "qualified": true,
    "available_medics": [
      {
        "medic_id": "uuid",
        "first_name": "Dr. Sarah",
        "last_name": "Wilson",
        "specialty": "Cardiology"
      }
    ],
    "total_qualified": 2,
    "total_available": 1
  }
}
```

### Get Protocols (Agent)
**Endpoint:** `POST /get-protocols`

**Request Body:**
```json
{
  "content": {
    "symptoms": ["chest pain", "fatigue"] // optional
  }
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "protocols": [
      {
        "protocol_id": "uuid",
        "name": "Chest Pain Protocol",
        "description": "Protocol for patients presenting with chest pain symptoms",
        "symptoms": ["chest pain", "chest discomfort"],
        "recommended_exams": ["ECG", "Chest X-Ray"],
        "recommended_treatments": ["Cardiology consultation"],
        "priority_level": 3,
        "matched_symptoms": ["chest pain"], // only if symptoms provided
        "match_count": 1 // only if symptoms provided
      }
    ],
    "count": 1
  }
}
```

### Reschedule Appointment
**Endpoint:** `POST /reschedule-appointment`

**Request Body:**
```json
{
  "content": {
    "reservation_id": "uuid",
    "new_start_time": "2024-01-21T14:00:00Z",
    "reason": "Patient requested different time"
  }
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "Appointment rescheduled successfully",
    "reservation": {
      "reservation_id": "uuid",
      "patient_id": "uuid",
      "medic_id": "uuid",
      "exam_id": "uuid",
      "start_time": "2024-01-21T14:00:00Z",
      "end_time": "2024-01-21T14:20:00Z",
      "status": "scheduled"
    }
  }
}
```

### Auto-Schedule
**Endpoint:** `POST /auto-schedule`

**Request Body:**
```json
{
  "content": {
    "patient_id": "uuid",
    "symptoms": ["chest pain", "shortness of breath"],
    "preferred_date": "2024-01-20T09:00:00Z" // optional
  }
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "Successfully scheduled 2 exams",
    "protocol_used": {
      "protocol_id": "uuid",
      "protocol_name": "Chest Pain Protocol"
    },
    "scheduled_exams": [
      {
        "exam_name": "ECG",
        "reservation": {
          "reservation_id": "uuid",
          "patient_id": "uuid",
          "medic_id": "uuid",
          "exam_id": "uuid",
          "start_time": "2024-01-20T09:00:00Z",
          "end_time": "2024-01-20T09:20:00Z",
          "status": "scheduled"
        },
        "medic": {
          "medic_id": "uuid",
          "first_name": "Dr. Sarah",
          "last_name": "Wilson",
          "specialty": "Cardiology"
        }
      }
    ],
    "symptoms": ["chest pain", "shortness of breath"]
  }
}
```

### Find Alternatives
**Endpoint:** `POST /find-alternatives`

**Request Body:**
```json
{
  "content": {
    "exam_id": "uuid",
    "medic_id": "uuid", // optional
    "preferred_date": "2024-01-20T10:00:00Z",
    "days_range": 7 // optional, default: 7
  }
}
```

**Response:**
```json
{
  "statusCode": 200,
  "body": {
    "alternatives": [
      {
        "medic_id": "uuid",
        "start_time": "2024-01-20T14:00:00Z",
        "end_time": "2024-01-20T14:20:00Z",
        "day_of_week": "Saturday",
        "date": "2024-01-20"
      }
    ],
    "count": 10,
    "exam_id": "uuid",
    "duration_minutes": 20
  }
}
```

---

## Reservation Management API

### List Reservations
**Endpoint:** `GET /reservations`

**Query Parameters:**
- `patient_id` (uuid) - Filter by patient
- `medic_id` (uuid) - Filter by medic
- `status` (string) - Filter by status (scheduled, confirmed, completed, cancelled, no_show)
- `auto_scheduled` (boolean) - Filter by auto-scheduled flag
- `from_date` (ISO datetime) - Filter by start date
- `to_date` (ISO datetime) - Filter by end date
- `limit` (integer, default: 50) - Number of results
- `offset` (integer, default: 0) - Pagination offset

**Response:**
```json
{
  "reservations": [
    {
      "reservation_id": "uuid",
      "patient_id": "uuid",
      "patient_name": "John Doe",
      "medic_id": "uuid",
      "medic_name": "Dr. Sarah Wilson",
      "specialty": "Cardiology",
      "exam_id": "uuid",
      "exam_name": "ECG",
      "duration_minutes": 20,
      "start_time": "2024-01-20T10:00:00Z",
      "end_time": "2024-01-20T10:20:00Z",
      "status": "scheduled",
      "notes": "Patient reports chest pain",
      "auto_scheduled": false,
      "protocol_id": "uuid",
      "protocol_name": "Chest Pain Protocol",
      "scheduling_agent_metadata": {
        "scheduled_by": "scheduling_agent",
        "scheduled_at": "2024-01-15T10:00:00Z",
        "protocol_based": true
      },
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### Get Reservation
**Endpoint:** `GET /reservations/{reservation_id}`

**Response:**
```json
{
  "reservation": {
    "reservation_id": "uuid",
    "patient_id": "uuid",
    "patient_name": "John Doe",
    "patient_email": "john.doe@email.com",
    "patient_phone": "+1-555-0101",
    "medic_id": "uuid",
    "medic_name": "Dr. Sarah Wilson",
    "specialty": "Cardiology",
    "medic_email": "sarah.wilson@hospital.com",
    "exam_id": "uuid",
    "exam_name": "ECG",
    "exam_description": "Electrocardiogram to measure heart electrical activity",
    "duration_minutes": 20,
    "preparation_instructions": "Avoid caffeine 2 hours before test",
    "start_time": "2024-01-20T10:00:00Z",
    "end_time": "2024-01-20T10:20:00Z",
    "status": "scheduled",
    "notes": "Patient reports chest pain",
    "auto_scheduled": false,
    "protocol_id": "uuid",
    "protocol_name": "Chest Pain Protocol",
    "protocol_description": "Protocol for patients presenting with chest pain symptoms",
    "scheduling_agent_metadata": {...},
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### Create Reservation
**Endpoint:** `POST /reservations`

**Request Body:**
```json
{
  "patient_id": "uuid",
  "exam_id": "uuid",
  "medic_id": "uuid",
  "start_time": "2024-01-20T10:00:00Z",
  "status": "scheduled", // optional, default: scheduled
  "notes": "Patient reports chest pain",
  "auto_scheduled": false,
  "protocol_id": "uuid", // optional
  "scheduling_agent_metadata": {} // optional
}
```

**Response:**
```json
{
  "message": "Reservation created successfully",
  "reservation": {
    "reservation_id": "uuid",
    "patient_id": "uuid",
    "medic_id": "uuid",
    "exam_id": "uuid",
    "start_time": "2024-01-20T10:00:00Z",
    "end_time": "2024-01-20T10:20:00Z",
    "status": "scheduled"
  }
}
```

### Update Reservation
**Endpoint:** `PUT /reservations/{reservation_id}`

**Request Body:** (all fields optional)
```json
{
  "status": "confirmed",
  "notes": "Updated notes",
  "start_time": "2024-01-20T11:00:00Z",
  "end_time": "2024-01-20T11:20:00Z",
  "scheduling_agent_metadata": {}
}
```

**Response:**
```json
{
  "message": "Reservation updated successfully",
  "reservation": {
    "reservation_id": "uuid",
    "patient_id": "uuid",
    "medic_id": "uuid",
    "exam_id": "uuid",
    "start_time": "2024-01-20T11:00:00Z",
    "end_time": "2024-01-20T11:20:00Z",
    "status": "confirmed"
  }
}
```

### Cancel Reservation
**Endpoint:** `DELETE /reservations/{reservation_id}`

**Response:**
```json
{
  "message": "Reservation cancelled successfully",
  "reservation_id": "uuid"
}
```

### Get Conflicts
**Endpoint:** `GET /reservations/conflicts`

**Response:**
```json
{
  "conflicts": [
    {
      "reservation_1": "uuid",
      "reservation_2": "uuid",
      "medic_id": "uuid",
      "start_1": "2024-01-20T10:00:00Z",
      "end_1": "2024-01-20T10:30:00Z",
      "start_2": "2024-01-20T10:15:00Z",
      "end_2": "2024-01-20T10:45:00Z",
      "medic_name": "Dr. Sarah Wilson"
    }
  ],
  "count": 1
}
```

### Auto-Schedule from Protocol
**Endpoint:** `POST /reservations/auto-schedule`

**Request Body:**
```json
{
  "patient_id": "uuid",
  "protocol_id": "uuid",
  "preferred_date": "2024-01-20T09:00:00Z" // optional
}
```

**Response:**
```json
{
  "message": "Scheduled 2 out of 3 exams",
  "successful": [
    {
      "reservation_id": "uuid",
      "exam_id": "uuid",
      "exam_name": "ECG",
      "medic_id": "uuid",
      "medic_name": "Dr. Sarah Wilson",
      "start_time": "2024-01-20T09:00:00Z",
      "end_time": "2024-01-20T09:20:00Z",
      "success": true,
      "message": "Successfully scheduled"
    }
  ],
  "failed": [
    {
      "reservation_id": null,
      "exam_id": "uuid",
      "exam_name": "MRI - Knee",
      "medic_id": null,
      "medic_name": null,
      "start_time": null,
      "end_time": null,
      "success": false,
      "message": "No available qualified medic found"
    }
  ],
  "total": 3
}
```

### Get Available Slots
**Endpoint:** `POST /reservations/available-slots`

**Request Body:**
```json
{
  "medic_id": "uuid",
  "date": "2024-01-20",
  "duration_minutes": 30 // optional, default: 30
}
```

**Response:**
```json
{
  "available_slots": [
    {
      "slot_start": "2024-01-20T09:00:00Z",
      "slot_end": "2024-01-20T09:30:00Z",
      "is_available": true
    },
    {
      "slot_start": "2024-01-20T10:00:00Z",
      "slot_end": "2024-01-20T10:30:00Z",
      "is_available": true
    }
  ],
  "total_slots": 10,
  "available_count": 8,
  "medic_id": "uuid",
  "date": "2024-01-20"
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "statusCode": 400|404|409|500,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "error": "Error message description"
  }
}
```

### Common Error Codes
- `400` - Bad Request (missing required fields, invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (scheduling conflict detected)
- `500` - Internal Server Error (database error, unexpected error)

---

## Database Functions

### get_available_slots
Returns available time slots for a medic on a given date.

**SQL:**
```sql
SELECT * FROM get_available_slots(
  'medic-uuid',
  '2024-01-20'::DATE,
  30 -- duration in minutes
);
```

### auto_schedule_from_protocol
Automatically schedules exams based on a medical protocol.

**SQL:**
```sql
SELECT * FROM auto_schedule_from_protocol(
  'patient-uuid',
  'protocol-uuid',
  '2024-01-20 09:00:00+00'::TIMESTAMP WITH TIME ZONE
);
```

---

## Integration Notes

### Bedrock Agent Action Groups
The Scheduling Agent should be configured with the following action groups pointing to `scheduling_actions.py`:

1. **SchedulingActions**
   - `schedule_exam`
   - `check_availability`
   - `get_protocols`
   - `reschedule_appointment`
   - `auto_schedule`
   - `find_alternatives`

### Environment Variables
All Lambda functions require:
```
DB_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
DB_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
DB_NAME=healthcare
```

### IAM Permissions
Lambda execution roles need:
- `rds-data:ExecuteStatement`
- `rds-data:BatchExecuteStatement`
- `secretsmanager:GetSecretValue`

---

## Testing Examples

### Test Protocol Matching
```bash
curl -X POST https://api.example.com/protocols/match \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["chest pain", "shortness of breath"]
  }'
```

### Test Auto-Scheduling
```bash
curl -X POST https://api.example.com/scheduling/auto-schedule \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "patient_id": "patient-uuid",
      "symptoms": ["chest pain", "fatigue"],
      "preferred_date": "2024-01-20T09:00:00Z"
    }
  }'
```

### Test Availability Check
```bash
curl -X POST https://api.example.com/scheduling/check-availability \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "exam_id": "exam-uuid",
      "start_time": "2024-01-20T10:00:00Z"
    }
  }'
```

---

## Version History
- v1.0 (2025-01-14) - Initial implementation

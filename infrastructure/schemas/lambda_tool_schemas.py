"""
Lambda Tool Schemas for AgentCore Gateway.
Defines the input and output schemas for each Lambda function tool.
"""

from aws_cdk import aws_bedrockagentcore as agentcore
from typing import List


def get_patients_tool_schema() -> agentcore.CfnGatewayTarget.ToolDefinitionProperty:
    """Create tool schema for patients lambda function."""
    return agentcore.CfnGatewayTarget.ToolDefinitionProperty(
        name="patients_api",
        description="Manage patient information including creating, reading, updating, and deleting patient records",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete"],
                    "description": "The action to perform on patient records"
                },
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID for get, update, or delete operations"
                },
                "patient_data": {
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string", "description": "Patient's full name"},
                        "date_of_birth": {"type": "string", "format": "date", "description": "Patient's date of birth (YYYY-MM-DD)"},
                        "email": {"type": "string", "format": "email", "description": "Patient's email address"},
                        "phone": {"type": "string", "description": "Patient's phone number"}
                    },
                    "description": "Patient data for create or update operations"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0}
                    },
                    "description": "Pagination parameters for list operations"
                }
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "statusCode": {"type": "integer", "description": "HTTP status code"},
                "body": {
                    "type": "object",
                    "properties": {
                        "patients": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "patient_id": {"type": "string"},
                                    "full_name": {"type": "string"},
                                    "email": {"type": "string"},
                                    "date_of_birth": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"}
                                }
                            }
                        },
                        "patient": {
                            "type": "object",
                            "properties": {
                                "patient_id": {"type": "string"},
                                "full_name": {"type": "string"},
                                "email": {"type": "string"},
                                "date_of_birth": {"type": "string"},
                                "phone": {"type": "string"},
                                "created_at": {"type": "string"},
                                "updated_at": {"type": "string"}
                            }
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer"},
                                "offset": {"type": "integer"},
                                "total": {"type": "integer"},
                                "count": {"type": "integer"}
                            }
                        },
                        "message": {"type": "string", "description": "Success or error message"}
                    }
                }
            }
        }
    )


def get_medics_tool_schema() -> agentcore.CfnGatewayTarget.ToolDefinitionProperty:
    """Create tool schema for medics lambda function."""
    return agentcore.CfnGatewayTarget.ToolDefinitionProperty(
        name="medics_api",
        description="Manage medical professionals including their specialties, schedules, and availability",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete"],
                    "description": "The action to perform on medic records"
                },
                "medic_id": {
                    "type": "string",
                    "description": "Medic ID for get, update, or delete operations"
                },
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty filter for list operations"
                },
                "medic_data": {
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string", "description": "Medic's full name"},
                        "specialty": {"type": "string", "description": "Medical specialty"},
                        "license_number": {"type": "string", "description": "Medical license number"},
                        "email": {"type": "string", "format": "email", "description": "Medic's email address"},
                        "phone": {"type": "string", "description": "Medic's phone number"}
                    },
                    "description": "Medic data for create or update operations"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0}
                    },
                    "description": "Pagination parameters for list operations"
                }
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "statusCode": {"type": "integer", "description": "HTTP status code"},
                "body": {
                    "type": "object",
                    "properties": {
                        "medics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "medic_id": {"type": "string"},
                                    "full_name": {"type": "string"},
                                    "specialty": {"type": "string"},
                                    "license_number": {"type": "string"},
                                    "email": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"}
                                }
                            }
                        },
                        "medic": {
                            "type": "object",
                            "properties": {
                                "medic_id": {"type": "string"},
                                "full_name": {"type": "string"},
                                "specialty": {"type": "string"},
                                "license_number": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "created_at": {"type": "string"},
                                "updated_at": {"type": "string"}
                            }
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer"},
                                "offset": {"type": "integer"},
                                "total": {"type": "integer"},
                                "count": {"type": "integer"}
                            }
                        },
                        "message": {"type": "string", "description": "Success or error message"}
                    }
                }
            }
        }
    )


def get_exams_tool_schema() -> agentcore.CfnGatewayTarget.ToolDefinitionProperty:
    """Create tool schema for exams lambda function."""
    return agentcore.CfnGatewayTarget.ToolDefinitionProperty(
        name="exams_api",
        description="Manage medical exams and procedures including types, requirements, and scheduling",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete"],
                    "description": "The action to perform on exam records"
                },
                "exam_id": {
                    "type": "string",
                    "description": "Exam ID for get, update, or delete operations"
                },
                "exam_type": {
                    "type": "string",
                    "description": "Exam type filter for list operations"
                },
                "exam_data": {
                    "type": "object",
                    "properties": {
                        "exam_name": {"type": "string", "description": "Name of the exam"},
                        "exam_type": {"type": "string", "description": "Type of exam (e.g., blood test, X-ray)"},
                        "description": {"type": "string", "description": "Detailed description of the exam"},
                        "duration_minutes": {"type": "integer", "description": "Expected duration in minutes"},
                        "preparation_instructions": {"type": "string", "description": "Patient preparation instructions"}
                    },
                    "description": "Exam data for create or update operations"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0}
                    },
                    "description": "Pagination parameters for list operations"
                }
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "statusCode": {"type": "integer", "description": "HTTP status code"},
                "body": {
                    "type": "object",
                    "properties": {
                        "exams": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "exam_id": {"type": "string"},
                                    "exam_name": {"type": "string"},
                                    "exam_type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "duration_minutes": {"type": "integer"},
                                    "preparation_instructions": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"}
                                }
                            }
                        },
                        "exam": {
                            "type": "object",
                            "properties": {
                                "exam_id": {"type": "string"},
                                "exam_name": {"type": "string"},
                                "exam_type": {"type": "string"},
                                "description": {"type": "string"},
                                "duration_minutes": {"type": "integer"},
                                "preparation_instructions": {"type": "string"},
                                "created_at": {"type": "string"},
                                "updated_at": {"type": "string"}
                            }
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer"},
                                "offset": {"type": "integer"},
                                "total": {"type": "integer"},
                                "count": {"type": "integer"}
                            }
                        },
                        "message": {"type": "string", "description": "Success or error message"}
                    }
                }
            }
        }
    )


def get_reservations_tool_schema() -> agentcore.CfnGatewayTarget.ToolDefinitionProperty:
    """Create tool schema for reservations lambda function."""
    return agentcore.CfnGatewayTarget.ToolDefinitionProperty(
        name="reservations_api",
        description="Manage medical appointments and reservations including scheduling, cancellation, and availability checks",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete", "check_availability"],
                    "description": "The action to perform on reservation records"
                },
                "reservation_id": {
                    "type": "string",
                    "description": "Reservation ID for get, update, or delete operations"
                },
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID filter for list operations or required for create"
                },
                "medic_id": {
                    "type": "string",
                    "description": "Medic ID filter for list operations or required for create/availability"
                },
                "exam_id": {
                    "type": "string",
                    "description": "Exam ID required for create operations"
                },
                "reservation_date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Reservation date and time (ISO format)"
                },
                "date_from": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date filter for list operations"
                },
                "date_to": {
                    "type": "string",
                    "format": "date",
                    "description": "End date filter for list operations"
                },
                "status": {
                    "type": "string",
                    "enum": ["scheduled", "completed", "cancelled", "no_show"],
                    "description": "Reservation status filter"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0}
                    },
                    "description": "Pagination parameters for list operations"
                }
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "statusCode": {"type": "integer", "description": "HTTP status code"},
                "body": {
                    "type": "object",
                    "properties": {
                        "reservations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "reservation_id": {"type": "string"},
                                    "patient_id": {"type": "string"},
                                    "medic_id": {"type": "string"},
                                    "exam_id": {"type": "string"},
                                    "reservation_date": {"type": "string"},
                                    "status": {"type": "string"},
                                    "notes": {"type": "string"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"}
                                }
                            }
                        },
                        "reservation": {
                            "type": "object",
                            "properties": {
                                "reservation_id": {"type": "string"},
                                "patient_id": {"type": "string"},
                                "medic_id": {"type": "string"},
                                "exam_id": {"type": "string"},
                                "reservation_date": {"type": "string"},
                                "status": {"type": "string"},
                                "notes": {"type": "string"},
                                "created_at": {"type": "string"},
                                "updated_at": {"type": "string"}
                            }
                        },
                        "available_slots": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "start_time": {"type": "string"},
                                    "end_time": {"type": "string"},
                                    "available": {"type": "boolean"}
                                }
                            }
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer"},
                                "offset": {"type": "integer"},
                                "total": {"type": "integer"},
                                "count": {"type": "integer"}
                            }
                        },
                        "message": {"type": "string", "description": "Success or error message"}
                    }
                }
            }
        }
    )


def get_files_tool_schema() -> agentcore.CfnGatewayTarget.ToolDefinitionProperty:
    """Create tool schema for files lambda function."""
    return agentcore.CfnGatewayTarget.ToolDefinitionProperty(
        name="files_api",
        description="Manage medical documents and files including upload, classification, and knowledge base integration",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "upload", "delete", "classify"],
                    "description": "The action to perform on file records"
                },
                "file_id": {
                    "type": "string",
                    "description": "File ID for get or delete operations"
                },
                "patient_id": {
                    "type": "string",
                    "description": "Patient ID filter for list operations"
                },
                "file_type": {
                    "type": "string",
                    "description": "File type filter (e.g., lab_result, x_ray, prescription)"
                },

                "file_name": {
                    "type": "string",
                    "description": "Original filename (required for upload)"
                },
                "category": {
                    "type": "string",
                    "description": "Document category (optional, defaults to 'other')"
                },
                "size": {
                    "type": "integer",
                    "description": "File size in bytes (optional)"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0}
                    },
                    "description": "Pagination parameters for list operations"
                }
            },
            "required": ["action"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "statusCode": {"type": "integer", "description": "HTTP status code"},
                "body": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "file_id": {"type": "string"},
                                    "filename": {"type": "string"},
                                    "content_type": {"type": "string"},
                                    "file_type": {"type": "string"},
                                    "patient_id": {"type": "string"},
                                    "file_size": {"type": "integer"},
                                    "s3_key": {"type": "string"},
                                    "classification": {"type": "object"},
                                    "created_at": {"type": "string"},
                                    "updated_at": {"type": "string"}
                                }
                            }
                        },
                        "file": {
                            "type": "object",
                            "properties": {
                                "file_id": {"type": "string"},
                                "filename": {"type": "string"},
                                "content_type": {"type": "string"},
                                "file_type": {"type": "string"},
                                "patient_id": {"type": "string"},
                                "file_size": {"type": "integer"},
                                "s3_key": {"type": "string"},
                                "classification": {"type": "object"},
                                "created_at": {"type": "string"},
                                "updated_at": {"type": "string"}
                            }
                        },

                        "classification_result": {
                            "type": "object",
                            "properties": {
                                "document_type": {"type": "string"},
                                "confidence": {"type": "number"},
                                "extracted_data": {"type": "object"}
                            }
                        },
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "limit": {"type": "integer"},
                                "offset": {"type": "integer"},
                                "total": {"type": "integer"},
                                "count": {"type": "integer"}
                            }
                        },
                        "message": {"type": "string", "description": "Success or error message"}
                    }
                }
            }
        }
    )


def get_all_tool_schemas() -> List[agentcore.CfnGatewayTarget.ToolDefinitionProperty]:
    """Get all tool schemas for the gateway target."""
    return [
        get_patients_tool_schema(),
        get_medics_tool_schema(),
        get_exams_tool_schema(),
        get_reservations_tool_schema(),
        get_files_tool_schema()
    ]

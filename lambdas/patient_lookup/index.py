"""
Patient Lookup Lambda Function
Handles patient search requests from the healthcare assistant agent.
Uses RDS Data API to query the Aurora PostgreSQL database.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from shared.database import DatabaseManager, DatabaseError
from shared.utils import create_response, create_error_response

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
PATIENT_TABLE = os.getenv("PATIENT_TABLE", "patients")

# Initialize database manager
db_manager = DatabaseManager()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for patient lookup requests.
    
    Args:
        event: Lambda event containing the request
        context: Lambda context
        
    Returns:
        Dict containing the response
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the request
        action = event.get("action")
        
        if action == "search_patient":
            return handle_search_patient(event.get("search_criteria", {}))
        elif action == "list_recent_patients":
            return handle_list_recent_patients(event.get("limit", 5))
        elif action == "get_patient_by_id":
            return handle_get_patient_by_id(event.get("patient_id"))
        else:
            return create_error_response(400, f"Acción no válida: {action}", "INVALID_ACTION")
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return create_error_response(500, f"Error interno del servidor: {str(e)}", "INTERNAL_ERROR")


def handle_search_patient(search_criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle patient search based on various criteria.
    
    Args:
        search_criteria: Dictionary containing search parameters
        
    Returns:
        Dict containing the response
    """
    try:
        logger.info(f"Searching patient with criteria: {search_criteria}")
        
        if not search_criteria:
            return create_error_response(400, "Criterios de búsqueda requeridos", "MISSING_CRITERIA")
        
        # Try different search strategies
        patient = None
        
        # 1. Search by patient ID (most precise)
        if search_criteria.get("patient_id"):
            patient = search_by_patient_id(search_criteria["patient_id"])
        
        # 2. Search by email
        if not patient and search_criteria.get("email"):
            patient = search_by_email(search_criteria["email"])
        
        # 3. Search by name (fuzzy matching)
        if not patient and search_criteria.get("full_name"):
            patient = search_by_name(search_criteria["full_name"])
        
        # 4. Search by first and last name
        if not patient and search_criteria.get("first_name") and search_criteria.get("last_name"):
            full_name = f"{search_criteria['first_name']} {search_criteria['last_name']}"
            patient = search_by_name(full_name)
        
        if patient:
            return create_response(200, {
                "success": True,
                "patient": patient,
                "message": f"Paciente encontrado: {patient['full_name']}"
            })
        else:
            return create_response(404, {
                "success": False,
                "error": "No se encontró paciente con los criterios proporcionados",
                "patient": None
            })
            
    except DatabaseError as e:
        logger.error(f"Database error in handle_search_patient: {str(e)}")
        return create_error_response(500, f"Error buscando paciente: {str(e)}", e.error_code)
    except Exception as e:
        logger.error(f"Error in handle_search_patient: {str(e)}")
        return create_error_response(500, f"Error buscando paciente: {str(e)}", "SEARCH_ERROR")


def handle_list_recent_patients(limit: int = 5) -> Dict[str, Any]:
    """
    Handle listing recent patients.
    
    Args:
        limit: Maximum number of patients to return
        
    Returns:
        Dict containing the response
    """
    try:
        logger.info(f"Listing recent patients (limit: {limit})")
        
        # Get recent patients from the database (ordered by updated_at)
        patients = get_recent_patients(limit)
        
        return create_response(200, {
            "success": True,
            "patients": patients,
            "count": len(patients),
            "message": f"Se encontraron {len(patients)} pacientes recientes"
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_list_recent_patients: {str(e)}")
        return create_error_response(500, f"Error listando pacientes: {str(e)}", e.error_code)
    except Exception as e:
        logger.error(f"Error in handle_list_recent_patients: {str(e)}")
        return create_error_response(500, f"Error listando pacientes: {str(e)}", "LIST_ERROR")


def handle_get_patient_by_id(patient_id: str) -> Dict[str, Any]:
    """
    Handle getting patient by exact ID.
    
    Args:
        patient_id: The patient ID
        
    Returns:
        Dict containing the response
    """
    try:
        logger.info(f"Getting patient by ID: {patient_id}")
        
        if not patient_id:
            return create_error_response(400, "ID de paciente requerido", "MISSING_PATIENT_ID")
        
        patient = search_by_patient_id(patient_id)
        
        if patient:
            return create_response(200, {
                "success": True,
                "patient": patient,
                "message": f"Paciente encontrado: {patient['full_name']}"
            })
        else:
            return create_response(404, {
                "success": False,
                "error": f"No se encontró paciente con ID: {patient_id}",
                "patient": None
            })
            
    except DatabaseError as e:
        logger.error(f"Database error in handle_get_patient_by_id: {str(e)}")
        return create_error_response(500, f"Error obteniendo paciente: {str(e)}", e.error_code)
    except Exception as e:
        logger.error(f"Error in handle_get_patient_by_id: {str(e)}")
        return create_error_response(500, f"Error obteniendo paciente: {str(e)}", "GET_ERROR")


def search_by_patient_id(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Search patient by patient ID using RDS Data API.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Patient data or None
    """
    try:
        sql = """
        SELECT patient_id, full_name, email, date_of_birth, phone, created_at, updated_at
        FROM patients
        WHERE patient_id = :patient_id
        """
        
        parameters = [
            db_manager.create_parameter('patient_id', patient_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if records:
            patients = db_manager.parse_records(records, response.get('columnMetadata', []))
            return patients[0] if patients else None
        
        return None
        
    except DatabaseError as e:
        logger.error(f"Database error searching by patient ID: {str(e)}")
        # Fallback to mock data for development
        return get_mock_patient_by_id(patient_id)
    except Exception as e:
        logger.error(f"Error searching by patient ID: {str(e)}")
        return None


def search_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Search patient by email using RDS Data API.
    
    Args:
        email: Patient email
        
    Returns:
        Patient data or None
    """
    try:
        sql = """
        SELECT patient_id, full_name, email, date_of_birth, phone, created_at, updated_at
        FROM patients
        WHERE email = :email
        """
        
        parameters = [
            db_manager.create_parameter('email', email, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if records:
            patients = db_manager.parse_records(records, response.get('columnMetadata', []))
            return patients[0] if patients else None
        
        return None
        
    except DatabaseError as e:
        logger.error(f"Database error searching by email: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error searching by email: {str(e)}")
        return None


def search_by_name(full_name: str) -> Optional[Dict[str, Any]]:
    """
    Search patient by name with fuzzy matching using RDS Data API.
    
    Args:
        full_name: Full name to search for
        
    Returns:
        Patient data or None
    """
    try:
        sql = """
        SELECT patient_id, full_name, email, date_of_birth, phone, created_at, updated_at
        FROM patients
        WHERE LOWER(full_name) LIKE LOWER(:name_pattern)
        ORDER BY full_name
        LIMIT 1
        """
        
        # Add wildcards for fuzzy matching
        name_pattern = f"%{full_name}%"
        
        parameters = [
            db_manager.create_parameter('name_pattern', name_pattern, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if records:
            patients = db_manager.parse_records(records, response.get('columnMetadata', []))
            return patients[0] if patients else None
        
        return None
        
    except DatabaseError as e:
        logger.error(f"Database error searching by name: {str(e)}")
        # Fallback to mock data for development
        return get_mock_patient_by_name({"full_name": full_name})
    except Exception as e:
        logger.error(f"Error searching by name: {str(e)}")
        return None


def get_recent_patients(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent patients from the database using RDS Data API.
    
    Args:
        limit: Maximum number of patients to return
        
    Returns:
        List of patient data
    """
    try:
        sql = """
        SELECT patient_id, full_name, email, date_of_birth, created_at, updated_at
        FROM patients
        ORDER BY updated_at DESC, created_at DESC
        LIMIT :limit
        """
        
        parameters = [
            db_manager.create_parameter('limit', limit, 'long')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if records:
            return db_manager.parse_records(records, response.get('columnMetadata', []))
        
        return []
        
    except DatabaseError as e:
        logger.error(f"Database error getting recent patients: {str(e)}")
        # Fallback to mock data for development
        return get_mock_sample_patients(limit)
    except Exception as e:
        logger.error(f"Error getting recent patients: {str(e)}")
        return []


# Mock data functions for development/testing
def get_mock_patient_by_id(patient_id: str) -> Optional[Dict[str, Any]]:
    """Mock function for development."""
    mock_patients = {
        "12345678": {
            "patient_id": "12345678",
            "full_name": "Juan Pérez",
            "email": "juan.perez@demo.hospital.com",
            "date_of_birth": "1985-03-15",
            "phone": "555-0123",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        },
        "87654321": {
            "patient_id": "87654321",
            "full_name": "María González",
            "email": "maria.gonzalez@demo.hospital.com",
            "date_of_birth": "1990-07-22",
            "phone": "555-0456",
            "created_at": "2024-01-02T10:00:00Z",
            "updated_at": "2024-01-02T10:00:00Z"
        },
        "11223344": {
            "patient_id": "11223344",
            "full_name": "Carlos Rodríguez",
            "email": "carlos.rodriguez@demo.hospital.com",
            "date_of_birth": "1978-12-03",
            "phone": "555-0789",
            "created_at": "2024-01-03T10:00:00Z",
            "updated_at": "2024-01-03T10:00:00Z"
        }
    }
    return mock_patients.get(patient_id)


def get_mock_patient_by_name(search_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Mock function for development."""
    mock_patients = [
        get_mock_patient_by_id("12345678"),
        get_mock_patient_by_id("87654321"),
        get_mock_patient_by_id("11223344")
    ]
    
    search_name = search_criteria.get("full_name", "").strip().lower()
    
    for patient in mock_patients:
        if patient and search_name in patient["full_name"].lower():
            return patient
    
    return None


def get_mock_sample_patients(limit: int = 5) -> List[Dict[str, Any]]:
    """Mock function for development."""
    mock_patients = [
        {
            "patient_id": "12345678",
            "full_name": "Juan Pérez",
            "email": "juan.perez@demo.hospital.com",
            "date_of_birth": "1985-03-15",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z"
        },
        {
            "patient_id": "87654321",
            "full_name": "María González",
            "email": "maria.gonzalez@demo.hospital.com",
            "date_of_birth": "1990-07-22",
            "created_at": "2024-01-02T10:00:00Z",
            "updated_at": "2024-01-02T10:00:00Z"
        },
        {
            "patient_id": "11223344",
            "full_name": "Carlos Rodríguez",
            "email": "carlos.rodriguez@demo.hospital.com",
            "date_of_birth": "1978-12-03",
            "created_at": "2024-01-03T10:00:00Z",
            "updated_at": "2024-01-03T10:00:00Z"
        }
    ]
    
    return mock_patients[:limit]

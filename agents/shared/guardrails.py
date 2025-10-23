"""
PII/PHI protection and Bedrock Guardrails integration for healthcare assistant.
Implements strict no-logging policy and automatic content filtering.
"""

import boto3
import re
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from botocore.exceptions import ClientError
from .config import get_agent_config
from .utils import get_logger

logger = get_logger(__name__)


class PIIProtectionManager:
    """
    Manages PII/PHI protection with strict no-logging policy.
    """
    
    # PII/PHI patterns for detection
    PII_PATTERNS = {
        'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'cedula': r'\b\d{8,12}\b',  # Colombian cedula pattern
        'medical_record': r'\b(MR|mr|Medical Record|Historia Clínica)[-\s]?\d+\b',
        'date_of_birth': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Calle|Carrera|Avenida)\b'
    }
    
    # Medical/PHI terms that should be handled carefully
    PHI_TERMS = [
        'diagnosis', 'diagnóstico', 'enfermedad', 'síntoma', 'medicamento',
        'tratamiento', 'cirugía', 'operación', 'laboratorio', 'examen',
        'resultado', 'análisis', 'biopsia', 'radiografía', 'resonancia',
        'tomografía', 'ecografía', 'electrocardiograma', 'presión arterial',
        'glucosa', 'colesterol', 'hemoglobina', 'diabetes', 'hipertensión',
        'cáncer', 'tumor', 'alergia', 'medicación', 'dosis', 'prescripción'
    ]
    
    def __init__(self):
        """Initialize PII protection manager."""
        self.config = get_agent_config()
        self.logger = logger
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PII_PATTERNS.items()
        }
    
    def detect_pii_phi(self, text: str) -> Dict[str, Any]:
        """
        Detect PII/PHI in text without logging the actual content.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict[str, Any]: Detection results (no actual PII/PHI content)
        """
        if not text:
            return {"has_pii": False, "has_phi": False, "detected_types": []}
        
        detected_types = []
        
        # Check for PII patterns
        for pii_type, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                detected_types.append(pii_type)
        
        # Check for PHI terms
        text_lower = text.lower()
        phi_detected = any(term in text_lower for term in self.PHI_TERMS)
        
        if phi_detected:
            detected_types.append("medical_phi")
        
        return {
            "has_pii": len([t for t in detected_types if t != "medical_phi"]) > 0,
            "has_phi": phi_detected,
            "detected_types": detected_types,
            "text_length": len(text),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def sanitize_for_logging(self, data: Any) -> Any:
        """
        Sanitize data for logging by removing/masking PII/PHI.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Any: Sanitized data safe for logging
        """
        if isinstance(data, str):
            # For strings, check for PII/PHI and mask if found
            detection = self.detect_pii_phi(data)
            if detection["has_pii"] or detection["has_phi"]:
                return f"[PROTECTED_CONTENT:{','.join(detection['detected_types'])}:{len(data)}chars]"
            return data
        
        elif isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Mask sensitive keys
                if key.lower() in [
                    'patient_id', 'cedula', 'ssn', 'phone', 'email', 
                    'address', 'full_name', 'first_name', 'last_name',
                    'medical_history', 'lab_results', 'diagnosis',
                    'medical_record_number', 'date_of_birth'
                ]:
                    sanitized[key] = f"[PROTECTED_{key.upper()}]"
                else:
                    sanitized[key] = self.sanitize_for_logging(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self.sanitize_for_logging(item) for item in data]
        
        else:
            return data
    
    def validate_response_safety(self, response: str) -> Dict[str, Any]:
        """
        Validate that response doesn't contain inappropriate PII/PHI disclosure.
        
        Args:
            response: Response text to validate
            
        Returns:
            Dict[str, Any]: Validation result
        """
        detection = self.detect_pii_phi(response)
        
        # Determine if response is safe
        safe = True
        issues = []
        
        if detection["has_pii"]:
            # Check if PII is in appropriate medical context
            pii_types = [t for t in detection["detected_types"] if t != "medical_phi"]
            if pii_types:
                safe = False
                issues.append(f"Contains PII: {', '.join(pii_types)}")
        
        # PHI is generally acceptable in medical context but should be noted
        if detection["has_phi"]:
            issues.append("Contains medical PHI (acceptable in medical context)")
        
        return {
            "safe": safe,
            "issues": issues,
            "detection_summary": detection,
            "validation_timestamp": datetime.utcnow().isoformat()
        }


class BedrockGuardrailsManager:
    """
    Manages Bedrock Guardrails integration for automatic content filtering.
    """
    
    def __init__(self):
        """Initialize Bedrock Guardrails manager."""
        self.config = get_agent_config()
        self.logger = logger
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        
        # Guardrails configuration
        self.guardrail_id = self.config.guardrail_id
        self.guardrail_version = self.config.guardrail_version
        
        # Track guardrail usage
        self.guardrail_calls = 0
        self.blocked_content_count = 0
    
    async def apply_guardrails(
        self, 
        content: str, 
        content_type: str = "input"
    ) -> Dict[str, Any]:
        """
        Apply Bedrock Guardrails to content.
        
        Args:
            content: Content to filter
            content_type: Type of content (input, output)
            
        Returns:
            Dict[str, Any]: Guardrail result
        """
        if not self.guardrail_id or not self.guardrail_version:
            self.logger.warning("Guardrails not configured - content not filtered")
            return {
                "filtered": False,
                "safe": True,
                "content": content,
                "message": "Guardrails not configured"
            }
        
        try:
            self.guardrail_calls += 1
            
            # Apply guardrail
            response = self.bedrock_runtime.apply_guardrail(
                guardrailIdentifier=self.guardrail_id,
                guardrailVersion=self.guardrail_version,
                source=content_type.upper(),
                content=[
                    {
                        'text': {
                            'text': content
                        }
                    }
                ]
            )
            
            # Process guardrail response
            action = response.get('action', 'NONE')
            filtered_content = content
            
            if action == 'GUARDRAIL_INTERVENED':
                self.blocked_content_count += 1
                
                # Get filtered content if available
                outputs = response.get('outputs', [])
                if outputs and 'text' in outputs[0]:
                    filtered_content = outputs[0]['text']
                else:
                    filtered_content = "[CONTENT_FILTERED_BY_GUARDRAILS]"
                
                self.logger.info("Content filtered by Bedrock Guardrails")
                
                return {
                    "filtered": True,
                    "safe": False,
                    "content": filtered_content,
                    "action": action,
                    "assessments": response.get('assessments', []),
                    "message": "Contenido filtrado por políticas de seguridad"
                }
            
            else:
                return {
                    "filtered": False,
                    "safe": True,
                    "content": content,
                    "action": action,
                    "message": "Contenido aprobado por políticas de seguridad"
                }
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            self.logger.error(f"Bedrock Guardrails error: {error_code}")
            
            # Fail safe - if guardrails fail, be conservative
            return {
                "filtered": True,
                "safe": False,
                "content": "[CONTENT_UNAVAILABLE_DUE_TO_SAFETY_CHECK_ERROR]",
                "error": error_code,
                "message": "Error en verificación de seguridad - contenido no disponible"
            }
        
        except Exception as e:
            self.logger.error(f"Unexpected guardrails error: {str(e)}")
            
            # Fail safe
            return {
                "filtered": True,
                "safe": False,
                "content": "[CONTENT_UNAVAILABLE_DUE_TO_ERROR]",
                "error": str(e),
                "message": "Error en sistema de seguridad - contenido no disponible"
            }
    
    def get_guardrail_stats(self) -> Dict[str, Any]:
        """
        Get guardrail usage statistics.
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return {
            "total_calls": self.guardrail_calls,
            "blocked_content_count": self.blocked_content_count,
            "block_rate": (
                self.blocked_content_count / self.guardrail_calls 
                if self.guardrail_calls > 0 else 0
            ),
            "guardrail_configured": bool(self.guardrail_id and self.guardrail_version),
            "guardrail_id": self.guardrail_id,
            "guardrail_version": self.guardrail_version
        }


class HealthcareComplianceManager:
    """
    Manages healthcare-specific compliance requirements.
    """
    
    def __init__(self):
        """Initialize healthcare compliance manager."""
        self.pii_manager = PIIProtectionManager()
        self.guardrails_manager = BedrockGuardrailsManager()
        self.logger = logger
    
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input with full compliance checks.
        
        Args:
            user_input: User's input message
            
        Returns:
            Dict[str, Any]: Processed input with compliance info
        """
        try:
            # Apply guardrails to input
            guardrail_result = await self.guardrails_manager.apply_guardrails(
                user_input, "input"
            )
            
            # Detect PII/PHI for logging decisions
            pii_detection = self.pii_manager.detect_pii_phi(user_input)
            
            # Determine logging policy
            should_log = not (pii_detection["has_pii"] or pii_detection["has_phi"])
            
            return {
                "processed_input": guardrail_result["content"],
                "safe_for_processing": guardrail_result["safe"],
                "guardrail_applied": guardrail_result["filtered"],
                "pii_phi_detected": pii_detection,
                "should_log": should_log,
                "compliance_message": guardrail_result.get("message", ""),
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user input for compliance: {str(e)}")
            
            # Fail safe - be conservative
            return {
                "processed_input": "[INPUT_PROCESSING_ERROR]",
                "safe_for_processing": False,
                "guardrail_applied": True,
                "pii_phi_detected": {"has_pii": True, "has_phi": True, "detected_types": ["unknown"]},
                "should_log": False,
                "compliance_message": "Error en procesamiento de entrada - aplicando políticas conservadoras",
                "error": str(e)
            }
    
    async def process_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Process agent response with compliance checks.
        
        Args:
            response: Agent's response
            
        Returns:
            Dict[str, Any]: Processed response with compliance info
        """
        try:
            # Apply guardrails to output
            guardrail_result = await self.guardrails_manager.apply_guardrails(
                response, "output"
            )
            
            # Validate response safety
            safety_validation = self.pii_manager.validate_response_safety(response)
            
            return {
                "processed_response": guardrail_result["content"],
                "safe_for_output": guardrail_result["safe"] and safety_validation["safe"],
                "guardrail_applied": guardrail_result["filtered"],
                "safety_validation": safety_validation,
                "compliance_message": guardrail_result.get("message", ""),
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing agent response for compliance: {str(e)}")
            
            # Fail safe
            return {
                "processed_response": "[RESPONSE_PROCESSING_ERROR]",
                "safe_for_output": False,
                "guardrail_applied": True,
                "safety_validation": {"safe": False, "issues": ["processing_error"]},
                "compliance_message": "Error en procesamiento de respuesta - aplicando políticas conservadoras",
                "error": str(e)
            }
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get compliance system summary.
        
        Returns:
            Dict[str, Any]: Compliance summary
        """
        return {
            "pii_protection_active": True,
            "phi_protection_active": True,
            "guardrails_stats": self.guardrails_manager.get_guardrail_stats(),
            "strict_no_logging_policy": True,
            "healthcare_compliance_mode": True,
            "summary_timestamp": datetime.utcnow().isoformat()
        }


# Global compliance manager instance
_global_compliance_manager = None


def get_compliance_manager() -> HealthcareComplianceManager:
    """
    Get global compliance manager instance.
    
    Returns:
        HealthcareComplianceManager: Global compliance manager
    """
    global _global_compliance_manager
    
    if _global_compliance_manager is None:
        _global_compliance_manager = HealthcareComplianceManager()
    
    return _global_compliance_manager


# Export main classes and functions
__all__ = [
    "PIIProtectionManager",
    "BedrockGuardrailsManager", 
    "HealthcareComplianceManager",
    "get_compliance_manager"
]

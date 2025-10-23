"""
Patient identification system for consistent patient context across agents.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

from .utils import get_logger, sanitize_for_logging
from .healthcare_api_tools import query_patient_api

logger = get_logger(__name__)


@dataclass
class PatientIdentifier:
    """Patient identifier with type and confidence."""
    value: str
    identifier_type: str  # 'id', 'name', 'cedula', 'phone', 'email'
    confidence: float  # 0.0 to 1.0
    source: str  # Where the identifier was extracted from


class PatientIdentificationSystem:
    """
    System for identifying and managing patient context consistently across agents.
    """
    
    def __init__(self):
        """Initialize patient identification system."""
        self.logger = logger
        
        # Patterns for different identifier types
        self.patterns = {
            'cedula': [
                r'\b(?:cedula|cédula|ci|c\.i\.?)\s*:?\s*(\d{7,12})\b',
                r'\b(\d{8,12})\b(?=\s*(?:cedula|cédula|ci|c\.i\.?))',
                r'\bcedula\s+(\d{7,12})\b'
            ],
            'patient_id': [
                r'\b(?:id|patient_id|paciente_id)\s*:?\s*([a-f0-9-]{36})\b',
                r'\b([a-f0-9-]{36})\b'
            ],
            'phone': [
                r'\b(?:tel|teléfono|telefono|phone|celular)\s*:?\s*(\+?[\d\s\-\(\)]{8,15})\b',
                r'\b(\+?[\d\s\-\(\)]{10,15})\b'
            ],
            'email': [
                r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
            ]
        }
        
        # Spanish name patterns
        self.name_patterns = [
            r'(?:paciente|patient)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'(?:esta sesión es del paciente|this session is for patient)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)'
        ]
        
        # Cache for resolved patients
        self.patient_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = 300  # 5 minutes
    
    def extract_identifiers(self, text: str) -> List[PatientIdentifier]:
        """
        Extract patient identifiers from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[PatientIdentifier]: Found identifiers
        """
        identifiers = []
        text_lower = text.lower()
        
        try:
            # Extract structured identifiers
            for identifier_type, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1).strip()
                        confidence = self._calculate_confidence(identifier_type, value, text)
                        
                        identifiers.append(PatientIdentifier(
                            value=value,
                            identifier_type=identifier_type,
                            confidence=confidence,
                            source="pattern_extraction"
                        ))
            
            # Extract names with context
            for pattern in self.name_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip()
                    if self._is_valid_name(name):
                        confidence = self._calculate_name_confidence(name, text)
                        
                        identifiers.append(PatientIdentifier(
                            value=name,
                            identifier_type="name",
                            confidence=confidence,
                            source="name_extraction"
                        ))
            
            # Remove duplicates and sort by confidence
            identifiers = self._deduplicate_identifiers(identifiers)
            identifiers.sort(key=lambda x: x.confidence, reverse=True)
            
            return identifiers
            
        except Exception as e:
            self.logger.error(f"Error extracting identifiers: {str(e)}")
            return []
    
    def _calculate_confidence(self, identifier_type: str, value: str, context: str) -> float:
        """Calculate confidence score for an identifier."""
        confidence = 0.5  # Base confidence
        
        # Type-specific confidence adjustments
        if identifier_type == 'cedula':
            if len(value) >= 8 and value.isdigit():
                confidence += 0.3
            if any(keyword in context.lower() for keyword in ['cedula', 'cédula', 'ci']):
                confidence += 0.2
        
        elif identifier_type == 'patient_id':
            if len(value) == 36 and '-' in value:  # UUID format
                confidence += 0.4
            if 'patient_id' in context.lower():
                confidence += 0.2
        
        elif identifier_type == 'phone':
            if len(value.replace(' ', '').replace('-', '')) >= 10:
                confidence += 0.3
            if any(keyword in context.lower() for keyword in ['tel', 'phone', 'celular']):
                confidence += 0.2
        
        elif identifier_type == 'email':
            if '@' in value and '.' in value:
                confidence += 0.4
        
        return min(confidence, 1.0)
    
    def _calculate_name_confidence(self, name: str, context: str) -> float:
        """Calculate confidence score for a name."""
        confidence = 0.3  # Lower base confidence for names
        
        # Context-based confidence
        if 'esta sesión es del paciente' in context.lower():
            confidence += 0.5
        elif 'paciente' in context.lower():
            confidence += 0.3
        
        # Name structure confidence
        parts = name.split()
        if len(parts) >= 2:  # At least first and last name
            confidence += 0.2
        if len(parts) >= 3:  # Full name
            confidence += 0.1
        
        # Spanish name patterns
        if any(part.endswith(('ez', 'es', 'az')) for part in parts):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a string is a valid patient name."""
        if len(name) < 3:
            return False
        
        # Must contain only letters, spaces, and common name characters
        if not re.match(r'^[A-Za-záéíóúñÁÉÍÓÚÑ\s\-\'\.]+$', name):
            return False
        
        # Must have at least one uppercase letter (proper name)
        if not any(c.isupper() for c in name):
            return False
        
        # Exclude common non-name words
        excluded_words = {
            'doctor', 'medico', 'médico', 'enfermera', 'paciente', 'patient',
            'hospital', 'clinica', 'clínica', 'centro', 'salud'
        }
        
        name_lower = name.lower()
        if any(word in name_lower for word in excluded_words):
            return False
        
        return True
    
    def _deduplicate_identifiers(self, identifiers: List[PatientIdentifier]) -> List[PatientIdentifier]:
        """Remove duplicate identifiers, keeping the highest confidence."""
        seen = {}
        
        for identifier in identifiers:
            key = f"{identifier.identifier_type}:{identifier.value.lower()}"
            
            if key not in seen or identifier.confidence > seen[key].confidence:
                seen[key] = identifier
        
        return list(seen.values())
    
    async def resolve_patient(self, identifier: PatientIdentifier) -> Optional[Dict[str, Any]]:
        """
        Resolve patient identifier to patient data.
        
        Args:
            identifier: Patient identifier to resolve
            
        Returns:
            Optional[Dict[str, Any]]: Patient data if found
        """
        try:
            # Check cache first
            cache_key = f"{identifier.identifier_type}:{identifier.value}"
            if cache_key in self.patient_cache:
                cached_data = self.patient_cache[cache_key]
                if datetime.utcnow().timestamp() - cached_data['timestamp'] < self.cache_expiry:
                    self.logger.debug(f"Using cached patient data for: {identifier.identifier_type}")
                    return cached_data['data']
            
            # Query API
            result = await query_patient_api(identifier.value, identifier.identifier_type)
            
            if result.success and result.result:
                patient_data = result.result
                
                # Cache the result
                self.patient_cache[cache_key] = {
                    'data': patient_data,
                    'timestamp': datetime.utcnow().timestamp()
                }
                
                self.logger.info(f"Resolved patient: {identifier.identifier_type}")
                return patient_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error resolving patient identifier: {str(e)}")
            return None
    
    async def identify_patient_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Identify and resolve patient from text.
        
        Args:
            text: Text containing patient information
            
        Returns:
            Optional[Dict[str, Any]]: Patient data if identified
        """
        try:
            # Extract identifiers
            identifiers = self.extract_identifiers(text)
            
            if not identifiers:
                self.logger.debug("No patient identifiers found in text")
                return None
            
            # Try to resolve identifiers in order of confidence
            for identifier in identifiers:
                self.logger.debug(f"Trying to resolve: {identifier.identifier_type} = {identifier.value} (confidence: {identifier.confidence})")
                
                patient_data = await self.resolve_patient(identifier)
                if patient_data:
                    # Add identification metadata
                    patient_data['identification'] = {
                        'identifier_used': identifier.value,
                        'identifier_type': identifier.identifier_type,
                        'confidence': identifier.confidence,
                        'identified_at': datetime.utcnow().isoformat()
                    }
                    
                    return patient_data
            
            self.logger.info("No patient could be resolved from identifiers")
            return None
            
        except Exception as e:
            self.logger.error(f"Error identifying patient from text: {str(e)}")
            return None
    
    def create_patient_context(
        self, 
        patient_data: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Create standardized patient context for agents.
        
        Args:
            patient_data: Patient data from API
            session_id: Current session ID
            
        Returns:
            Dict[str, Any]: Standardized patient context
        """
        try:
            context = {
                'patient_id': patient_data.get('patient_id'),
                'full_name': patient_data.get('full_name'),
                'date_of_birth': patient_data.get('date_of_birth'),
                'session_id': session_id,
                'context_set_at': datetime.utcnow().isoformat(),
                'identification': patient_data.get('identification', {}),
                'api_data': patient_data
            }
            
            # Add computed fields
            if patient_data.get('date_of_birth'):
                try:
                    from datetime import date
                    birth_date = datetime.fromisoformat(patient_data['date_of_birth']).date()
                    today = date.today()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    context['computed_age'] = age
                except:
                    pass
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error creating patient context: {str(e)}")
            return {
                'session_id': session_id,
                'context_set_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def clear_cache(self) -> None:
        """Clear the patient cache."""
        self.patient_cache.clear()
        self.logger.info("Patient cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = datetime.utcnow().timestamp()
        valid_entries = sum(
            1 for entry in self.patient_cache.values()
            if current_time - entry['timestamp'] < self.cache_expiry
        )
        
        return {
            'total_entries': len(self.patient_cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.patient_cache) - valid_entries,
            'cache_expiry_seconds': self.cache_expiry
        }


# Global patient identification system instance
patient_identification_system = PatientIdentificationSystem()


async def identify_patient_from_message(
    message: str, 
    session_id: str
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to identify patient from message.
    
    Args:
        message: User message
        session_id: Session ID
        
    Returns:
        Optional[Dict[str, Any]]: Patient context if identified
    """
    patient_data = await patient_identification_system.identify_patient_from_text(message)
    
    if patient_data:
        return patient_identification_system.create_patient_context(patient_data, session_id)
    
    return None


def extract_patient_identifiers(text: str) -> List[PatientIdentifier]:
    """
    Convenience function to extract patient identifiers.
    
    Args:
        text: Text to analyze
        
    Returns:
        List[PatientIdentifier]: Found identifiers
    """
    return patient_identification_system.extract_identifiers(text)

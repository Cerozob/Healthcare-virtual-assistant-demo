"""
Pydantic models for structured output from Strands agents.

These models ensure type-safe, validated responses from the medical data generation agents.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    """Personal information for a patient in Latin American format."""

    nombre_completo: str = Field(description="Full name with two surnames")
    primer_nombre: str = Field(description="First name")
    segundo_nombre: Optional[str] = Field(
        default=None, description="Second name (optional)")
    primer_apellido: str = Field(description="First surname")
    segundo_apellido: str = Field(description="Second surname")
    fecha_nacimiento: str = Field(
        description="Birth date in DD/MM/YYYY format")
    edad: int = Field(description="Age in years", ge=0, le=120)
    sexo: str = Field(description="Gender: M or F", pattern="^[MF]$")
    tipo_documento: str = Field(
        description="Document type: DNI, Cédula, or Pasaporte")
    numero_documento: str = Field(description="Document number")
    direccion: Dict[str, str] = Field(
        description="Address with street, number, city, province, postal_code, country")
    telefono: str = Field(description="Phone number with country code")
    email: str = Field(description="Email address")


class MedicalCondition(BaseModel):
    """A medical condition or diagnosis."""

    codigo: Optional[str] = Field(
        default=None, description="ICD code if available")
    descripcion: str = Field(description="Condition description in Spanish")
    fecha_diagnostico: str = Field(
        description="Diagnosis date in DD/MM/YYYY format")
    estado: str = Field(description="Status: activo or resuelto")


class Medication(BaseModel):
    """A prescribed medication."""

    nombre: str = Field(description="Medication name in Spanish")
    dosis: str = Field(description="Dosage")
    frecuencia: str = Field(description="Frequency of administration")
    fecha_inicio: str = Field(description="Start date in DD/MM/YYYY format")
    activo: bool = Field(description="Whether medication is currently active")


class Procedure(BaseModel):
    """A medical procedure."""

    nombre: str = Field(description="Procedure name in Spanish")
    fecha: str = Field(description="Procedure date in DD/MM/YYYY format")
    notas: Optional[str] = Field(default=None, description="Additional notes")


class MedicalHistory(BaseModel):
    """Complete medical history for a patient."""

    conditions: List[MedicalCondition] = Field(
        default_factory=list, description="Medical conditions")
    medications: List[Medication] = Field(
        default_factory=list, description="Current and past medications")
    procedures: List[Procedure] = Field(
        default_factory=list, description="Medical procedures")


class LabResult(BaseModel):
    """A laboratory test result."""

    nombre_prueba: str = Field(description="Test name in Spanish")
    valor: str = Field(description="Test value")
    unidad: str = Field(description="Unit of measurement")
    rango_referencia: str = Field(description="Reference range")
    fecha: str = Field(description="Test date in DD/MM/YYYY format")
    estado: str = Field(description="Status: normal or anormal")


class PatientProfile(BaseModel):
    """Complete patient profile with all medical information."""

    patient_id: str = Field(description="Unique patient identifier (UUID)")
    personal_info: PersonalInfo = Field(description="Personal information")
    medical_history: MedicalHistory = Field(description="Medical history")
    lab_results: List[LabResult] = Field(
        default_factory=list, description="Laboratory results")
    source_scan: Optional[str] = Field(
        default=None, description="Path to source medical scan if used")


class DocumentNarratives(BaseModel):
    """Generated narratives for different document types."""

    historia_clinica: Optional[str] = Field(
        default=None, description="Clinical history narrative")
    resultados_laboratorio: Optional[str] = Field(
        default=None, description="Laboratory results narrative")
    receta_medica: Optional[str] = Field(
        default=None, description="Prescription narrative")
    informe_medico: Optional[str] = Field(
        default=None, description="General medical report narrative")


class ScannedDocumentAnalysis(BaseModel):
    """Simplified analysis of a scanned medical document for anonymized documents."""

    document_type: str = Field(
        default="documento_medico", description="Type of medical document identified")
    medical_conditions: Optional[List[str]] = Field(
        default=None, description="Medical conditions mentioned if any")
    medications: Optional[List[str]] = Field(
        default=None, description="Medications mentioned if any")
    lab_values: Optional[List[str]] = Field(
        default=None, description="Laboratory values mentioned if any")
    key_findings: Optional[List[str]] = Field(
        default=None, description="Key medical findings if any")
    document_language: str = Field(
        default="es", description="Language of the document")
    source_path: Optional[str] = Field(
        default=None, description="Path to the source scan file")

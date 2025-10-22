"""
Document generator module for creating PDF medical documents.

This module provides the MedicalDocumentGenerator class that creates
PDF medical documents based on patient profiles using reportlab.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from bedrock_agent import MedicalDataAgent
from data_loaders import PDFTemplateLoader

logger = logging.getLogger(__name__)


class MedicalDocumentGenerator:
    """Generates PDF medical documents."""

    def __init__(
        self,
        template_loader: PDFTemplateLoader,
        agent: MedicalDataAgent
    ):
        """Initialize with template loader and Bedrock agent.

        Args:
            template_loader: PDF template loader instance
            agent: Bedrock agent for content generation
        """
        self.template_loader = template_loader
        self.agent = agent

        # Initialize reportlab styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        logger.info("Initialized MedicalDocumentGenerator")

    def _setup_custom_styles(self):
        """Set up custom paragraph styles for medical documents."""
        # Header style
        self.styles.add(ParagraphStyle(
            name='MedicalHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.darkblue,
            leftIndent=0
        ))

        # Medical content style
        self.styles.add(ParagraphStyle(
            name='MedicalContent',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=20
        ))

        # Patient info style
        self.styles.add(ParagraphStyle(
            name='PatientInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=10
        ))

    def generate_document(
        self,
        profile: Dict,
        document_type: str,
        output_path: str,
        narrative: Optional[str] = None
    ) -> str:
        """Generate PDF document, return file path.

        Args:
            profile: Patient profile dictionary
            document_type: Type of document to generate
            output_path: Directory path for output file
            narrative: Pre-generated narrative content (optional)

        Returns:
            Full path to generated PDF file
        """
        logger.info(
            f"Generating {document_type} document for patient {profile.get('patient_id')}")

        try:
            # Create document content
            content = self._create_document_content(profile, document_type, narrative)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            patient_id = profile.get('patient_id', 'unknown')
            filename = f"patient_{patient_id}_{document_type}_{timestamp}.pdf"

            # Ensure output directory exists
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            file_path = output_dir / filename

            # Render PDF
            pdf_content = self._render_pdf(content, str(file_path))

            logger.info(f"Successfully generated document: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to generate document: {e}")
            raise

    def _create_document_content(
        self,
        profile: Dict,
        document_type: str,
        narrative: Optional[str] = None
    ) -> Dict:
        """Create structured document content.

        Args:
            profile: Patient profile dictionary
            document_type: Type of document to generate
            narrative: Pre-generated narrative content (optional)

        Returns:
            Structured document content dictionary
        """
        # Use provided narrative or generate it
        if narrative is None:
            # Convert profile dict to PatientProfile model for structured output
            from models import PatientProfile
            profile_model = PatientProfile.model_validate(profile)
            narrative = self.agent.generate_medical_narrative(
                profile=profile_model,
                document_type=document_type,
                language="es-LA"
            )

        # Extract patient information
        personal_info = profile.get('personal_info', {})
        medical_history = profile.get('medical_history', {})
        lab_results = profile.get('lab_results', [])

        # Create document structure based on type
        if document_type == "historia_clinica":
            content = self._create_clinical_history_content(
                personal_info, medical_history, lab_results, narrative
            )
        elif document_type == "resultados_laboratorio":
            content = self._create_lab_results_content(
                personal_info, lab_results, narrative
            )
        elif document_type == "receta_medica":
            content = self._create_prescription_content(
                personal_info, medical_history, narrative
            )
        else:
            content = self._create_general_medical_content(
                personal_info, medical_history, lab_results, narrative
            )

        return content

    def _create_clinical_history_content(
        self,
        personal_info: Dict,
        medical_history: Dict,
        lab_results: List[Dict],
        narrative: str
    ) -> Dict:
        """Create clinical history document content."""
        return {
            'title': 'HISTORIA CLÍNICA',
            'sections': [
                {
                    'title': 'INFORMACIÓN DEL PACIENTE',
                    'content': self._format_patient_info(personal_info)
                },
                {
                    'title': 'ANTECEDENTES MÉDICOS',
                    'content': self._format_medical_history(medical_history)
                },
                {
                    'title': 'RESULTADOS DE LABORATORIO',
                    'content': self._format_lab_results(lab_results)
                },
                {
                    'title': 'EVALUACIÓN CLÍNICA',
                    'content': narrative
                }
            ]
        }

    def _create_lab_results_content(
        self,
        personal_info: Dict,
        lab_results: List[Dict],
        narrative: str
    ) -> Dict:
        """Create laboratory results document content."""
        return {
            'title': 'RESULTADOS DE LABORATORIO',
            'sections': [
                {
                    'title': 'INFORMACIÓN DEL PACIENTE',
                    'content': self._format_patient_info(personal_info)
                },
                {
                    'title': 'RESULTADOS',
                    'content': self._format_lab_results(lab_results)
                },
                {
                    'title': 'INTERPRETACIÓN',
                    'content': narrative
                }
            ]
        }

    def _create_prescription_content(
        self,
        personal_info: Dict,
        medical_history: Dict,
        narrative: str
    ) -> Dict:
        """Create prescription document content."""
        return {
            'title': 'RECETA MÉDICA',
            'sections': [
                {
                    'title': 'INFORMACIÓN DEL PACIENTE',
                    'content': self._format_patient_info(personal_info)
                },
                {
                    'title': 'MEDICAMENTOS PRESCRITOS',
                    'content': self._format_medications(medical_history.get('medications', []))
                },
                {
                    'title': 'INDICACIONES',
                    'content': narrative
                }
            ]
        }

    def _create_general_medical_content(
        self,
        personal_info: Dict,
        medical_history: Dict,
        lab_results: List[Dict],
        narrative: str
    ) -> Dict:
        """Create general medical document content."""
        return {
            'title': 'INFORME MÉDICO',
            'sections': [
                {
                    'title': 'INFORMACIÓN DEL PACIENTE',
                    'content': self._format_patient_info(personal_info)
                },
                {
                    'title': 'CONTENIDO MÉDICO',
                    'content': narrative
                }
            ]
        }

    def _format_patient_info(self, personal_info: Dict) -> str:
        """Format patient information for document."""
        info_lines = []

        if personal_info.get('nombre_completo'):
            info_lines.append(
                f"<b>Nombre:</b> {personal_info['nombre_completo']}")

        if personal_info.get('fecha_nacimiento'):
            info_lines.append(
                f"<b>Fecha de Nacimiento:</b> {personal_info['fecha_nacimiento']}")

        if personal_info.get('edad'):
            info_lines.append(f"<b>Edad:</b> {personal_info['edad']} años")

        if personal_info.get('sexo'):
            sexo_text = "Masculino" if personal_info['sexo'] == 'M' else "Femenino"
            info_lines.append(f"<b>Sexo:</b> {sexo_text}")

        if personal_info.get('tipo_documento') and personal_info.get('numero_documento'):
            info_lines.append(
                f"<b>{personal_info['tipo_documento']}:</b> {personal_info['numero_documento']}")

        if personal_info.get('telefono'):
            info_lines.append(f"<b>Teléfono:</b> {personal_info['telefono']}")

        return "<br/>".join(info_lines)

    def _format_medical_history(self, medical_history: Dict) -> str:
        """Format medical history for document."""
        content_lines = []

        # Conditions
        conditions = medical_history.get('conditions', [])
        if conditions:
            content_lines.append("<b>Condiciones Médicas:</b>")
            for condition in conditions:
                desc = condition.get(
                    'descripcion', 'Condición no especificada')
                fecha = condition.get(
                    'fecha_diagnostico', 'Fecha no disponible')
                estado = condition.get('estado', 'desconocido')
                content_lines.append(
                    f"• {desc} (Diagnóstico: {fecha}, Estado: {estado})")

        # Procedures
        procedures = medical_history.get('procedures', [])
        if procedures:
            content_lines.append("<br/><b>Procedimientos:</b>")
            for procedure in procedures:
                nombre = procedure.get(
                    'nombre', 'Procedimiento no especificado')
                fecha = procedure.get('fecha', 'Fecha no disponible')
                content_lines.append(f"• {nombre} ({fecha})")

        return "<br/>".join(content_lines) if content_lines else "No hay antecedentes médicos registrados."

    def _format_lab_results(self, lab_results: List[Dict]) -> str:
        """Format laboratory results for document."""
        if not lab_results:
            return "No hay resultados de laboratorio disponibles."

        content_lines = []
        for result in lab_results:
            nombre = result.get('nombre_prueba', 'Prueba no especificada')
            valor = result.get('valor', 'N/A')
            unidad = result.get('unidad', '')
            rango = result.get('rango_referencia', 'N/A')
            fecha = result.get('fecha', 'Fecha no disponible')
            estado = result.get('estado', 'normal')

            estado_text = "🔴 ANORMAL" if estado == 'anormal' else "🟢 NORMAL"

            content_lines.append(
                f"<b>{nombre}:</b> {valor} {unidad} "
                f"(Rango: {rango}) - {estado_text} - {fecha}"
            )

        return "<br/>".join(content_lines)

    def _format_medications(self, medications: List[Dict]) -> str:
        """Format medications for document."""
        if not medications:
            return "No hay medicamentos prescritos."

        content_lines = []
        for med in medications:
            nombre = med.get('nombre', 'Medicamento no especificado')
            dosis = med.get('dosis', 'Dosis no especificada')
            frecuencia = med.get('frecuencia', 'Frecuencia no especificada')
            activo = med.get('activo', True)

            estado_text = "(ACTIVO)" if activo else "(SUSPENDIDO)"
            content_lines.append(
                f"• <b>{nombre}</b> - {dosis} - {frecuencia} {estado_text}")

        return "<br/>".join(content_lines)

    def _render_pdf(self, content: Dict, file_path: str) -> bytes:
        """Render content to PDF format.

        Args:
            content: Structured document content
            file_path: Output file path

        Returns:
            PDF content as bytes
        """
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Build document content
        story = []

        # Add synthetic data disclaimer at the top
        story.append(Paragraph(
            "<i>Este documento ha sido generado sintéticamente para propósitos de prueba.</i>",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1,
                     lineCap='round', color=colors.grey))
        story.append(Spacer(1, 20))

        # Add title
        title = content.get('title', 'DOCUMENTO MÉDICO')
        story.append(Paragraph(title, self.styles['MedicalHeader']))
        story.append(Spacer(1, 20))

        # Add generation date
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(
            Paragraph(f"<i>Generado el: {fecha_generacion}</i>", self.styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=1,
                     lineCap='round', color=colors.grey))
        story.append(Spacer(1, 20))

        # Add sections
        sections = content.get('sections', [])
        for section in sections:
            section_title = section.get('title', '')
            section_content = section.get('content', '')

            if section_title:
                story.append(
                    Paragraph(section_title, self.styles['SectionHeader']))

            if section_content:
                # Split content into paragraphs
                paragraphs = section_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(
                            Paragraph(para.strip(), self.styles['MedicalContent']))

            story.append(Spacer(1, 15))

        # Add footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1,
                     lineCap='round', color=colors.grey))

        # Build PDF
        doc.build(story)

        # Read and return PDF content
        with open(file_path, 'rb') as f:
            pdf_content = f.read()

        return pdf_content

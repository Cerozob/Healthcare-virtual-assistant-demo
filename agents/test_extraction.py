#!/usr/bin/env python3
"""
Test the extraction function directly.
"""

import re

def test_extraction():
    """Test the extraction patterns."""
    
    message_content = """Perfecto, he encontrado la información del paciente:

## **Información del Paciente Encontrado**

**📋 Datos Generales:**
- **Nombre completo:** Juan Pérez
- **Cédula:** 12345678
- **ID del Paciente:** 12345678
- **Número de Historia Clínica:** MRN-001

**📅 Información Personal:**
- **Fecha de nacimiento:** 15 de marzo de 1985
- **Teléfono:** 555-0123
- **Email:** juan.perez@email.com

¿Qué información específica necesitas sobre el paciente Juan Pérez? Puedo ayudarte con:
- Historial médico
- Programación de citas
- Revisión de tratamientos
- Cualquier otra consulta relacionada con su atención médica

El contexto del paciente Juan Pérez está ahora establecido para nuestra conversación."""

    print("Testing extraction patterns...")
    
    # Pattern 1: "Paciente encontrado: Name (Cédula: 12345678)"
    patient_pattern1 = r"Paciente encontrado:\s*([^(]+)\s*\(Cédula:\s*(\d+)\)"
    match = re.search(patient_pattern1, message_content)
    print(f"Pattern 1 match: {match}")
    
    # Pattern 2: Look for structured patient info in the response
    name_pattern = r"\*\*Nombre completo:\*\*\s*([^\n*]+)"
    cedula_pattern = r"\*\*Cédula:\*\*\s*(\d+)"
    
    name_match = re.search(name_pattern, message_content)
    cedula_match = re.search(cedula_pattern, message_content)
    
    print(f"Name match: {name_match}")
    print(f"Cedula match: {cedula_match}")
    
    if name_match and cedula_match:
        patient_name = name_match.group(1).strip()
        patient_id = cedula_match.group(1).strip()
        print(f"✅ Extracted: {patient_name} (ID: {patient_id})")
        return patient_id, patient_name
    
    # Pattern 3: Look for any mention of patient name and cedula
    general_pattern = r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)[^\d]*(\d{8,10})"
    matches = re.findall(general_pattern, message_content)
    
    print(f"General pattern matches: {matches}")
    
    for name, cedula in matches:
        # Filter out common non-name words
        if name.lower() not in ["información", "datos", "paciente", "cédula", "número", "historia"]:
            print(f"✅ General pattern extracted: {name} (ID: {cedula})")
            return cedula, name
    
    print("❌ No matches found")
    return None, None

if __name__ == "__main__":
    test_extraction()

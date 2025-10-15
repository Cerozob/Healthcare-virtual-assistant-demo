-- Migration: Add enhanced patient data models for medical history and chat integration
-- This migration extends the patient schema with medical history fields and creates
-- relationships between patients and processed documents

-- Add medical history fields to patients table
ALTER TABLE patients ADD COLUMN IF NOT EXISTS medical_history JSONB DEFAULT '{}';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_symptoms JSONB DEFAULT '[]';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS allergies JSONB DEFAULT '[]';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS current_medications JSONB DEFAULT '[]';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS chronic_conditions JSONB DEFAULT '[]';
ALTER TABLE patients ADD COLUMN IF NOT EXISTS blood_type VARCHAR(10);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS height_cm DECIMAL(5,2);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS weight_kg DECIMAL(5,2);

-- Create medical notes table for chat conversation observations
CREATE TABLE IF NOT EXISTS medical_notes (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    chat_session_id UUID,
    note_type VARCHAR(50) CHECK (note_type IN ('symptom', 'observation', 'diagnosis', 'treatment', 'general')),
    content TEXT NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    recorded_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create processed documents table
CREATE TABLE IF NOT EXISTS processed_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id UUID REFERENCES patients(patient_id) ON DELETE SET NULL,
    document_type VARCHAR(100),
    original_filename VARCHAR(500),
    s3_raw_key VARCHAR(500),
    s3_processed_key VARCHAR(500),
    extracted_data JSONB DEFAULT '{}',
    processing_date TIMESTAMP WITH TIME ZONE,
    kb_document_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create medical protocols table
CREATE TABLE IF NOT EXISTS medical_protocols (
    protocol_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    symptoms JSONB DEFAULT '[]',
    recommended_exams JSONB DEFAULT '[]',
    recommended_treatments JSONB DEFAULT '[]',
    priority_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Add scheduling agent metadata to reservations
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS scheduling_agent_metadata JSONB DEFAULT '{}';
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS auto_scheduled BOOLEAN DEFAULT false;
ALTER TABLE reservations ADD COLUMN IF NOT EXISTS protocol_id UUID REFERENCES medical_protocols(protocol_id) ON DELETE SET NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_medical_notes_patient ON medical_notes(patient_id);
CREATE INDEX IF NOT EXISTS idx_medical_notes_session ON medical_notes(chat_session_id);
CREATE INDEX IF NOT EXISTS idx_medical_notes_type ON medical_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_medical_notes_created ON medical_notes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_processed_docs_patient ON processed_documents(patient_id);
CREATE INDEX IF NOT EXISTS idx_processed_docs_type ON processed_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_processed_docs_date ON processed_documents(processing_date DESC);
CREATE INDEX IF NOT EXISTS idx_processed_docs_kb ON processed_documents(kb_document_id);

CREATE INDEX IF NOT EXISTS idx_protocols_active ON medical_protocols(is_active);
CREATE INDEX IF NOT EXISTS idx_protocols_priority ON medical_protocols(priority_level);

CREATE INDEX IF NOT EXISTS idx_reservations_protocol ON reservations(protocol_id);
CREATE INDEX IF NOT EXISTS idx_reservations_auto_scheduled ON reservations(auto_scheduled);

-- Add triggers for updated_at timestamps
CREATE TRIGGER update_medical_notes_updated_at BEFORE UPDATE ON medical_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_processed_documents_updated_at BEFORE UPDATE ON processed_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medical_protocols_updated_at BEFORE UPDATE ON medical_protocols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for patient medical summary
CREATE OR REPLACE VIEW patient_medical_summary AS
SELECT 
    p.patient_id,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.email,
    p.phone,
    p.date_of_birth,
    p.gender,
    p.blood_type,
    p.height_cm,
    p.weight_kg,
    p.medical_history,
    p.current_symptoms,
    p.allergies,
    p.current_medications,
    p.chronic_conditions,
    COUNT(DISTINCT mn.note_id) AS total_notes,
    COUNT(DISTINCT pd.id) AS total_documents,
    COUNT(DISTINCT r.reservation_id) AS total_reservations,
    MAX(mn.created_at) AS last_note_date,
    MAX(pd.processing_date) AS last_document_date,
    MAX(r.start_time) AS next_appointment
FROM patients p
LEFT JOIN medical_notes mn ON p.patient_id = mn.patient_id
LEFT JOIN processed_documents pd ON p.patient_id = pd.patient_id
LEFT JOIN reservations r ON p.patient_id = r.patient_id AND r.start_time > CURRENT_TIMESTAMP
GROUP BY p.patient_id, p.first_name, p.last_name, p.email, p.phone, p.date_of_birth, 
         p.gender, p.blood_type, p.height_cm, p.weight_kg, p.medical_history, 
         p.current_symptoms, p.allergies, p.current_medications, p.chronic_conditions;

-- Insert sample medical protocols
INSERT INTO medical_protocols (name, description, symptoms, recommended_exams, recommended_treatments, priority_level) VALUES
(
    'Chest Pain Protocol',
    'Protocol for patients presenting with chest pain symptoms',
    '["chest pain", "chest discomfort", "pressure in chest", "tightness in chest"]'::jsonb,
    '["ECG", "Chest X-Ray", "Blood Test - Complete Panel"]'::jsonb,
    '["Cardiology consultation", "Stress test if needed"]'::jsonb,
    3
),
(
    'Respiratory Symptoms Protocol',
    'Protocol for patients with respiratory complaints',
    '["cough", "shortness of breath", "wheezing", "difficulty breathing"]'::jsonb,
    '["Chest X-Ray", "Pulmonary Function Test"]'::jsonb,
    '["Respiratory therapy", "Pulmonology consultation"]'::jsonb,
    2
),
(
    'Joint Pain Protocol',
    'Protocol for patients with joint pain and mobility issues',
    '["joint pain", "knee pain", "hip pain", "swelling", "limited mobility"]'::jsonb,
    '["MRI - Knee", "X-Ray", "Blood Test - Complete Panel"]'::jsonb,
    '["Physical therapy", "Orthopedic consultation"]'::jsonb,
    1
),
(
    'Annual Physical Protocol',
    'Standard protocol for annual physical examinations',
    '["routine checkup", "annual physical", "preventive care"]'::jsonb,
    '["General Physical Exam", "Blood Test - Complete Panel"]'::jsonb,
    '["Follow-up as needed"]'::jsonb,
    1
);

-- Add sample medical notes for existing patients
INSERT INTO medical_notes (patient_id, note_type, content, severity, recorded_by) VALUES
(
    (SELECT patient_id FROM patients WHERE email = 'john.doe@email.com'),
    'symptom',
    'Patient reports occasional chest pain, especially during physical activity. Pain is described as pressure-like.',
    'medium',
    'Chat AI Assistant'
),
(
    (SELECT patient_id FROM patients WHERE email = 'jane.smith@email.com'),
    'symptom',
    'Patient has persistent cough for 2 weeks, mild shortness of breath. No fever reported.',
    'medium',
    'Chat AI Assistant'
),
(
    (SELECT patient_id FROM patients WHERE email = 'robert.johnson@email.com'),
    'observation',
    'Patient mentioned history of hypertension, currently on medication. Blood pressure readings have been stable.',
    'low',
    'Chat AI Assistant'
);

-- Update existing patients with sample medical history
UPDATE patients 
SET 
    medical_history = '{"previous_conditions": ["hypertension"], "surgeries": [], "hospitalizations": []}'::jsonb,
    current_symptoms = '["chest pain", "fatigue"]'::jsonb,
    allergies = '["penicillin"]'::jsonb,
    current_medications = '["lisinopril 10mg daily"]'::jsonb,
    blood_type = 'O+',
    height_cm = 175.0,
    weight_kg = 80.5
WHERE email = 'john.doe@email.com';

UPDATE patients 
SET 
    medical_history = '{"previous_conditions": [], "surgeries": [], "hospitalizations": []}'::jsonb,
    current_symptoms = '["cough", "shortness of breath"]'::jsonb,
    allergies = '[]'::jsonb,
    current_medications = '[]'::jsonb,
    blood_type = 'A+',
    height_cm = 165.0,
    weight_kg = 62.0
WHERE email = 'jane.smith@email.com';

UPDATE patients 
SET 
    medical_history = '{"previous_conditions": ["hypertension", "type 2 diabetes"], "surgeries": ["appendectomy 2010"], "hospitalizations": []}'::jsonb,
    current_symptoms = '[]'::jsonb,
    allergies = '["sulfa drugs"]'::jsonb,
    current_medications = '["metformin 500mg twice daily", "amlodipine 5mg daily"]'::jsonb,
    chronic_conditions = '["hypertension", "type 2 diabetes"]'::jsonb,
    blood_type = 'B+',
    height_cm = 180.0,
    weight_kg = 95.0
WHERE email = 'robert.johnson@email.com';

-- Add validation constraints
ALTER TABLE medical_notes ADD CONSTRAINT check_severity_not_null 
    CHECK (severity IS NOT NULL OR note_type = 'general');

ALTER TABLE medical_protocols ADD CONSTRAINT check_priority_range 
    CHECK (priority_level BETWEEN 1 AND 5);

-- Comments for documentation
COMMENT ON TABLE medical_notes IS 'Stores medical notes and observations from chat conversations';
COMMENT ON TABLE processed_documents IS 'Stores metadata and extracted data from processed medical documents';
COMMENT ON TABLE medical_protocols IS 'Stores company medical protocols for automated scheduling';
COMMENT ON COLUMN patients.medical_history IS 'JSONB field containing structured medical history data';
COMMENT ON COLUMN patients.current_symptoms IS 'JSONB array of current patient symptoms';
COMMENT ON COLUMN patients.allergies IS 'JSONB array of patient allergies';
COMMENT ON COLUMN patients.current_medications IS 'JSONB array of current medications';
COMMENT ON COLUMN reservations.scheduling_agent_metadata IS 'Metadata from AI scheduling agent decisions';
COMMENT ON COLUMN reservations.auto_scheduled IS 'Flag indicating if reservation was automatically scheduled by AI';

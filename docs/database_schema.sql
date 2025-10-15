-- Healthcare Management System Database Schema - PoC Simplified Version
-- PostgreSQL 17.5 compatible

-- Create ENUM types for better data integrity
CREATE TYPE reservation_status_enum AS ENUM ('scheduled', 'confirmed', 'completed', 'cancelled');

-- Patients table - Simplified for PoC
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Medics (Medical Professionals) table - Simplified for PoC
CREATE TABLE medics (
    medic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(200) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exams and Tests table - Simplified for PoC
CREATE TABLE exams (
    exam_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for medics and exams (many-to-many relationship) - Simplified
CREATE TABLE exam_medics (
    exam_id UUID REFERENCES exams(exam_id) ON DELETE CASCADE,
    medic_id UUID REFERENCES medics(medic_id) ON DELETE CASCADE,
    PRIMARY KEY (exam_id, medic_id)
);

-- Reservations (Time slots) table - Simplified for PoC
CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    medic_id UUID NOT NULL REFERENCES medics(medic_id) ON DELETE CASCADE,
    exam_id UUID NOT NULL REFERENCES exams(exam_id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status reservation_status_enum DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Essential indexes for PoC performance
CREATE INDEX idx_patients_name ON patients(full_name);
CREATE INDEX idx_medics_specialty ON medics(specialty);
CREATE INDEX idx_reservations_medic_time ON reservations(medic_id, start_time);
CREATE INDEX idx_reservations_patient ON reservations(patient_id);
CREATE INDEX idx_reservations_date ON reservations(start_time);

-- Sample data for PoC testing - Simplified
INSERT INTO patients (full_name, date_of_birth) VALUES
('John Doe', '1985-03-15'),
('Jane Smith', '1990-07-22'),
('Robert Johnson', '1978-11-08');

INSERT INTO medics (full_name, specialty) VALUES
('Dr. Sarah Wilson', 'Cardiology'),
('Dr. Michael Brown', 'Radiology'),
('Dr. Emily Davis', 'General Medicine'),
('Dr. James Miller', 'Orthopedics');

INSERT INTO exams (name, category, duration_minutes) VALUES
('Chest X-Ray', 'Radiology', 15),
('ECG', 'Cardiology', 20),
('Blood Test', 'Laboratory', 10),
('MRI - Knee', 'Radiology', 45),
('Physical Exam', 'General Medicine', 30);

-- Associate medics with exams they can perform - Simplified
INSERT INTO exam_medics (exam_id, medic_id) VALUES
-- Dr. Wilson (Cardiology) can do ECG and Physical Exam
((SELECT exam_id FROM exams WHERE name = 'ECG'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Sarah Wilson')),
((SELECT exam_id FROM exams WHERE name = 'Physical Exam'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Sarah Wilson')),

-- Dr. Brown (Radiology) can do X-Ray and MRI
((SELECT exam_id FROM exams WHERE name = 'Chest X-Ray'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Michael Brown')),
((SELECT exam_id FROM exams WHERE name = 'MRI - Knee'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Michael Brown')),

-- Dr. Davis (General Medicine) can do Physical Exam and Blood Test
((SELECT exam_id FROM exams WHERE name = 'Physical Exam'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Emily Davis')),
((SELECT exam_id FROM exams WHERE name = 'Blood Test'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. Emily Davis')),

-- Dr. Miller (Orthopedics) can do MRI and Physical Exam
((SELECT exam_id FROM exams WHERE name = 'MRI - Knee'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. James Miller')),
((SELECT exam_id FROM exams WHERE name = 'Physical Exam'), (SELECT medic_id FROM medics WHERE full_name = 'Dr. James Miller'));

-- Sample reservations - Simplified
INSERT INTO reservations (patient_id, medic_id, exam_id, start_time, end_time, status) VALUES
(
    (SELECT patient_id FROM patients WHERE full_name = 'John Doe'),
    (SELECT medic_id FROM medics WHERE full_name = 'Dr. Sarah Wilson'),
    (SELECT exam_id FROM exams WHERE name = 'ECG'),
    '2024-03-15 10:00:00+00',
    '2024-03-15 10:20:00+00',
    'scheduled'
),
(
    (SELECT patient_id FROM patients WHERE full_name = 'Jane Smith'),
    (SELECT medic_id FROM medics WHERE full_name = 'Dr. Michael Brown'),
    (SELECT exam_id FROM exams WHERE name = 'Chest X-Ray'),
    '2024-03-16 14:30:00+00',
    '2024-03-16 14:45:00+00',
    'confirmed'
);

-- Simplified view for common queries
CREATE VIEW reservation_details AS
SELECT 
    r.reservation_id,
    r.start_time,
    r.end_time,
    r.status,
    p.full_name AS patient_name,
    m.full_name AS medic_name,
    m.specialty,
    e.name AS exam_name,
    e.duration_minutes
FROM reservations r
JOIN patients p ON r.patient_id = p.patient_id
JOIN medics m ON r.medic_id = m.medic_id
JOIN exams e ON r.exam_id = e.exam_id;

-- Healthcare Management System Database Schema
-- This file documents the expected database schema for the healthcare system
-- Tables will be created automatically when first accessed by the application

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(255) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    age INTEGER,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    document_type VARCHAR(20),
    document_number VARCHAR(50),
    address JSONB,
    medical_history JSONB,
    lab_results JSONB,
    source_scan VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Medics table
CREATE TABLE IF NOT EXISTS medics (
    medic_id VARCHAR(255) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    specialization VARCHAR(100),
    license_number VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exams table
CREATE TABLE IF NOT EXISTS exams (
    exam_id VARCHAR(255) PRIMARY KEY,
    exam_name VARCHAR(200) NOT NULL UNIQUE,
    exam_type VARCHAR(100) NOT NULL,
    description TEXT,
    duration_minutes INTEGER DEFAULT 30,
    preparation_instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reservations table
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id VARCHAR(255) PRIMARY KEY,
    patient_id VARCHAR(255) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    medic_id VARCHAR(255) NOT NULL REFERENCES medics(medic_id) ON DELETE RESTRICT,
    exam_id VARCHAR(255) NOT NULL REFERENCES exams(exam_id) ON DELETE RESTRICT,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(medic_id, reservation_date, reservation_time)
);



-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_medics_email ON medics(email);
CREATE INDEX IF NOT EXISTS idx_medics_specialization ON medics(specialization);
CREATE INDEX IF NOT EXISTS idx_exams_type ON exams(exam_type);
CREATE INDEX IF NOT EXISTS idx_reservations_patient ON reservations(patient_id);
CREATE INDEX IF NOT EXISTS idx_reservations_medic ON reservations(medic_id);
CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(reservation_date);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);


CREATE INDEX IF NOT EXISTS idx_processed_documents_patient ON processed_documents(patient_id);
CREATE INDEX IF NOT EXISTS idx_processed_documents_processing_date ON processed_documents(processing_date);


-- Processed documents table for document workflow
CREATE TABLE IF NOT EXISTS processed_documents (
    document_id VARCHAR(255) PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES patients(patient_id) ON DELETE SET NULL,
    extracted_data JSONB NOT NULL,
    s3_uri VARCHAR(500) NOT NULL,
    processing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge base table for Bedrock (created manually by handler)
-- This table is managed by the Bedrock Knowledge Base service and requires vector extension

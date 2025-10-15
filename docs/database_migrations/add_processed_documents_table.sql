-- Migration: Add processed_documents table for storing extracted document data
-- Date: 2025-01-14
-- Description: Creates table to store processed documents with extracted data from BDA

-- Create processed_documents table
CREATE TABLE IF NOT EXISTS processed_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id VARCHAR(255) UNIQUE NOT NULL,
    patient_id VARCHAR(255),
    extracted_data JSONB NOT NULL,
    s3_uri VARCHAR(1000) NOT NULL,
    processing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to patients table (if patient_id exists)
    CONSTRAINT fk_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id)
        ON DELETE SET NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_processed_documents_patient_id 
    ON processed_documents(patient_id);

CREATE INDEX IF NOT EXISTS idx_processed_documents_processing_date 
    ON processed_documents(processing_date DESC);

CREATE INDEX IF NOT EXISTS idx_processed_documents_extracted_data 
    ON processed_documents USING GIN (extracted_data);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_processed_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_processed_documents_updated_at
    BEFORE UPDATE ON processed_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_processed_documents_updated_at();

-- Add comments for documentation
COMMENT ON TABLE processed_documents IS 'Stores processed medical documents with extracted data from Bedrock Data Automation';
COMMENT ON COLUMN processed_documents.document_id IS 'Unique identifier for the document';
COMMENT ON COLUMN processed_documents.patient_id IS 'Associated patient identifier (nullable)';
COMMENT ON COLUMN processed_documents.extracted_data IS 'JSON data extracted by BDA with PII anonymization';
COMMENT ON COLUMN processed_documents.s3_uri IS 'S3 URI of the processed document output';
COMMENT ON COLUMN processed_documents.processing_date IS 'Date when document was processed';

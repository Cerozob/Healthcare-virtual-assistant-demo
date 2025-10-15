-- Migration: Simplify schema for PoC
-- Date: 2025-01-14
-- Description: Removes unnecessary columns and tables to create a minimal PoC schema

-- Drop existing views that reference old columns
DROP VIEW IF EXISTS reservation_details CASCADE;
DROP VIEW IF EXISTS medic_availability CASCADE;
DROP VIEW IF EXISTS scheduling_conflicts CASCADE;
DROP VIEW IF EXISTS auto_scheduled_reservations CASCADE;
DROP VIEW IF EXISTS medic_schedule_summary CASCADE;
DROP VIEW IF EXISTS protocol_scheduling_recommendations CASCADE;

-- Drop functions that reference old columns
DROP FUNCTION IF EXISTS get_available_slots CASCADE;
DROP FUNCTION IF EXISTS auto_schedule_from_protocol CASCADE;

-- Drop medical_protocols table if it exists (not needed for PoC)
DROP TABLE IF EXISTS medical_protocols CASCADE;

-- Remove unnecessary columns from patients table
ALTER TABLE patients DROP COLUMN IF EXISTS email CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS phone CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS gender CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS address CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS emergency_contact_name CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS emergency_contact_phone CASCADE;
ALTER TABLE patients DROP COLUMN IF EXISTS updated_at CASCADE;

-- Combine first_name and last_name into full_name for patients
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'patients' AND column_name = 'first_name') THEN
        -- Add full_name column if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'patients' AND column_name = 'full_name') THEN
            ALTER TABLE patients ADD COLUMN full_name VARCHAR(200);
        END IF;
        
        -- Migrate data from first_name and last_name to full_name
        UPDATE patients SET full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') WHERE full_name IS NULL;
        
        -- Drop old columns
        ALTER TABLE patients DROP COLUMN first_name CASCADE;
        ALTER TABLE patients DROP COLUMN last_name CASCADE;
    END IF;
END $$;

-- Remove unnecessary columns from medics table
ALTER TABLE medics DROP COLUMN IF EXISTS email CASCADE;
ALTER TABLE medics DROP COLUMN IF EXISTS phone CASCADE;
ALTER TABLE medics DROP COLUMN IF EXISTS license_number CASCADE;
ALTER TABLE medics DROP COLUMN IF EXISTS years_experience CASCADE;
ALTER TABLE medics DROP COLUMN IF EXISTS is_active CASCADE;
ALTER TABLE medics DROP COLUMN IF EXISTS updated_at CASCADE;

-- Combine first_name and last_name into full_name for medics
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'medics' AND column_name = 'first_name') THEN
        -- Add full_name column if it doesn't exist
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'medics' AND column_name = 'full_name') THEN
            ALTER TABLE medics ADD COLUMN full_name VARCHAR(200);
        END IF;
        
        -- Migrate data from first_name and last_name to full_name
        UPDATE medics SET full_name = COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') WHERE full_name IS NULL;
        
        -- Drop old columns
        ALTER TABLE medics DROP COLUMN first_name CASCADE;
        ALTER TABLE medics DROP COLUMN last_name CASCADE;
    END IF;
END $$;

-- Remove unnecessary columns from exams table
ALTER TABLE exams DROP COLUMN IF EXISTS description CASCADE;
ALTER TABLE exams DROP COLUMN IF EXISTS preparation_instructions CASCADE;
ALTER TABLE exams DROP COLUMN IF EXISTS is_active CASCADE;
ALTER TABLE exams DROP COLUMN IF EXISTS updated_at CASCADE;

-- Remove unnecessary columns from reservations table
ALTER TABLE reservations DROP COLUMN IF EXISTS notes CASCADE;
ALTER TABLE reservations DROP COLUMN IF EXISTS updated_at CASCADE;
ALTER TABLE reservations DROP COLUMN IF EXISTS auto_scheduled CASCADE;
ALTER TABLE reservations DROP COLUMN IF EXISTS protocol_id CASCADE;
ALTER TABLE reservations DROP COLUMN IF EXISTS scheduling_agent_metadata CASCADE;

-- Drop unnecessary indexes
DROP INDEX IF EXISTS idx_patients_email;
DROP INDEX IF EXISTS idx_patients_name;
DROP INDEX IF EXISTS idx_medics_email;
DROP INDEX IF EXISTS idx_medics_license;
DROP INDEX IF EXISTS idx_exams_name;
DROP INDEX IF EXISTS idx_reservations_status;
DROP INDEX IF EXISTS idx_reservations_protocol;
DROP INDEX IF EXISTS idx_reservations_auto_scheduled;
DROP INDEX IF EXISTS idx_reservations_medic_status;

-- Create simplified view for reservation details
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

-- Update sample data to use full_name format
UPDATE patients SET full_name = 'John Doe' WHERE full_name LIKE 'John %' OR full_name = ' ';
UPDATE patients SET full_name = 'Jane Smith' WHERE full_name LIKE 'Jane %';
UPDATE patients SET full_name = 'Robert Johnson' WHERE full_name LIKE 'Robert %';

UPDATE medics SET full_name = 'Dr. Sarah Wilson' WHERE full_name LIKE 'Dr. Sarah %' OR full_name LIKE '% Wilson';
UPDATE medics SET full_name = 'Dr. Michael Brown' WHERE full_name LIKE 'Dr. Michael %' OR full_name LIKE '% Brown';
UPDATE medics SET full_name = 'Dr. Emily Davis' WHERE full_name LIKE 'Dr. Emily %' OR full_name LIKE '% Davis';
UPDATE medics SET full_name = 'Dr. James Miller' WHERE full_name LIKE 'Dr. James %' OR full_name LIKE '% Miller';

-- Add NOT NULL constraints for essential fields
ALTER TABLE patients ALTER COLUMN full_name SET NOT NULL;
ALTER TABLE patients ALTER COLUMN date_of_birth SET NOT NULL;
ALTER TABLE medics ALTER COLUMN full_name SET NOT NULL;
ALTER TABLE medics ALTER COLUMN specialty SET NOT NULL;
ALTER TABLE exams ALTER COLUMN name SET NOT NULL;
ALTER TABLE exams ALTER COLUMN category SET NOT NULL;

COMMENT ON TABLE patients IS 'Simplified patients table for PoC - contains only essential information';
COMMENT ON TABLE medics IS 'Simplified medics table for PoC - contains only essential information';
COMMENT ON TABLE exams IS 'Simplified exams table for PoC - contains only essential information';
COMMENT ON TABLE reservations IS 'Simplified reservations table for PoC - contains only essential information';

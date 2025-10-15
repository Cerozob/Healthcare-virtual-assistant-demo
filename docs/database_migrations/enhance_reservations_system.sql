-- Migration: Enhance reservations system for automated scheduling
-- Date: 2025-01-14
-- Description: Adds additional fields and views for automated scheduling workflows

-- Ensure the columns exist (some may have been added in previous migrations)
DO $$ 
BEGIN
    -- Add scheduling_agent_metadata if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'reservations' AND column_name = 'scheduling_agent_metadata'
    ) THEN
        ALTER TABLE reservations ADD COLUMN scheduling_agent_metadata JSONB DEFAULT '{}';
    END IF;
    
    -- Add auto_scheduled if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'reservations' AND column_name = 'auto_scheduled'
    ) THEN
        ALTER TABLE reservations ADD COLUMN auto_scheduled BOOLEAN DEFAULT false;
    END IF;
    
    -- Add protocol_id if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'reservations' AND column_name = 'protocol_id'
    ) THEN
        ALTER TABLE reservations ADD COLUMN protocol_id UUID REFERENCES medical_protocols(protocol_id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create indexes for performance if they don't exist
CREATE INDEX IF NOT EXISTS idx_reservations_protocol ON reservations(protocol_id);
CREATE INDEX IF NOT EXISTS idx_reservations_auto_scheduled ON reservations(auto_scheduled);
CREATE INDEX IF NOT EXISTS idx_reservations_start_time ON reservations(start_time);
CREATE INDEX IF NOT EXISTS idx_reservations_medic_status ON reservations(medic_id, status);

-- Create view for scheduling conflicts detection
CREATE OR REPLACE VIEW scheduling_conflicts AS
SELECT 
    r1.reservation_id as reservation_1,
    r2.reservation_id as reservation_2,
    r1.medic_id,
    r1.start_time as start_1,
    r1.end_time as end_1,
    r2.start_time as start_2,
    r2.end_time as end_2,
    m.first_name || ' ' || m.last_name as medic_name
FROM reservations r1
JOIN reservations r2 ON r1.medic_id = r2.medic_id 
    AND r1.reservation_id < r2.reservation_id
    AND r1.status IN ('scheduled', 'confirmed')
    AND r2.status IN ('scheduled', 'confirmed')
    AND (
        (r1.start_time <= r2.start_time AND r1.end_time > r2.start_time)
        OR (r1.start_time < r2.end_time AND r1.end_time >= r2.end_time)
        OR (r1.start_time >= r2.start_time AND r1.end_time <= r2.end_time)
    )
JOIN medics m ON r1.medic_id = m.medic_id;

-- Create view for auto-scheduled reservations with protocol details
CREATE OR REPLACE VIEW auto_scheduled_reservations AS
SELECT 
    r.reservation_id,
    r.patient_id,
    p.first_name || ' ' || p.last_name as patient_name,
    r.medic_id,
    m.first_name || ' ' || m.last_name as medic_name,
    m.specialty,
    r.exam_id,
    e.name as exam_name,
    e.category as exam_category,
    r.start_time,
    r.end_time,
    r.status,
    r.protocol_id,
    mp.name as protocol_name,
    mp.priority_level as protocol_priority,
    r.scheduling_agent_metadata,
    r.notes,
    r.created_at,
    r.updated_at
FROM reservations r
JOIN patients p ON r.patient_id = p.patient_id
JOIN medics m ON r.medic_id = m.medic_id
JOIN exams e ON r.exam_id = e.exam_id
LEFT JOIN medical_protocols mp ON r.protocol_id = mp.protocol_id
WHERE r.auto_scheduled = true
ORDER BY r.start_time DESC;

-- Create view for medic schedule with availability gaps
CREATE OR REPLACE VIEW medic_schedule_summary AS
SELECT 
    m.medic_id,
    m.first_name || ' ' || m.last_name as medic_name,
    m.specialty,
    m.is_active,
    COUNT(r.reservation_id) FILTER (WHERE r.start_time >= CURRENT_TIMESTAMP) as upcoming_appointments,
    COUNT(r.reservation_id) FILTER (WHERE r.start_time >= CURRENT_TIMESTAMP AND r.auto_scheduled = true) as auto_scheduled_count,
    MIN(r.start_time) FILTER (WHERE r.start_time >= CURRENT_TIMESTAMP) as next_appointment,
    MAX(r.start_time) FILTER (WHERE r.start_time >= CURRENT_TIMESTAMP) as last_scheduled_appointment,
    json_agg(
        json_build_object(
            'reservation_id', r.reservation_id,
            'start_time', r.start_time,
            'end_time', r.end_time,
            'exam_name', e.name,
            'patient_name', p.first_name || ' ' || p.last_name,
            'auto_scheduled', r.auto_scheduled
        ) ORDER BY r.start_time
    ) FILTER (WHERE r.start_time >= CURRENT_TIMESTAMP AND r.start_time < CURRENT_TIMESTAMP + INTERVAL '7 days') as next_week_schedule
FROM medics m
LEFT JOIN reservations r ON m.medic_id = r.medic_id 
    AND r.status IN ('scheduled', 'confirmed')
LEFT JOIN exams e ON r.exam_id = e.exam_id
LEFT JOIN patients p ON r.patient_id = p.patient_id
WHERE m.is_active = true
GROUP BY m.medic_id, m.first_name, m.last_name, m.specialty, m.is_active;

-- Create view for protocol-based scheduling recommendations
CREATE OR REPLACE VIEW protocol_scheduling_recommendations AS
SELECT 
    mp.protocol_id,
    mp.name as protocol_name,
    mp.description,
    mp.priority_level,
    mp.symptoms,
    mp.recommended_exams,
    json_agg(
        DISTINCT json_build_object(
            'exam_id', e.exam_id,
            'exam_name', e.name,
            'category', e.category,
            'duration_minutes', e.duration_minutes,
            'qualified_medics_count', (
                SELECT COUNT(DISTINCT em2.medic_id)
                FROM exam_medics em2
                JOIN medics m2 ON em2.medic_id = m2.medic_id
                WHERE em2.exam_id = e.exam_id AND m2.is_active = true
            )
        )
    ) as exam_details
FROM medical_protocols mp
CROSS JOIN LATERAL jsonb_array_elements_text(mp.recommended_exams) as recommended_exam
JOIN exams e ON e.name = recommended_exam AND e.is_active = true
WHERE mp.is_active = true
GROUP BY mp.protocol_id, mp.name, mp.description, mp.priority_level, mp.symptoms, mp.recommended_exams;

-- Create function to get available time slots for a medic
CREATE OR REPLACE FUNCTION get_available_slots(
    p_medic_id UUID,
    p_date DATE,
    p_duration_minutes INTEGER DEFAULT 30
)
RETURNS TABLE (
    slot_start TIMESTAMP WITH TIME ZONE,
    slot_end TIMESTAMP WITH TIME ZONE,
    is_available BOOLEAN
) AS $
DECLARE
    v_hour INTEGER;
    v_slot_start TIMESTAMP WITH TIME ZONE;
    v_slot_end TIMESTAMP WITH TIME ZONE;
    v_conflict_count INTEGER;
BEGIN
    -- Check business hours: 8 AM to 6 PM
    FOR v_hour IN 8..17 LOOP
        v_slot_start := p_date + (v_hour || ' hours')::INTERVAL;
        v_slot_end := v_slot_start + (p_duration_minutes || ' minutes')::INTERVAL;
        
        -- Check for conflicts
        SELECT COUNT(*) INTO v_conflict_count
        FROM reservations
        WHERE medic_id = p_medic_id
        AND status IN ('scheduled', 'confirmed')
        AND (
            (start_time <= v_slot_start AND end_time > v_slot_start)
            OR (start_time < v_slot_end AND end_time >= v_slot_end)
            OR (start_time >= v_slot_start AND end_time <= v_slot_end)
        );
        
        slot_start := v_slot_start;
        slot_end := v_slot_end;
        is_available := (v_conflict_count = 0);
        
        RETURN NEXT;
    END LOOP;
END;
$ LANGUAGE plpgsql;

-- Create function to auto-schedule based on protocol
CREATE OR REPLACE FUNCTION auto_schedule_from_protocol(
    p_patient_id UUID,
    p_protocol_id UUID,
    p_preferred_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    reservation_id UUID,
    exam_id UUID,
    exam_name VARCHAR,
    medic_id UUID,
    medic_name VARCHAR,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    success BOOLEAN,
    message TEXT
) AS $
DECLARE
    v_exam_name TEXT;
    v_exam_id UUID;
    v_duration INTEGER;
    v_medic_id UUID;
    v_medic_name TEXT;
    v_start_time TIMESTAMP WITH TIME ZONE;
    v_end_time TIMESTAMP WITH TIME ZONE;
    v_new_reservation_id UUID;
    v_preferred_date TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Set preferred date to tomorrow if not provided
    v_preferred_date := COALESCE(p_preferred_date, CURRENT_TIMESTAMP + INTERVAL '1 day');
    
    -- Get recommended exams from protocol
    FOR v_exam_name IN 
        SELECT jsonb_array_elements_text(recommended_exams)
        FROM medical_protocols
        WHERE protocol_id = p_protocol_id
    LOOP
        -- Get exam details
        SELECT e.exam_id, e.duration_minutes
        INTO v_exam_id, v_duration
        FROM exams e
        WHERE e.name = v_exam_name AND e.is_active = true
        LIMIT 1;
        
        IF v_exam_id IS NULL THEN
            reservation_id := NULL;
            exam_id := NULL;
            exam_name := v_exam_name;
            medic_id := NULL;
            medic_name := NULL;
            start_time := NULL;
            end_time := NULL;
            success := false;
            message := 'Exam not found or inactive';
            RETURN NEXT;
            CONTINUE;
        END IF;
        
        -- Find available medic
        SELECT m.medic_id, m.first_name || ' ' || m.last_name
        INTO v_medic_id, v_medic_name
        FROM medics m
        JOIN exam_medics em ON m.medic_id = em.medic_id
        WHERE em.exam_id = v_exam_id
        AND m.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM reservations r
            WHERE r.medic_id = m.medic_id
            AND r.status IN ('scheduled', 'confirmed')
            AND (
                (r.start_time <= v_preferred_date AND r.end_time > v_preferred_date)
                OR (r.start_time < v_preferred_date + (v_duration || ' minutes')::INTERVAL 
                    AND r.end_time >= v_preferred_date + (v_duration || ' minutes')::INTERVAL)
            )
        )
        LIMIT 1;
        
        IF v_medic_id IS NULL THEN
            reservation_id := NULL;
            exam_id := v_exam_id;
            exam_name := v_exam_name;
            medic_id := NULL;
            medic_name := NULL;
            start_time := NULL;
            end_time := NULL;
            success := false;
            message := 'No available qualified medic found';
            RETURN NEXT;
            CONTINUE;
        END IF;
        
        -- Create reservation
        v_start_time := v_preferred_date;
        v_end_time := v_preferred_date + (v_duration || ' minutes')::INTERVAL;
        
        INSERT INTO reservations (
            patient_id, medic_id, exam_id, start_time, end_time,
            status, auto_scheduled, protocol_id, notes,
            scheduling_agent_metadata
        ) VALUES (
            p_patient_id, v_medic_id, v_exam_id, v_start_time, v_end_time,
            'scheduled', true, p_protocol_id, 'Auto-scheduled by protocol',
            json_build_object(
                'scheduled_by', 'auto_schedule_function',
                'scheduled_at', CURRENT_TIMESTAMP,
                'protocol_based', true
            )::jsonb
        )
        RETURNING reservations.reservation_id INTO v_new_reservation_id;
        
        reservation_id := v_new_reservation_id;
        exam_id := v_exam_id;
        exam_name := v_exam_name;
        medic_id := v_medic_id;
        medic_name := v_medic_name;
        start_time := v_start_time;
        end_time := v_end_time;
        success := true;
        message := 'Successfully scheduled';
        
        RETURN NEXT;
        
        -- Move to next time slot
        v_preferred_date := v_end_time + INTERVAL '15 minutes';
    END LOOP;
END;
$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON VIEW scheduling_conflicts IS 'Identifies scheduling conflicts where medics have overlapping appointments';
COMMENT ON VIEW auto_scheduled_reservations IS 'Shows all reservations that were automatically scheduled by the AI agent';
COMMENT ON VIEW medic_schedule_summary IS 'Provides summary of medic schedules with upcoming appointments';
COMMENT ON VIEW protocol_scheduling_recommendations IS 'Shows exam recommendations from protocols with qualified medic counts';
COMMENT ON FUNCTION get_available_slots IS 'Returns available time slots for a medic on a given date';
COMMENT ON FUNCTION auto_schedule_from_protocol IS 'Automatically schedules exams based on a medical protocol';

-- Sample usage examples in comments
COMMENT ON COLUMN reservations.scheduling_agent_metadata IS 'JSONB metadata from AI scheduling agent. Example: {"scheduled_by": "scheduling_agent", "scheduled_at": "2024-01-15T10:00:00Z", "protocol_based": true, "confidence_score": 0.95}';
COMMENT ON COLUMN reservations.auto_scheduled IS 'Flag indicating if reservation was automatically scheduled by AI agent based on symptom analysis';


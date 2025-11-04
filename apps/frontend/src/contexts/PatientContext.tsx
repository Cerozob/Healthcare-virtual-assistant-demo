/**
 * Patient Context
 * Provides patient data and state management across the application
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import type { Patient, Reservation } from '../types/api';

interface PatientContextValue {
  selectedPatient: Patient | null;
  patientExams: Reservation[];
  setSelectedPatient: (patient: Patient | null) => void;
  setPatientExams: (exams: Reservation[]) => void;
  clearPatient: () => void;
  isPatientSelected: boolean;
  // Enhanced patient context sync capabilities
  syncPatientFromResponse: (patientContext: {
    patientId?: string;
    patientName?: string;
    contextChanged?: boolean;
    identificationSource?: string;
  }) => Promise<{
    patientUpdated: boolean;
    requiresNewSession: boolean;
    patient?: Patient;
  }>;
  lastSyncedPatientId: string | null;
}

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

interface PatientProviderProps {
  children: ReactNode;
}

export const PatientProvider: React.FC<PatientProviderProps> = ({ children }) => {
  const [selectedPatient, setSelectedPatientState] = useState<Patient | null>(null);
  const [patientExams, setPatientExamsState] = useState<Reservation[]>([]);
  const [lastSyncedPatientId, setLastSyncedPatientId] = useState<string | null>(null);

  const setSelectedPatient = useCallback((patient: Patient | null) => {
    setSelectedPatientState(patient);
    setLastSyncedPatientId(patient?.patient_id || null);
  }, []);

  const setPatientExams = useCallback((exams: Reservation[]) => {
    setPatientExamsState(exams);
  }, []);

  const clearPatient = useCallback(() => {
    setSelectedPatientState(null);
    setPatientExamsState([]);
    setLastSyncedPatientId(null);
  }, []);

  const syncPatientFromResponse = useCallback(async (patientContext: {
    patientId?: string;
    patientName?: string;
    contextChanged?: boolean;
    identificationSource?: string;
  }) => {
    console.log('🔄 Syncing patient from response:', patientContext);
    
    const { patientId, patientName } = patientContext;
    
    // If no patient detected, no sync needed
    if (!patientId || !patientName) {
      console.log('ℹ️ No patient context in response, no sync needed');
      return { patientUpdated: false, requiresNewSession: false };
    }

    const currentPatientId = selectedPatient?.patient_id;
    
    // Check if this is a different patient (security concern)
    const isDifferentPatient = currentPatientId && currentPatientId !== patientId;
    
    if (isDifferentPatient) {
      console.warn('⚠️ Different patient detected in response!');
      console.warn(`  Current: ${currentPatientId} (${selectedPatient?.full_name})`);
      console.warn(`  Detected: ${patientId} (${patientName})`);
      
      return {
        patientUpdated: false,
        requiresNewSession: true,
        patient: undefined
      };
    }
    
    // If same patient, no update needed
    if (currentPatientId === patientId) {
      console.log('✅ Same patient confirmed, no update needed');
      setLastSyncedPatientId(patientId);
      return { patientUpdated: false, requiresNewSession: false, patient: selectedPatient || undefined };
    }
    
    // No current patient - fetch and set the detected patient
    if (!currentPatientId) {
      try {
        console.log(`🔍 Fetching patient data for auto-detected patient: ${patientId}`);
        
        // Import patient service dynamically to avoid circular dependencies
        const { patientService } = await import('../services/patientService');
        const patientResponse = await patientService.getPatient(patientId);
        const fetchedPatient = patientResponse.patient;
        
        console.log('✅ Successfully fetched patient data:', fetchedPatient);
        
        // Update patient context
        setSelectedPatientState(fetchedPatient);
        setLastSyncedPatientId(patientId);
        
        // Load patient exams if available
        try {
          const { reservationService } = await import('../services/reservationService');
          const reservationsResponse = await reservationService.getReservations();
          const patientReservations = reservationsResponse.reservations.filter(
            reservation => reservation.patient_id === patientId
          );
          setPatientExamsState(patientReservations);
          console.log(`📅 Loaded ${patientReservations.length} reservations for patient`);
        } catch (examError) {
          console.warn('⚠️ Failed to load patient exams:', examError);
          setPatientExamsState([]);
        }
        
        return {
          patientUpdated: true,
          requiresNewSession: false,
          patient: fetchedPatient || undefined
        };
        
      } catch (fetchError) {
        console.error('❌ Failed to fetch patient data:', fetchError);
        
        // Create minimal patient object with available data
        const fallbackPatient: Patient = {
          patient_id: patientId,
          full_name: patientName,
          date_of_birth: '1900-01-01', // Fallback date
          cedula: '',
          email: '',
          phone: '',
          gender: '',
          document_type: 'cedula',
          document_number: '',
          address: {
            street: '',
            city: '',
            province: '',
            country: '',
            postal_code: ''
          },
          medical_history: {
            conditions: [],
            procedures: [],
            medications: []
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        setSelectedPatientState(fallbackPatient);
        setLastSyncedPatientId(patientId);
        setPatientExamsState([]);
        
        return {
          patientUpdated: true,
          requiresNewSession: false,
          patient: fallbackPatient
        };
      }
    }
    
    return { patientUpdated: false, requiresNewSession: false };
  }, [selectedPatient]);

  const value: PatientContextValue = {
    selectedPatient,
    patientExams,
    setSelectedPatient,
    setPatientExams,
    clearPatient,
    isPatientSelected: selectedPatient !== null,
    syncPatientFromResponse,
    lastSyncedPatientId
  };

  return (
    <PatientContext.Provider value={value}>
      {children}
    </PatientContext.Provider>
  );
};

export const usePatientContext = (): PatientContextValue => {
  const context = useContext(PatientContext);
  if (context === undefined) {
    throw new Error('usePatientContext must be used within a PatientProvider');
  }
  return context;
};

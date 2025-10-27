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
}

const PatientContext = createContext<PatientContextValue | undefined>(undefined);

interface PatientProviderProps {
  children: ReactNode;
}

export const PatientProvider: React.FC<PatientProviderProps> = ({ children }) => {
  const [selectedPatient, setSelectedPatientState] = useState<Patient | null>(null);
  const [patientExams, setPatientExamsState] = useState<Reservation[]>([]);

  const setSelectedPatient = useCallback((patient: Patient | null) => {
    setSelectedPatientState(patient);
  }, []);

  const setPatientExams = useCallback((exams: Reservation[]) => {
    setPatientExamsState(exams);
  }, []);

  const clearPatient = useCallback(() => {
    setSelectedPatientState(null);
    setPatientExamsState([]);
  }, []);

  const value: PatientContextValue = {
    selectedPatient,
    patientExams,
    setSelectedPatient,
    setPatientExams,
    clearPatient,
    isPatientSelected: selectedPatient !== null
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

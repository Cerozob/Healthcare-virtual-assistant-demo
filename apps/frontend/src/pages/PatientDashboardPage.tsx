/**
 * Patient Dashboard Page
 * Main page for viewing and managing patient information
 */

import { useState } from 'react';
import {
  Header,
  SpaceBetween,
  Alert
} from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import { PatientSelector, PatientInfo, ScheduledExams } from '../components/patient';
import { usePatientContext } from '../contexts/PatientContext';
import { usePatientWithExams } from '../hooks/usePatients';
import { Patient } from '../types/api';
import { es } from '../i18n/es';

interface PatientDashboardPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

export const PatientDashboardPage: React.FC<PatientDashboardPageProps> = ({ signOut, user }) => {
  const { selectedPatient, patientExams, setSelectedPatient, setPatientExams } = usePatientContext();
  const { execute: fetchPatientWithExams, loading, error } = usePatientWithExams();
  const [localError, setLocalError] = useState<string | null>(null);

  const handlePatientSelect = async (patient: Patient | null) => {
    setLocalError(null);
    
    if (!patient) {
      setSelectedPatient(null);
      setPatientExams([]);
      return;
    }

    try {
      // Fetch patient with exams
      const result = await fetchPatientWithExams(patient.patient_id);
      
      if (result) {
        setSelectedPatient(result.patient);
        setPatientExams(result.exams || []);
      }
    } catch (err) {
      console.error('Error fetching patient data:', err);
      setLocalError('Error al cargar los datos del paciente. Por favor, intente nuevamente.');
      setSelectedPatient(patient); // Still set the basic patient info
      setPatientExams([]);
    }
  };

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">{es.nav.dashboard}</Header>

        {/* Patient Selector */}
        <PatientSelector
          onPatientSelect={handlePatientSelect}
          selectedPatient={selectedPatient}
        />

        {/* Error Alert */}
        {(error || localError) && (
          <Alert
            type="error"
            dismissible
            onDismiss={() => setLocalError(null)}
          >
            {localError || es.errors.generic}
          </Alert>
        )}

        {/* Patient Information */}
        {selectedPatient && (
          <>
            <PatientInfo patient={selectedPatient} />
            
            {/* Scheduled Exams */}
            <ScheduledExams
              exams={patientExams}
              loading={loading}
            />
          </>
        )}

        {/* No Patient Selected Message */}
        {!selectedPatient && !loading && (
          <Alert type="info">
            {es.patient.noPatientSelected}. {es.patient.selectPatient}.
          </Alert>
        )}
      </SpaceBetween>
    </MainLayout>
  );
};

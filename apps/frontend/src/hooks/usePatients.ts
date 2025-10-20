/**
 * usePatients Hook
 * React hooks for patient-related API operations
 */

import { useApi } from './useApi';
import { patientService } from '../services';
import {
  Patient,
  CreatePatientRequest,
  UpdatePatientRequest,
  PatientsResponse,
  PaginationParams
} from '../types/api';

export function usePatients() {
  return useApi<PatientsResponse>((params?: PaginationParams) => 
    patientService.getPatients(params)
  );
}

export function usePatient() {
  return useApi<{ patient: Patient }>((id: string) => 
    patientService.getPatient(id)
  );
}

export function usePatientWithExams() {
  return useApi<{ patient: Patient; exams: import('../types/api').Exam[] }>((id: string) => 
    patientService.getPatientWithExams(id)
  );
}

export function useSearchPatients() {
  return useApi<PatientsResponse>((query: string, params?: PaginationParams) => 
    patientService.searchPatients(query, params)
  );
}

export function useCreatePatient() {
  return useApi<{ message: string; patient: Patient }>((data: CreatePatientRequest) => 
    patientService.createPatient(data)
  );
}

export function useUpdatePatient() {
  return useApi<{ message: string; patient: Patient }>((id: string, data: UpdatePatientRequest) => 
    patientService.updatePatient(id, data)
  );
}

export function useDeletePatient() {
  return useApi<{ message: string; patient_id: string }>((id: string) => 
    patientService.deletePatient(id)
  );
}

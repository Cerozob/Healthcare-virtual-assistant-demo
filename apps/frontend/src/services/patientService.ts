/**
 * Patient Service
 * Service class for patient-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  Patient,
  CreatePatientRequest,
  UpdatePatientRequest,
  PatientsResponse,
  PaginationParams
} from '../types/api';

export class PatientService {
  /**
   * Get list of patients with pagination
   */
  async getPatients(params?: PaginationParams): Promise<PatientsResponse> {
    return apiClient.get<PatientsResponse>(API_ENDPOINTS.patients, params);
  }

  /**
   * Get patient by ID
   */
  async getPatient(id: string): Promise<{ patient: Patient }> {
    return apiClient.get<{ patient: Patient }>(API_ENDPOINTS.patient(id));
  }

  /**
   * Create new patient
   */
  async createPatient(data: CreatePatientRequest): Promise<{ message: string; patient: Patient }> {
    return apiClient.post<{ message: string; patient: Patient }>(API_ENDPOINTS.patients, data);
  }

  /**
   * Update existing patient
   */
  async updatePatient(id: string, data: UpdatePatientRequest): Promise<{ message: string; patient: Patient }> {
    return apiClient.put<{ message: string; patient: Patient }>(API_ENDPOINTS.patient(id), data);
  }

  /**
   * Delete patient
   */
  async deletePatient(id: string): Promise<{ message: string; patient_id: string }> {
    return apiClient.delete<{ message: string; patient_id: string }>(API_ENDPOINTS.patient(id));
  }
}

// Export singleton instance
export const patientService = new PatientService();

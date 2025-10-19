/**
 * Medic Service
 * Service class for medic-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  Medic,
  CreateMedicRequest,
  UpdateMedicRequest,
  MedicsResponse,
  PaginationParams
} from '../types/api';

export class MedicService {
  /**
   * Get list of medics with pagination
   */
  async getMedics(params?: PaginationParams): Promise<MedicsResponse> {
    return apiClient.get<MedicsResponse>(API_ENDPOINTS.medics, params);
  }

  /**
   * Get medic by ID
   */
  async getMedic(id: string): Promise<{ medic: Medic }> {
    return apiClient.get<{ medic: Medic }>(API_ENDPOINTS.medic(id));
  }

  /**
   * Create new medic
   */
  async createMedic(data: CreateMedicRequest): Promise<{ message: string; medic: Medic }> {
    return apiClient.post<{ message: string; medic: Medic }>(API_ENDPOINTS.medics, data);
  }

  /**
   * Update existing medic
   */
  async updateMedic(id: string, data: UpdateMedicRequest): Promise<{ message: string; medic: Medic }> {
    return apiClient.put<{ message: string; medic: Medic }>(API_ENDPOINTS.medic(id), data);
  }

  /**
   * Delete medic
   */
  async deleteMedic(id: string): Promise<{ message: string; medic_id: string }> {
    return apiClient.delete<{ message: string; medic_id: string }>(API_ENDPOINTS.medic(id));
  }
}

// Export singleton instance
export const medicService = new MedicService();

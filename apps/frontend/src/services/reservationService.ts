/**
 * Reservation Service
 * Service class for reservation-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  Reservation,
  CreateReservationRequest,
  UpdateReservationRequest,
  ReservationsResponse,
  PaginationParams
} from '../types/api';

export class ReservationService {
  /**
   * Get list of reservations with pagination
   */
  async getReservations(params?: PaginationParams): Promise<ReservationsResponse> {
    return apiClient.get<ReservationsResponse>(API_ENDPOINTS.reservations, params);
  }

  /**
   * Get reservation by ID
   */
  async getReservation(id: string): Promise<{ reservation: Reservation }> {
    return apiClient.get<{ reservation: Reservation }>(API_ENDPOINTS.reservation(id));
  }

  /**
   * Create new reservation
   */
  async createReservation(data: CreateReservationRequest): Promise<{ message: string; reservation: Reservation }> {
    return apiClient.post<{ message: string; reservation: Reservation }>(API_ENDPOINTS.reservations, data);
  }

  /**
   * Update existing reservation
   */
  async updateReservation(id: string, data: UpdateReservationRequest): Promise<{ message: string; reservation: Reservation }> {
    return apiClient.put<{ message: string; reservation: Reservation }>(API_ENDPOINTS.reservation(id), data);
  }

  /**
   * Delete reservation
   */
  async deleteReservation(id: string): Promise<{ message: string; reservation_id: string }> {
    return apiClient.delete<{ message: string; reservation_id: string }>(API_ENDPOINTS.reservation(id));
  }
}

// Export singleton instance
export const reservationService = new ReservationService();

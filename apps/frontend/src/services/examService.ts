/**
 * Exam Service
 * Service class for exam-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  Exam,
  CreateExamRequest,
  UpdateExamRequest,
  ExamsResponse,
  PaginationParams
} from '../types/api';

export class ExamService {
  /**
   * Get list of exams with pagination
   */
  async getExams(params?: PaginationParams): Promise<ExamsResponse> {
    return apiClient.get<ExamsResponse>(API_ENDPOINTS.exams, params);
  }

  /**
   * Get exam by ID
   */
  async getExam(id: string): Promise<{ exam: Exam }> {
    return apiClient.get<{ exam: Exam }>(API_ENDPOINTS.exam(id));
  }

  /**
   * Create new exam
   */
  async createExam(data: CreateExamRequest): Promise<{ message: string; exam: Exam }> {
    return apiClient.post<{ message: string; exam: Exam }>(API_ENDPOINTS.exams, data);
  }

  /**
   * Update existing exam
   */
  async updateExam(id: string, data: UpdateExamRequest): Promise<{ message: string; exam: Exam }> {
    return apiClient.put<{ message: string; exam: Exam }>(API_ENDPOINTS.exam(id), data);
  }

  /**
   * Delete exam
   */
  async deleteExam(id: string): Promise<{ message: string; exam_id: string }> {
    return apiClient.delete<{ message: string; exam_id: string }>(API_ENDPOINTS.exam(id));
  }
}

// Export singleton instance
export const examService = new ExamService();

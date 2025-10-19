/**
 * Document Service
 * Service class for document-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentStatus
} from '../types/api';

export class DocumentService {
  /**
   * Upload document
   */
  async uploadDocument(data: DocumentUploadRequest): Promise<DocumentUploadResponse> {
    const { file, ...additionalData } = data;
    return apiClient.upload<DocumentUploadResponse>(API_ENDPOINTS.documentUpload, file, additionalData);
  }

  /**
   * Get document processing status
   */
  async getDocumentStatus(documentId: string): Promise<DocumentStatus> {
    return apiClient.get<DocumentStatus>(API_ENDPOINTS.documentStatus(documentId));
  }
}

// Export singleton instance
export const documentService = new DocumentService();

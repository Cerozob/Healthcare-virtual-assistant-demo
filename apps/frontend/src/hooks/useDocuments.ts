/**
 * useDocuments Hook
 * React hooks for document-related API operations
 */

import { documentService } from '../services';
import type {
  DocumentStatus,
  DocumentUploadRequest,
  DocumentUploadResponse
} from '../types/api';
import { useApi } from './useApi';

export function useDocumentUpload() {
  return useApi<DocumentUploadResponse>((data: DocumentUploadRequest) =>
    documentService.uploadDocument(data)
  );
}

export function useDocumentStatus() {
  return useApi<DocumentStatus>((documentId: string) =>
    documentService.getDocumentStatus(documentId)
  );
}

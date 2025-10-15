import { uploadData, downloadData, remove } from 'aws-amplify/storage';
import { v4 as uuidv4 } from 'uuid';

// API endpoint for document metadata
const API_BASE_URL = process.env.VITE_API_URL || 'https://api.example.com';

export interface DocumentUploadOptions {
  patientId?: string;
  chatSessionId?: string;
  onProgress?: (progress: { transferredBytes: number; totalBytes?: number }) => void;
}

export interface DocumentMetadata {
  documentId: string;
  fileName: string;
  contentType: string;
  fileSize: number;
  s3Key: string;
  patientId?: string;
  chatSessionId?: string;
  uploadedAt: string;
  status: 'uploading' | 'uploaded' | 'processing' | 'processed' | 'error';
}

export class DocumentUploadService {
  /**
   * Upload a document using Amplify Storage
   */
  async uploadDocument(
    file: File,
    options: DocumentUploadOptions = {}
  ): Promise<DocumentMetadata> {
    try {
      const documentId = uuidv4();
      const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
      
      // Create organized path structure
      let path: string;
      if (options.patientId) {
        path = `patients/${options.patientId}/${timestamp}/${documentId}/${file.name}`;
      } else if (options.chatSessionId) {
        path = `chat-sessions/${options.chatSessionId}/${timestamp}/${documentId}/${file.name}`;
      } else {
        path = `temp-uploads/${timestamp}/${documentId}/${file.name}`;
      }

      // Upload file to S3 using Amplify Storage
      const uploadResult = await uploadData({
        path,
        data: file,
        options: {
          contentType: file.type,
          metadata: {
            documentId,
            originalFileName: file.name,
            patientId: options.patientId || '',
            chatSessionId: options.chatSessionId || '',
            uploadTimestamp: new Date().toISOString(),
          },
          onProgress: options.onProgress,
        },
      }).result;

      console.log('File uploaded successfully:', uploadResult);

      // Create document metadata
      const metadata: DocumentMetadata = {
        documentId,
        fileName: file.name,
        contentType: file.type,
        fileSize: file.size,
        s3Key: path,
        patientId: options.patientId,
        chatSessionId: options.chatSessionId,
        uploadedAt: new Date().toISOString(),
        status: 'uploaded',
      };

      // Send metadata to backend for processing
      await this.notifyBackendOfUpload(metadata);

      return metadata;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw new Error(`Failed to upload document: ${(error as Error).message}`);
    }
  }

  /**
   * Upload multiple documents
   */
  async uploadMultipleDocuments(
    files: File[],
    options: DocumentUploadOptions = {}
  ): Promise<DocumentMetadata[]> {
    const uploadPromises = files.map(file => this.uploadDocument(file, options));
    return Promise.all(uploadPromises);
  }

  /**
   * Get document download URL
   */
  async getDocumentUrl(s3Key: string): Promise<string> {
    try {
      const result = await downloadData({
        path: s3Key,
      }).result;

      // Create blob URL for download
      const blob = await result.body.blob();
      return URL.createObjectURL(blob);
    } catch (error) {
      console.error('Error getting document URL:', error);
      throw new Error(`Failed to get document URL: ${(error as Error).message}`);
    }
  }

  /**
   * Delete document from storage
   */
  async deleteDocument(s3Key: string): Promise<void> {
    try {
      await remove({
        path: s3Key,
      });
      console.log('Document deleted successfully:', s3Key);
    } catch (error) {
      console.error('Error deleting document:', error);
      throw new Error(`Failed to delete document: ${(error as Error).message}`);
    }
  }

  /**
   * Get document processing status
   */
  async getDocumentStatus(documentId: string): Promise<{
    status: string;
    progress?: number;
    error?: string;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/status/${documentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add authentication headers
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get document status: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        status: data.document?.status || 'unknown',
        error: data.document?.error_message,
      };
    } catch (error) {
      console.error('Error getting document status:', error);
      throw new Error(`Failed to get document status: ${(error as Error).message}`);
    }
  }

  /**
   * Notify backend of successful upload for processing
   */
  private async notifyBackendOfUpload(metadata: DocumentMetadata): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // TODO: Add authentication headers
        },
        body: JSON.stringify(metadata),
      });

      if (!response.ok) {
        throw new Error(`Failed to notify backend: ${response.statusText}`);
      }

      console.log('Backend notified of upload:', metadata.documentId);
    } catch (error) {
      console.error('Error notifying backend:', error);
      // Don't fail the upload if backend notification fails
      // The file is already uploaded to S3
    }
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/tiff',
      'audio/mpeg',
      'audio/wav',
      'video/mp4',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
    ];

    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size exceeds maximum allowed size of ${maxSize / (1024 * 1024)}MB`,
      };
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type ${file.type} is not supported`,
      };
    }

    return { valid: true };
  }
}

export const documentUploadService = new DocumentUploadService();

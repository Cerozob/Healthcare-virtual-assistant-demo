/**
 * Processed File Service
 * Handles operations for processed files from the document workflow
 * Enhanced to support unified file loading and preview functionality
 */

import { configService } from './configService';
import { storageService } from './storageService';
import { FileTypeDetector } from '../utils/fileTypeDetector';
import type { ProcessedFile } from '../components/config/ProcessedFileManager';
import type { PatientFile } from '../components/config/FileManager';
import type {
  UnifiedFile,
  PreviewCapabilities,
  FileContent,
  UnifiedFileLoadOptions,
  FileOperationResult,
} from '../types/unifiedFile';
import { FileError } from '../types/unifiedFile';
import { ErrorHandler } from '../utils/errorHandler';

class ProcessedFileService {

  /**
   * Load unified files from both raw and processed buckets
   */
  async getUnifiedFiles(options: UnifiedFileLoadOptions = {}): Promise<UnifiedFile[]> {
    const {
      patientId,
      includeRaw = true,
      includeProcessed = true,
      maxFiles = 1000,
    } = options;

    try {
      console.log(`Loading unified files${patientId ? ` for patient: ${patientId}` : ' (all patients)'}`);
      console.log(`Options:`, { includeRaw, includeProcessed, maxFiles });

      const unifiedFiles: UnifiedFile[] = [];

      // Load raw files if requested
      if (includeRaw) {
        const rawFiles = await this.loadRawFilesAsUnified(patientId);
        unifiedFiles.push(...rawFiles);
      }

      // Load processed files if requested
      if (includeProcessed) {
        const processedFiles = await this.loadProcessedFilesAsUnified(patientId);
        unifiedFiles.push(...processedFiles);
      }

      // Sort by date (newest first) and limit results
      unifiedFiles.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      const limitedFiles = unifiedFiles.slice(0, maxFiles);

      console.log(`Loaded ${limitedFiles.length} unified files (${unifiedFiles.length} total before limit)`);
      return limitedFiles;

    } catch (error) {
      console.error('Failed to load unified files:', error);
      throw error;
    }
  }

  /**
   * Load raw files and convert to unified format
   */
  private async loadRawFilesAsUnified(patientId?: string): Promise<UnifiedFile[]> {
    try {
      const config = configService.getConfig();
      const prefix = patientId ? `${patientId}/` : '';

      const s3Files = await storageService.listFiles(prefix, {
        includeMetadata: true,
        bucket: config.s3BucketName, // Raw bucket
        pageSize: 1000,
      });

      const unifiedFiles: UnifiedFile[] = [];

      for (const s3File of s3Files) {
        // Skip directories and invalid files
        if (!s3File.key || s3File.key.endsWith('/')) continue;

        // Extract patient ID from key structure
        const keyParts = s3File.key.split('/');
        const extractedPatientId = keyParts.length > 1 ? keyParts[0] : patientId || 'unknown';
        const fileName = keyParts[keyParts.length - 1];

        // Get file extension and type
        const fileExtension = fileName.split('.').pop()?.toUpperCase() || 'UNKNOWN';

        // Extract metadata
        const metadata = s3File.metadata || {};
        const category = metadata['document-category'] || metadata['category'];
        const confidence = parseFloat(metadata['classification-confidence'] || '0');
        const autoClassified = metadata['auto-classified'] === 'true';
        const originalClassification = metadata['original-classification'];
        const uploadDate = metadata['upload-timestamp'] || s3File.lastModified?.toISOString() || new Date().toISOString();

        // Determine preview capabilities
        const preview = this.getPreviewCapabilities(fileName, s3File.size || 0);

        const unifiedFile: UnifiedFile = {
          id: s3File.key,
          name: fileName,
          type: fileExtension,
          size: s3File.size || 0,
          date: uploadDate,
          url: s3File.key,
          bucket: config.s3BucketName,
          metadata,
          source: 'raw',
          patientId: extractedPatientId,
          rawProperties: {
            uploadDate,
            category,
            autoClassified,
            classificationConfidence: confidence > 0 ? confidence : undefined,
            originalClassification,
          },
          preview,
        };

        unifiedFiles.push(unifiedFile);
      }

      console.log(`Loaded ${unifiedFiles.length} raw files as unified`);
      return unifiedFiles;

    } catch (error) {
      console.error('Failed to load raw files as unified:', error);
      throw error;
    }
  }

  /**
   * Load processed files and convert to unified format
   */
  private async loadProcessedFilesAsUnified(patientId?: string): Promise<UnifiedFile[]> {
    try {
      const config = configService.getConfig();
      const prefix = patientId ? `${patientId}/` : '';

      const s3Files = await storageService.listFiles(prefix, {
        includeMetadata: true,
        bucket: config.processedBucketName,
        pageSize: 1000,
      });

      const unifiedFiles: UnifiedFile[] = [];

      for (const s3File of s3Files) {
        // Skip directories and invalid files
        if (!s3File.key || s3File.key.endsWith('/')) continue;

        // Extract patient ID and document ID from key structure
        const keyParts = s3File.key.split('/');
        if (keyParts.length < 3) continue; // Skip malformed keys

        const extractedPatientId = keyParts[0];
        const documentIdentifier = keyParts[1];
        const fileName = keyParts[keyParts.length - 1];

        // Get file extension and type
        const fileExtension = fileName.split('.').pop()?.toUpperCase() || 'UNKNOWN';

        // Extract metadata
        const metadata = s3File.metadata || {};
        const category = metadata['document-category'] || 'other';
        const confidence = parseFloat(metadata['classification-confidence'] || '0');
        const autoClassified = metadata['auto-classified'] === 'true';
        const originalClassification = metadata['original-classification'];
        const processedDate = metadata['processing-timestamp'] ||
          metadata['classification-timestamp'] ||
          s3File.lastModified?.toISOString() || new Date().toISOString();

        // Determine preview capabilities
        const preview = this.getPreviewCapabilities(fileName, s3File.size || 0);

        // Don't load extracted data during listing - only load at preview time
        let extractedData: Record<string, unknown> | undefined;
        let bdaMetadata: Record<string, unknown> | undefined;

        const unifiedFile: UnifiedFile = {
          id: s3File.key,
          name: fileName,
          type: fileExtension,
          size: s3File.size || 0,
          date: processedDate,
          url: s3File.key,
          bucket: config.processedBucketName,
          metadata,
          source: 'processed',
          patientId: extractedPatientId,
          processedProperties: {
            processedDate,
            category,
            confidence: confidence > 0 ? confidence : undefined,
            originalClassification,
            autoClassified,
            documentId: documentIdentifier,
            extractedData,
            bdaMetadata,
          },
          preview,
        };

        unifiedFiles.push(unifiedFile);
      }

      console.log(`Loaded ${unifiedFiles.length} processed files as unified`);
      return unifiedFiles;

    } catch (error) {
      console.error('Failed to load processed files as unified:', error);
      throw error;
    }
  }

  /**
   * Determine preview capabilities for a file
   */
  private getPreviewCapabilities(fileName: string, fileSize: number): PreviewCapabilities {
    const validation = FileTypeDetector.validateFileForPreview(fileName, fileSize);
    const fileTypeInfo = FileTypeDetector.getFileTypeInfo(fileName);

    return {
      previewSupported: validation.supported,
      previewConfig: validation.config,
      contentType: fileTypeInfo?.mimeType,
      canLoadContent: validation.supported,
    };
  }

  /**
   * Get file content for preview (simplified - no caching)
   */
  async getFileContent(file: UnifiedFile): Promise<FileOperationResult<FileContent>> {
    try {
      // Check if preview is supported
      if (!file.preview.previewSupported) {
        return {
          success: false,
          error: {
            type: FileError.UNSUPPORTED_TYPE,
            message: `File type ${file.type} is not supported for preview`,
          },
        };
      }

      console.log(`Loading content for ${file.name} from ${file.source} bucket`);

      // Load file content directly
      const blob = await storageService.downloadFile(file.url, { bucket: file.bucket });

      // Determine content type
      const contentType = file.preview.contentType || blob.type || 'application/octet-stream';

      // Convert blob to appropriate format based on file type
      let content: string | Blob;
      
      if (file.preview.previewConfig?.component === 'container') {
        // For images and PDFs, keep as blob
        content = blob;
      } else {
        // For text-based files, convert to string
        let textContent = await blob.text();
        
        // Special handling for extracted_data.json files - clean up processing metadata
        if (file.name === 'extracted_data.json' && file.source === 'processed') {
          try {
            const jsonData = JSON.parse(textContent);
            // Remove processing metadata for cleaner display
            const cleanData = { ...jsonData };
            delete cleanData.processing_metadata;
            textContent = JSON.stringify(cleanData, null, 2);
          } catch {
            // If JSON parsing fails, use original content
          }
        }
        
        content = textContent;
      }

      const fileContent: FileContent = {
        content,
        contentType,
        size: blob.size,
        lastModified: new Date().toISOString(),
      };

      console.log(`Successfully loaded content for ${file.name} (${blob.size} bytes)`);

      return {
        success: true,
        data: fileContent,
      };

    } catch (error) {
      console.error(`Failed to load content for ${file.name}:`, error);

      // Use enhanced error handler
      const errorDetails = ErrorHandler.getErrorDetails(error, `Carga de contenido de ${file.name}`);
      
      // Map to appropriate FileError types
      let errorType = FileError.NETWORK_ERROR;
      
      if (error instanceof Error) {
        const errorMessage = error.message.toLowerCase();
        if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
          errorType = FileError.TIMEOUT;
        } else if (errorMessage.includes('nosuchkey') || errorMessage.includes('notfound') || errorMessage.includes('not found')) {
          errorType = FileError.NOT_FOUND;
        } else if (errorMessage.includes('accessdenied') || errorMessage.includes('forbidden') || errorMessage.includes('access denied')) {
          errorType = FileError.ACCESS_DENIED;
        } else if (errorMessage.includes('abort')) {
          // Request was cancelled, treat as network error but don't retry
          errorType = FileError.NETWORK_ERROR;
        }
      }

      return {
        success: false,
        error: {
          type: errorType,
          message: errorDetails.userMessage,
          details: { 
            originalError: error instanceof Error ? error.message : String(error),
            technicalDetails: errorDetails.technicalDetails,
          },
        },
      };
    }
  }



  /**
   * Get processed files from the processed bucket (legacy method)
   */
  async getProcessedFiles(patientId?: string): Promise<ProcessedFile[]> {
    try {
      const config = configService.getConfig();
      console.log(`Using processed bucket: ${config.processedBucketName}`);
      console.log(`Loading processed files${patientId ? ` for patient: ${patientId}` : ' (all patients)'}`);

      // Use patient ID as prefix if provided to filter files
      // Structure: {patient_id}/{document_identifier}/ (same as raw bucket)
      const prefix = patientId ? `${patientId}/` : '';

      // Use storage service with processed bucket
      const s3Files = await storageService.listFiles(prefix, {
        includeMetadata: true,
        bucket: config.processedBucketName,
        pageSize: 1000
      });

      // Convert all processed files to ProcessedFile format
      const processedFiles: ProcessedFile[] = [];

      for (const s3File of s3Files) {
        // Extract patient ID and document ID from the file key
        // Structure: {patient_id}/{document_identifier}/filename.ext
        const keyParts = s3File.key.split('/');
        if (keyParts.length < 3) continue; // Skip malformed keys

        const extractedPatientId = keyParts[0];
        const documentIdentifier = keyParts[1];
        const fileName = keyParts[keyParts.length - 1];

        // Determine file type from extension
        const fileExtension = fileName.split('.').pop()?.toUpperCase() || 'UNKNOWN';
        
        // Extract metadata from S3
        const metadata = s3File.metadata || {};
        const category = metadata['document-category'] || 'other';
        const confidence = parseFloat(
          metadata['classification-confidence'] || '0'
        );
        const autoClassified = (
          metadata['auto-classified'] === 'true' ||
          metadata['auto-classified'] === 'True'
        );
        const originalClassification = metadata['original-classification'];
        const processingTimestamp = metadata['processing-timestamp'] ||
          metadata['classification-timestamp'] ||
          s3File.lastModified?.toISOString() || new Date().toISOString();
        // Use just the filename for processed files since original document is shown elsewhere
        const displayName = fileName;

        // Don't load file content during listing - only load at preview time
        let extractedData = null;
        let bdaMetadata = null;

        const processedFile: ProcessedFile = {
          id: s3File.key,
          name: displayName,
          type: fileExtension,
          size: s3File.size || 0,
          processedDate: processingTimestamp,
          category: category,
          confidence: confidence > 0 ? confidence : undefined,
          originalClassification: originalClassification,
          autoClassified: autoClassified,
          patientId: extractedPatientId,
          documentId: documentIdentifier,
          url: s3File.key,
          extractedData: extractedData,
          bdaMetadata: bdaMetadata,
        };

        processedFiles.push(processedFile);
      }

      // Sort by processing date (newest first)
      processedFiles.sort((a, b) => new Date(b.processedDate).getTime() - new Date(a.processedDate).getTime());

      console.log(`Loaded ${processedFiles.length} processed files${patientId ? ` for patient: ${patientId}` : ' (all patients)'}`);
      return processedFiles;

    } catch (error) {
      console.error('Failed to load processed files:', error);
      throw error;
    }
  }

  /**
   * Download a processed file
   */
  async downloadProcessedFile(file: ProcessedFile): Promise<Blob> {
    try {
      console.log(`Downloading processed file: ${file.name} (ID: ${file.id})`);
      const config = configService.getConfig();
      return await storageService.downloadFile(file.id, { bucket: config.processedBucketName });
    } catch (error) {
      console.error('Failed to download processed file:', error);
      throw error;
    }
  }

  /**
   * Get all result files for a processed document
   */
  async getDocumentResultFiles(patientId: string, documentId: string): Promise<{ [key: string]: unknown }> {
    try {
      const config = configService.getConfig();
      console.log(`Loading result files for document: ${documentId}, patient: ${patientId}`);

      // List all files in the document directory
      const prefix = `${patientId}/${documentId}/`;
      const s3Files = await storageService.listFiles(prefix, {
        bucket: config.processedBucketName,
        pageSize: 100
      });

      const resultFiles: { [key: string]: unknown } = {};

      for (const s3File of s3Files) {
        const fileName = s3File.key.split('/').pop() || '';

        try {
          const blob = await storageService.downloadFile(s3File.key, { bucket: config.processedBucketName });

          if (fileName.endsWith('.json')) {
            const text = await blob.text();
            resultFiles[fileName] = JSON.parse(text);
          } else {
            const text = await blob.text();
            resultFiles[fileName] = text;
          }
        } catch (error) {
          console.warn(`Failed to load result file ${fileName}:`, error);
          resultFiles[fileName] = `Error loading file: ${error}`;
        }
      }

      console.log(`Loaded ${Object.keys(resultFiles).length} result files for document ${documentId}`);
      return resultFiles;

    } catch (error) {
      console.error('Failed to load document result files:', error);
      throw error;
    }
  }
  /**
   * Convert PatientFile array to UnifiedFile array
   */
  convertPatientFilesToUnified(patientFiles: PatientFile[], patientId: string): UnifiedFile[] {
    const config = configService.getConfig();
    
    return patientFiles.map(patientFile => {
      const preview = this.getPreviewCapabilities(patientFile.name, patientFile.size);
      
      const unifiedFile: UnifiedFile = {
        id: patientFile.id,
        name: patientFile.name,
        type: patientFile.type,
        size: patientFile.size,
        date: patientFile.uploadDate,
        url: patientFile.url || patientFile.id,
        bucket: config.s3BucketName, // Raw bucket for patient files
        metadata: {},
        source: 'raw',
        patientId,
        rawProperties: {
          uploadDate: patientFile.uploadDate,
          category: patientFile.category,
          autoClassified: patientFile.autoClassified,
          classificationConfidence: patientFile.classificationConfidence,
          originalClassification: patientFile.originalClassification,
        },
        preview,
      };

      return unifiedFile;
    });
  }

  /**
   * Convert ProcessedFile array to UnifiedFile array
   */
  convertProcessedFilesToUnified(processedFiles: ProcessedFile[]): UnifiedFile[] {
    const config = configService.getConfig();
    
    return processedFiles.map(processedFile => {
      const preview = this.getPreviewCapabilities(processedFile.name, processedFile.size);
      
      const unifiedFile: UnifiedFile = {
        id: processedFile.id,
        name: processedFile.name,
        type: processedFile.type,
        size: processedFile.size,
        date: processedFile.processedDate,
        url: processedFile.url || processedFile.id,
        bucket: config.processedBucketName,
        metadata: {},
        source: 'processed',
        patientId: processedFile.patientId || 'unknown',
        processedProperties: {
          processedDate: processedFile.processedDate,
          category: processedFile.category,
          confidence: processedFile.confidence,
          originalClassification: processedFile.originalClassification,
          autoClassified: processedFile.autoClassified,
          documentId: processedFile.documentId,
          extractedData: processedFile.extractedData as Record<string, unknown>,
          bdaMetadata: processedFile.bdaMetadata as Record<string, unknown>,
        },
        preview,
      };

      return unifiedFile;
    });
  }

  /**
   * Download a unified file
   */
  async downloadUnifiedFile(file: UnifiedFile): Promise<Blob> {
    try {
      console.log(`Downloading unified file: ${file.name} from ${file.source} bucket`);
      return await storageService.downloadFile(file.url, { bucket: file.bucket });
    } catch (error) {
      console.error('Failed to download unified file:', error);
      throw error;
    }
  }
}

export const processedFileService = new ProcessedFileService();

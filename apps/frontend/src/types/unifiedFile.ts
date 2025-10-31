/**
 * Unified File Data Model
 * Extends existing file models with source identification and preview capabilities
 */

import type { PreviewConfig } from '../utils/fileTypeDetector';

/**
 * Source type for unified files
 */
export type FileSource = 'raw' | 'processed';

/**
 * Base interface for all file types in the system
 */
export interface BaseFile {
  id: string;
  name: string;
  type: string;
  size: number;
  date: string;
  url: string;
  bucket: string;
  metadata?: Record<string, string>;
}

/**
 * Raw file specific properties
 */
export interface RawFileProperties {
  uploadDate: string;
  category?: string;
  autoClassified?: boolean;
  classificationConfidence?: number;
  originalClassification?: string;
}

/**
 * Processed file specific properties
 */
export interface ProcessedFileProperties {
  processedDate: string;
  category?: string;
  confidence?: number;
  originalClassification?: string;
  autoClassified?: boolean;
  documentId?: string;
  extractedData?: Record<string, unknown>;
  bdaMetadata?: Record<string, unknown>;
}

/**
 * Preview capabilities for files
 */
export interface PreviewCapabilities {
  previewSupported: boolean;
  previewConfig?: PreviewConfig;
  contentType?: string;
  canLoadContent: boolean;
}

/**
 * Unified file interface that combines raw and processed files
 */
export interface UnifiedFile extends BaseFile {
  // Source identification
  source: FileSource;
  
  // Patient association
  patientId: string;
  
  // Source-specific properties (only one will be populated)
  rawProperties?: RawFileProperties;
  processedProperties?: ProcessedFileProperties;
  
  // Preview capabilities
  preview: PreviewCapabilities;
  
  // Caching metadata
  lastAccessed?: string;
  contentCached?: boolean;
}

/**
 * File content for preview functionality
 */
export interface FileContent {
  content: string | Blob;
  contentType: string;
  size: number;
  lastModified?: string;
  encoding?: string;
}

/**
 * Preview state for managing file content loading
 */
export interface PreviewState {
  loading: boolean;
  content: FileContent | null;
  error: string | null;
  loadedAt?: string;
}



/**
 * Options for loading unified files
 */
export interface UnifiedFileLoadOptions {
  patientId?: string;
  includeRaw?: boolean;
  includeProcessed?: boolean;
  maxFiles?: number;
}

/**
 * Error types for file operations
 */
export enum FileError {
  NOT_FOUND = 'FILE_NOT_FOUND',
  ACCESS_DENIED = 'ACCESS_DENIED',
  SIZE_LIMIT_EXCEEDED = 'SIZE_LIMIT_EXCEEDED',
  UNSUPPORTED_TYPE = 'UNSUPPORTED_TYPE',
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',
  INVALID_CONTENT = 'INVALID_CONTENT',
}

/**
 * File operation result
 */
export interface FileOperationResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    type: FileError;
    message: string;
    details?: Record<string, unknown>;
  };
}

/**
 * Type guards for unified files
 */
export function isRawFile(file: UnifiedFile): file is UnifiedFile & { rawProperties: RawFileProperties } {
  return file.source === 'raw' && !!file.rawProperties;
}

export function isProcessedFile(file: UnifiedFile): file is UnifiedFile & { processedProperties: ProcessedFileProperties } {
  return file.source === 'processed' && !!file.processedProperties;
}

/**
 * Helper function to get display date for unified files
 */
export function getFileDisplayDate(file: UnifiedFile): string {
  if (isRawFile(file)) {
    return file.rawProperties.uploadDate;
  } else if (isProcessedFile(file)) {
    return file.processedProperties.processedDate;
  }
  return file.date;
}

/**
 * Helper function to get file category for display
 */
export function getFileCategory(file: UnifiedFile): string | undefined {
  if (isRawFile(file)) {
    return file.rawProperties.category;
  } else if (isProcessedFile(file)) {
    return file.processedProperties.category;
  }
  return undefined;
}

/**
 * Helper function to get classification confidence
 */
export function getClassificationConfidence(file: UnifiedFile): number | undefined {
  if (isRawFile(file)) {
    return file.rawProperties.classificationConfidence;
  } else if (isProcessedFile(file)) {
    return file.processedProperties.confidence;
  }
  return undefined;
}

/**
 * Helper function to check if file was auto-classified
 */
export function isAutoClassified(file: UnifiedFile): boolean {
  if (isRawFile(file)) {
    return file.rawProperties.autoClassified || false;
  } else if (isProcessedFile(file)) {
    return file.processedProperties.autoClassified || false;
  }
  return false;
}

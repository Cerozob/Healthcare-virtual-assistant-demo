/**
 * Processed File Service
 * Handles operations for processed files from the document workflow
 */

import { configService } from './configService';
import { storageService } from './storageService';
import type { ProcessedFile } from '../components/config/ProcessedFileManager';

class ProcessedFileService {

  /**
   * Get processed files from the processed bucket
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

      // Filter for main extracted data files and convert to ProcessedFile format
      const processedFiles: ProcessedFile[] = [];

      for (const s3File of s3Files) {


        // Extract patient ID and document ID from the file key
        // Structure: {patient_id}/{document_identifier}/extracted_data.json
        const keyParts = s3File.key.split('/');
        if (keyParts.length < 3) continue; // Skip malformed keys

        const extractedPatientId = keyParts[0];
        const documentIdentifier = keyParts[1];

        // Extract metadata from S3
        // Handle both with and without  prefix
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
          metadata['classification-timestamp'];
        const originalDocument = metadata["document-id"] || "Unknown";

        // Try to download and parse the extracted data for preview
        let extractedData = null;
        let bdaMetadata = null;

        try {
          const blob = await storageService.downloadFile(s3File.key, { bucket: config.processedBucketName });
          const text = await blob.text();
          const parsedData = JSON.parse(text);

          // Separate extracted data from BDA metadata
          extractedData = { ...parsedData };
          delete extractedData.processing_metadata;

          // Look for BDA metadata file
          const bdaMetadataKey = s3File.key.replace('/extracted_data.json', '/bda_metadata.json');
          try {
            const bdaBlob = await storageService.downloadFile(bdaMetadataKey, { bucket: config.processedBucketName });
            const bdaText = await bdaBlob.text();
            bdaMetadata = JSON.parse(bdaText);
          } catch {
            console.log(`No BDA metadata found for ${documentIdentifier}`);
          }
        } catch (dataError) {
          console.warn(`Failed to load extracted data for ${s3File.key}:`, dataError);
        }

        const processedFile: ProcessedFile = {
          id: s3File.key,
          name: originalDocument,
          type: 'JSON',
          size: s3File.size || 0,
          processedDate: processingTimestamp || s3File.lastModified?.toISOString() || new Date().toISOString(),
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
}

export const processedFileService = new ProcessedFileService();

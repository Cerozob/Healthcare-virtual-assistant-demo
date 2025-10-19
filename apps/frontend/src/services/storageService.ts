/**
 * Storage Service
 * Handles file uploads and downloads using existing CDK S3 bucket
 */

import { uploadData, downloadData, remove, list, type TransferProgressEvent } from 'aws-amplify/storage';

interface UploadResult {
  key: string;
  url?: string;
}

interface FileItem {
  key: string;
  size?: number;
  lastModified?: Date;
}

class StorageService {
  /**
   * Upload a file to S3
   */
  async uploadFile(
    file: File,
    key: string,
    options?: {
      accessLevel?: 'guest' | 'protected' | 'private';
      contentType?: string;
      onProgress?: (event: TransferProgressEvent) => void;
    }
  ): Promise<UploadResult> {
    try {
      console.log(`📤 Uploading file: ${key}`);
      
      const result = await uploadData({
        key,
        data: file,
        options: {
          accessLevel: options?.accessLevel || 'private',
          contentType: options?.contentType || file.type,
          onProgress: options?.onProgress,
        },
      }).result;

      console.log(`✅ File uploaded successfully: ${key}`);
      return {
        key: result.key,
      };
    } catch (error) {
      console.error(`❌ Failed to upload file: ${key}`, error);
      throw error;
    }
  }

  /**
   * Download a file from S3
   */
  async downloadFile(
    key: string,
    options?: {
      accessLevel?: 'guest' | 'protected' | 'private';
    }
  ): Promise<Blob> {
    try {
      console.log(`📥 Downloading file: ${key}`);
      
      const result = await downloadData({
        key,
        options: {
          accessLevel: options?.accessLevel || 'private',
        },
      }).result;

      const blob = await result.body.blob();
      console.log(`✅ File downloaded successfully: ${key}`);
      return blob;
    } catch (error) {
      console.error(`❌ Failed to download file: ${key}`, error);
      throw error;
    }
  }

  /**
   * Delete a file from S3
   */
  async deleteFile(
    key: string,
    options?: {
      accessLevel?: 'guest' | 'protected' | 'private';
    }
  ): Promise<void> {
    try {
      console.log(`🗑️ Deleting file: ${key}`);
      
      await remove({
        key,
        options: {
          accessLevel: options?.accessLevel || 'private',
        },
      });

      console.log(`✅ File deleted successfully: ${key}`);
    } catch (error) {
      console.error(`❌ Failed to delete file: ${key}`, error);
      throw error;
    }
  }

  /**
   * List files in S3
   */
  async listFiles(
    prefix?: string,
    options?: {
      accessLevel?: 'guest' | 'protected' | 'private';
      pageSize?: number;
    }
  ): Promise<FileItem[]> {
    try {
      console.log(`📋 Listing files with prefix: ${prefix || 'all'}`);
      
      const result = await list({
        prefix,
        options: {
          accessLevel: options?.accessLevel || 'private',
          pageSize: options?.pageSize || 100,
        },
      });

      const files = result.items.map(item => ({
        key: item.key,
        size: item.size,
        lastModified: item.lastModified,
      }));

      console.log(`✅ Found ${files.length} files`);
      return files;
    } catch (error) {
      console.error(`❌ Failed to list files`, error);
      throw error;
    }
  }

  /**
   * Generate a download URL for a file
   */
  async getDownloadUrl(
    key: string,
    options?: {
      accessLevel?: 'guest' | 'protected' | 'private';
      expiresIn?: number; // seconds
    }
  ): Promise<string> {
    try {
      console.log(`🔗 Generating download URL for: ${key}`);
      
      const result = await downloadData({
        key,
        options: {
          accessLevel: options?.accessLevel || 'private',
        },
      }).result;

      // For now, we'll create a blob URL
      // In production, you might want to use getUrl from aws-amplify/storage
      const blob = await result.body.blob();
      const url = URL.createObjectURL(blob);
      
      console.log(`✅ Download URL generated for: ${key}`);
      return url;
    } catch (error) {
      console.error(`❌ Failed to generate download URL: ${key}`, error);
      throw error;
    }
  }
}

export const storageService = new StorageService();
export type { FileItem, UploadResult };

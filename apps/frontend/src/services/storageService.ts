/**
 * Storage Service
 * Handles file uploads and downloads using AWS Amplify Storage
 */

import { uploadData, downloadData, remove, list, type TransferProgressEvent } from 'aws-amplify/storage';
import { configService } from './configService';

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
   * Upload a file to S3 using Amplify Storage
   */
  async uploadFile(
    file: File,
    key: string,
    options?: {
      contentType?: string;
      onProgress?: (event: TransferProgressEvent) => void;
      bucket?: string;
      metadata?: { [key: string]: string };
    }
  ): Promise<UploadResult> {
    try {
      console.log(`📤 Uploading file: ${key}`);

      // Get and log bucket configuration
      const config = configService.getConfig();
      console.log(`🪣 StorageService - Bucket from config: ${config.s3BucketName}`);
      console.log(`🪣 StorageService - Bucket from options: ${options?.bucket}`);
      console.log(`🌍 StorageService - Region: ${config.region}`);

      // Prepare metadata for upload
      const uploadMetadata = {
        ...options?.metadata,
        'Content-Type': file.type,
      };

      // Log metadata being uploaded for verification
      console.log(`📋 Metadata being uploaded:`, uploadMetadata);

      const result = await uploadData({
        path: key,
        data: file,
        options: {
          contentType: options?.contentType || file.type,
          onProgress: options?.onProgress,
          metadata: uploadMetadata,
          // Use the custom bucket configuration
          bucket: {
            bucketName: config.s3BucketName,
            region: config.region
          },
        },
      }).result;

      console.log(`✅ File uploaded successfully: ${key}`);
      console.log(`📍 S3 Path: ${result.path}`);

      return {
        key: result.path,
      };
    } catch (error) {
      console.error(`❌ Failed to upload file: ${key}`, error);
      console.error(`❌ StorageService - Error details:`, {
        bucketFromConfig: configService.getConfig().s3BucketName,
        bucketFromOptions: options?.bucket,
        region: configService.getConfig().region
      });
      throw error;
    }
  }

  /**
   * Download a file from S3 using Amplify Storage
   */
  async downloadFile(
    key: string
  ): Promise<Blob> {
    try {
      console.log(`📥 Downloading file: ${key}`);

      const config = configService.getConfig();
      const result = await downloadData({
        path: key,
        options: {
          bucket: {
            bucketName: config.s3BucketName,
            region: config.region
          },
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
   * Delete a file from S3 using Amplify Storage
   */
  async deleteFile(
    key: string,
  ): Promise<void> {
    try {
      console.log(`🗑️ Deleting file: ${key}`);

      const config = configService.getConfig();
      await remove({
        path: key,
        options: {
          bucket: {
            bucketName: config.s3BucketName,
            region: config.region
          },
        },
      });

      console.log(`✅ File deleted successfully: ${key}`);
    } catch (error) {
      console.error(`❌ Failed to delete file: ${key}`, error);
      throw error;
    }
  }

  /**
   * List files in S3 using Amplify Storage
   */
  async listFiles(
    prefix?: string,
    options?: {
      pageSize?: number;
    }
  ): Promise<FileItem[]> {
    try {
      console.log(`📋 Listing files with prefix: ${prefix || 'all'}`);

      const config = configService.getConfig();
      const result = await list({
        path: prefix || '',
        options: {
          pageSize: options?.pageSize || 100,
          bucket: {
            bucketName: config.s3BucketName,
            region: config.region
          },
        },
      });

      const files = result.items.map(item => ({
        key: item.path,
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
   * Generate a download URL for a file using Amplify Storage
   */
  async getDownloadUrl(
    key: string,
    options?: {
      expiresIn?: number; // seconds
    }
  ): Promise<string> {
    try {
      console.log(`🔗 Generating download URL for: ${key}`);

      const config = configService.getConfig();
      const result = await downloadData({
        path: key,
        options: {
          bucket: {
            bucketName: config.s3BucketName,
            region: config.region
          },
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

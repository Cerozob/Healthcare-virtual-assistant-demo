/**
 * Storage Service
 * Handles file uploads and downloads using AWS S3 SDK directly
 */

import { DeleteObjectCommand, GetObjectCommand, HeadObjectCommand, ListObjectsV2Command, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { fetchAuthSession } from 'aws-amplify/auth';
import { configService } from './configService';

interface UploadResult {
  key: string;
  url?: string;
}

interface FileItem {
  key: string;
  size?: number;
  lastModified?: Date;
  metadata?: { [key: string]: string };
}

interface ProgressEvent {
  loaded: number;
  total: number;
}

class StorageService {
  private s3Client: S3Client | null = null;
  private lastCredentialsRefresh: number = 0;
  private readonly CREDENTIALS_REFRESH_INTERVAL = 50 * 60 * 1000; // 50 minutes

  private async getS3Client(): Promise<S3Client> {
    const now = Date.now();

    // Refresh client if it doesn't exist or credentials are old
    if (!this.s3Client || (now - this.lastCredentialsRefresh) > this.CREDENTIALS_REFRESH_INTERVAL) {
      const config = configService.getConfig();

      // Get credentials from Amplify Auth session
      const session = await fetchAuthSession();
      const credentials = session.credentials;

      if (!credentials) {
        throw new Error('No AWS credentials available');
      }

      // Log credential information (without exposing sensitive data)
      console.log(`🔑 Credentials info:`, {
        hasAccessKeyId: !!credentials.accessKeyId,
        hasSecretAccessKey: !!credentials.secretAccessKey,
        hasSessionToken: !!credentials.sessionToken,
        accessKeyIdPrefix: `${credentials.accessKeyId?.substring(0, 4)}...`,
        expiration: credentials.expiration
      });

      this.s3Client = new S3Client({
        region: config.region,
        credentials: {
          accessKeyId: credentials.accessKeyId,
          secretAccessKey: credentials.secretAccessKey,
          sessionToken: credentials.sessionToken,
        },
        // Add explicit configuration to prevent signature issues
        forcePathStyle: false,
        useAccelerateEndpoint: false,
        useDualstackEndpoint: false,
      });

      this.lastCredentialsRefresh = now;
      console.log('🔑 S3 client credentials refreshed');
    }

    return this.s3Client;
  }

  /**
   * Force refresh of S3 client credentials
   */
  public refreshCredentials(): void {
    this.s3Client = null;
    this.lastCredentialsRefresh = 0;
  }

  /**
   * Upload a file to S3 using AWS S3 SDK directly
   */
  async uploadFile(
    file: File,
    key: string,
    options?: {
      contentType?: string;
      onProgress?: (event: ProgressEvent) => void;
      bucket?: string;
      metadata?: { [key: string]: string };
    }
  ): Promise<UploadResult> {
    try {
      console.log(`📤 Uploading file: ${key}`);

      // Get and log bucket configuration
      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;

      // Prepare variables for upload and potential retry
      const fileBuffer = await file.arrayBuffer();
      const contentType = options?.contentType || file.type;

      // Clean and encode metadata to prevent signature issues
      const uploadMetadata: { [key: string]: string } = {};
      if (options?.metadata) {
        for (const [key, value] of Object.entries(options.metadata)) {
          // S3 metadata keys and values have restrictions
          // Keys: must be valid HTTP header names (no spaces, special chars)
          // Values: must be UTF-8 encoded, no control characters
          const cleanKey = key.toLowerCase().replace(/[^a-z0-9-]/g, '-');
          // Clean value by removing problematic characters and limiting length
          let cleanValue = String(value);
          // Remove common problematic characters for S3 metadata
          cleanValue = cleanValue.replace(/[^\x20-\x7E]/g, ''); // Keep only printable ASCII
          cleanValue = cleanValue.substring(0, 2048); // S3 metadata value limit

          uploadMetadata[cleanKey] = cleanValue;
        }
      }

      // Log detailed debugging information
      console.log(`🪣 StorageService - Bucket from config: ${config.s3BucketName}`);
      console.log(`🪣 StorageService - Bucket from options: ${options?.bucket}`);
      console.log(`🌍 StorageService - Region: ${config.region}`);
      console.log(`📋 File details:`, {
        name: file.name,
        type: file.type,
        size: file.size,
        lastModified: file.lastModified
      });
      console.log(`📋 Content-Type being set:`, contentType);
      console.log(`📋 Original metadata:`, options?.metadata);
      console.log(`📋 Cleaned metadata being uploaded:`, uploadMetadata);
      console.log(`📋 S3 Key:`, key);
      console.log(`📋 Bucket Name:`, bucketName);

      // Check for potential signature issues
      const currentTime = new Date().toISOString();
      console.log(`🕐 Current time:`, currentTime);
      console.log(`🔍 Key length:`, key.length);
      console.log(`🔍 Key contains special chars:`, /[^a-zA-Z0-9\-_./]/.test(key));

      const s3Client = await this.getS3Client();

      // Log the command parameters before sending
      console.log(`📋 S3 Command Parameters:`, {
        Bucket: bucketName,
        Key: key,
        ContentType: contentType,
        BodySize: fileBuffer.byteLength,
        MetadataKeys: Object.keys(uploadMetadata)
      });

      // Create the upload command
      const command = new PutObjectCommand({
        Bucket: bucketName,
        Key: key,
        Body: new Uint8Array(fileBuffer),
        ContentType: contentType,
        Metadata: uploadMetadata,
      });

      // If progress callback is provided, we'll simulate progress
      // Note: S3 SDK doesn't provide built-in progress for browser uploads
      if (options?.onProgress) {
        options.onProgress({ loaded: 0, total: file.size });
      }

      const result = await s3Client.send(command);

      // Simulate progress completion
      if (options?.onProgress) {
        options.onProgress({ loaded: file.size, total: file.size });
      }

      console.log(`✅ File uploaded successfully: ${key}`);
      console.log(`📍 S3 ETag: ${result.ETag}`);

      return {
        key: key,
      };
    } catch (error) {
      console.error(`❌ Failed to upload file: ${key}`, error);

      // Get variables for error logging (re-declare if needed)
      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;
      const uploadMetadata = { ...options?.metadata };

      console.error(`❌ StorageService - Error details:`, {
        bucketFromConfig: config.s3BucketName,
        bucketFromOptions: options?.bucket,
        region: config.region,
        errorName: error instanceof Error ? error.name : 'Unknown',
        errorMessage: error instanceof Error ? error.message : 'Unknown error'
      });

      // Special handling for signature errors
      if (error instanceof Error && error.message.includes('SignatureDoesNotMatch')) {
        console.error(`🔐 Signature Error - Additional Debug Info:`, {
          contentType: options?.contentType || file.type,
          fileType: file.type,
          fileName: file.name,
          originalMetadataCount: Object.keys(options?.metadata || {}).length,
          cleanedMetadataCount: Object.keys(uploadMetadata).length,
          credentialsRefreshTime: this.lastCredentialsRefresh,
          timeSinceRefresh: Date.now() - this.lastCredentialsRefresh
        });

        // Try refreshing credentials and retrying once
        console.log(`🔄 Attempting to refresh credentials and retry...`);
        this.refreshCredentials();

        try {
          const retryFileBuffer = await file.arrayBuffer();
          const retryContentType = options?.contentType || file.type;

          const newS3Client = await this.getS3Client();

          // First try without metadata to isolate the issue
          console.log(`🔄 Retry 1: Attempting upload without metadata...`);
          const simpleRetryCommand = new PutObjectCommand({
            Bucket: bucketName,
            Key: key,
            Body: new Uint8Array(retryFileBuffer),
            ContentType: retryContentType,
            // No metadata on first retry
          });

          const simpleRetryResult = await newS3Client.send(simpleRetryCommand);
          console.log(`✅ File uploaded successfully without metadata: ${key}`);
          console.log(`📍 S3 ETag: ${simpleRetryResult.ETag}`);
          console.log(`⚠️ Note: Metadata was skipped due to signature issues`);

          return { key: key };
        } catch (retryError) {
          console.error(`❌ Retry without metadata also failed:`, retryError);

          // Try one more time with minimal metadata
          try {
            console.log(`🔄 Retry 2: Attempting with minimal metadata...`);
            const retryFileBuffer = await file.arrayBuffer();
            const newS3Client = await this.getS3Client();

            const minimalRetryCommand = new PutObjectCommand({
              Bucket: bucketName,
              Key: key,
              Body: new Uint8Array(retryFileBuffer),
              ContentType: options?.contentType || file.type,
              Metadata: {
                'patient-id': uploadMetadata['patient-id'] || '',
                'file-id': uploadMetadata['file-id'] || '',
                'document-category': uploadMetadata['document-category'] || "auto"
              }
            });

            const minimalRetryResult = await newS3Client.send(minimalRetryCommand);
            console.log(`✅ File uploaded successfully with minimal metadata: ${key}`);
            console.log(`📍 S3 ETag: ${minimalRetryResult.ETag}`);

            return { key: key };
          } catch (finalError) {
            console.error(`❌ All retries failed:`, finalError);
            throw finalError;
          }
        }
      }

      throw error;
    }
  }

  /**
   * Download a file from S3 using AWS S3 SDK directly
   */
  async downloadFile(
    key: string,
    options?: {
      bucket?: string;
    }
  ): Promise<Blob> {
    try {
      console.log(`📥 Downloading file: ${key}`);

      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;
      const s3Client = await this.getS3Client();

      const command = new GetObjectCommand({
        Bucket: bucketName,
        Key: key,
      });

      const result = await s3Client.send(command);

      if (!result.Body) {
        throw new Error('No body in S3 response');
      }

      // Convert the response body to a blob using the most compatible method
      const byteArray = await result.Body.transformToByteArray();
      const buffer = byteArray.buffer instanceof ArrayBuffer
        ? byteArray.buffer
        : new ArrayBuffer(byteArray.byteLength);

      if (!(byteArray.buffer instanceof ArrayBuffer)) {
        new Uint8Array(buffer).set(byteArray);
      }

      const blob = new Blob([buffer], { type: result.ContentType });
      console.log(`✅ File downloaded successfully: ${key} from bucket: ${bucketName}`);
      return blob;
    } catch (error) {
      console.error(`❌ Failed to download file: ${key}`, error);
      throw error;
    }
  }

  /**
   * Delete a file from S3 using AWS S3 SDK directly
   */
  async deleteFile(
    key: string,
    options?: {
      bucket?: string;
    }
  ): Promise<void> {
    try {
      console.log(`🗑️ Deleting file: ${key}`);

      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;
      const s3Client = await this.getS3Client();

      const command = new DeleteObjectCommand({
        Bucket: bucketName,
        Key: key,
      });

      await s3Client.send(command);

      console.log(`✅ File deleted successfully: ${key} from bucket: ${bucketName}`);
    } catch (error) {
      console.error(`❌ Failed to delete file: ${key}`, error);
      throw error;
    }
  }

  /**
   * List files in S3 using AWS S3 SDK directly with metadata
   */
  async listFiles(
    prefix?: string,
    options?: {
      pageSize?: number;
      includeMetadata?: boolean;
      bucket?: string;
    }
  ): Promise<FileItem[]> {
    try {
      console.log(`📋 Listing files with prefix: ${prefix || 'all'}`);
      console.log(`📋 Options:`, options);
      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;
      const s3Client = await this.getS3Client();

      const command = new ListObjectsV2Command({
        Bucket: bucketName,
        Prefix: prefix || '',
        MaxKeys: options?.pageSize || 100,
      });

      const result = await s3Client.send(command);

      const files: FileItem[] = [];

      // If metadata is requested, fetch it for each file
      if (options?.includeMetadata) {
        for (const item of result.Contents || []) {
          if (!item.Key) continue;

          try {
            // Fetch object metadata using HeadObject (more efficient than GetObject)
            const headResponse = await s3Client.send(
              new HeadObjectCommand({
                Bucket: bucketName,
                Key: item.Key,
              })
            );

            console.log(`✅ Fetched metadata for ${item.Key}`)
            console.log(headResponse.Metadata);

            files.push({
              key: item.Key,
              size: item.Size,
              lastModified: item.LastModified,
              metadata: headResponse.Metadata || {},
            });
          } catch (error) {
            console.warn(`Failed to fetch metadata for ${item.Key}:`, error);
            // Add file without metadata if fetch fails
            files.push({
              key: item.Key,
              size: item.Size,
              lastModified: item.LastModified,
              metadata: {},
            });
          }
        }
      } else {
        // Just return basic file info without metadata
        for (const item of result.Contents || []) {
          files.push({
            key: item.Key || '',
            size: item.Size,
            lastModified: item.LastModified,
          });
        }
      }

      console.log(`✅ Found ${files.length} files${options?.includeMetadata ? ' with metadata' : ''} from bucket: ${bucketName}`);
      return files;
    } catch (error) {
      console.error(`❌ Failed to list files from bucket: ${options?.bucket || 'default'}`, error);
      throw error;
    }
  }

  /**
   * Generate a presigned download URL for a file using AWS S3 SDK directly
   */
  async getDownloadUrl(
    key: string,
    options?: {
      expiresIn?: number; // seconds
      bucket?: string;
    }
  ): Promise<string> {
    try {
      console.log(`🔗 Generating download URL for: ${key}`);

      const config = configService.getConfig();
      const bucketName = options?.bucket || config.s3BucketName;
      const s3Client = await this.getS3Client();

      const command = new GetObjectCommand({
        Bucket: bucketName,
        Key: key,
      });

      const url = await getSignedUrl(s3Client, command, {
        expiresIn: options?.expiresIn || 3600, // Default 1 hour
      });

      console.log(`✅ Download URL generated for: ${key} from bucket: ${bucketName}`);
      return url;
    } catch (error) {
      console.error(`❌ Failed to generate download URL: ${key}`, error);
      throw error;
    }
  }
}

export const storageService = new StorageService();
export type { FileItem, ProgressEvent, UploadResult };

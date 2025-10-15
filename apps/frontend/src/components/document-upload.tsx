import React, { useState, useCallback } from 'react';
import { documentUploadService, DocumentMetadata, DocumentUploadOptions } from '../services/document-upload-service';

interface DocumentUploadProps {
  onUploadComplete?: (documents: DocumentMetadata[]) => void;
  onUploadError?: (error: string) => void;
  options?: DocumentUploadOptions;
  multiple?: boolean;
  accept?: string;
  maxSize?: number; // in MB
  className?: string;
}

interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadComplete,
  onUploadError,
  options = {},
  multiple = true,
  accept = '.pdf,.jpg,.jpeg,.png,.tiff,.mp3,.wav,.mp4,.docx,.doc',
  maxSize = 100,
  className = '',
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFiles = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);
    
    // Validate files
    const validationErrors: string[] = [];
    fileArray.forEach(file => {
      const validation = documentUploadService.validateFile(file);
      if (!validation.valid) {
        validationErrors.push(`${file.name}: ${validation.error}`);
      }
    });

    if (validationErrors.length > 0) {
      onUploadError?.(validationErrors.join('\n'));
      return;
    }

    setIsUploading(true);
    
    // Initialize upload progress tracking
    const initialProgress: UploadProgress[] = fileArray.map(file => ({
      fileName: file.name,
      progress: 0,
      status: 'uploading',
    }));
    setUploads(initialProgress);

    try {
      const uploadPromises = fileArray.map(async (file, index) => {
        try {
          const metadata = await documentUploadService.uploadDocument(file, {
            ...options,
            onProgress: (progress) => {
              const percentage = progress.totalBytes 
                ? Math.round((progress.transferredBytes / progress.totalBytes) * 100)
                : 0;
              
              setUploads(prev => prev.map((upload, i) => 
                i === index 
                  ? { ...upload, progress: percentage }
                  : upload
              ));
            },
          });

          // Update status to completed
          setUploads(prev => prev.map((upload, i) => 
            i === index 
              ? { ...upload, progress: 100, status: 'completed' }
              : upload
          ));

          return metadata;
        } catch (error) {
          // Update status to error
          setUploads(prev => prev.map((upload, i) => 
            i === index 
              ? { ...upload, status: 'error', error: (error as Error).message }
              : upload
          ));
          throw error;
        }
      });

      const results = await Promise.allSettled(uploadPromises);
      const successful = results
        .filter((result): result is PromiseFulfilledResult<DocumentMetadata> => 
          result.status === 'fulfilled'
        )
        .map(result => result.value);

      const failed = results
        .filter((result): result is PromiseRejectedResult => 
          result.status === 'rejected'
        );

      if (successful.length > 0) {
        onUploadComplete?.(successful);
      }

      if (failed.length > 0) {
        const errorMessages = failed.map(f => f.reason.message).join('\n');
        onUploadError?.(errorMessages);
      }

    } catch (error) {
      onUploadError?.((error as Error).message);
    } finally {
      setIsUploading(false);
      // Clear progress after a delay
      setTimeout(() => setUploads([]), 3000);
    }
  }, [options, onUploadComplete, onUploadError]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  return (
    <div className={`document-upload ${className}`}>
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          border: '2px dashed #ccc',
          borderRadius: '8px',
          padding: '20px',
          textAlign: 'center',
          backgroundColor: isDragging ? '#f0f8ff' : '#fafafa',
          cursor: isUploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
        }}
      >
        <input
          type="file"
          multiple={multiple}
          accept={accept}
          onChange={handleFileSelect}
          disabled={isUploading}
          style={{ display: 'none' }}
          id="file-input"
        />
        
        <label htmlFor="file-input" style={{ cursor: 'inherit' }}>
          {isUploading ? (
            <div>
              <div>📤 Uploading files...</div>
              <div style={{ fontSize: '0.9em', color: '#666', marginTop: '8px' }}>
                Please wait while your files are being uploaded
              </div>
            </div>
          ) : (
            <div>
              <div>📁 Drop files here or click to select</div>
              <div style={{ fontSize: '0.9em', color: '#666', marginTop: '8px' }}>
                Supported: PDF, Images, Audio, Video, Word documents (max {maxSize}MB)
              </div>
            </div>
          )}
        </label>
      </div>

      {uploads.length > 0 && (
        <div className="upload-progress" style={{ marginTop: '16px' }}>
          <h4>Upload Progress</h4>
          {uploads.map((upload, index) => (
            <div key={index} style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9em' }}>{upload.fileName}</span>
                <span style={{ fontSize: '0.8em', color: upload.status === 'error' ? 'red' : 'inherit' }}>
                  {upload.status === 'error' ? '❌ Error' : 
                   upload.status === 'completed' ? '✅ Complete' : 
                   `${upload.progress}%`}
                </span>
              </div>
              {upload.status === 'uploading' && (
                <div style={{ 
                  width: '100%', 
                  height: '4px', 
                  backgroundColor: '#eee', 
                  borderRadius: '2px',
                  overflow: 'hidden'
                }}>
                  <div 
                    style={{ 
                      width: `${upload.progress}%`, 
                      height: '100%', 
                      backgroundColor: '#007bff',
                      transition: 'width 0.3s ease'
                    }} 
                  />
                </div>
              )}
              {upload.error && (
                <div style={{ fontSize: '0.8em', color: 'red', marginTop: '4px' }}>
                  {upload.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;

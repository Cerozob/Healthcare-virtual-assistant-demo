/**
 * PromptInput Component
 * Message input with file upload capabilities
 */

import { useState, useRef, ChangeEvent, DragEvent } from 'react';
import {
  Box,
  Button,
  FormField,
  Textarea,
  SpaceBetween,
  Alert,
  Icon
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';

interface PromptInputProps {
  onSendMessage: (content: string, files?: File[]) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

// Supported file types based on requirements
const SUPPORTED_FILE_TYPES = {
  documents: ['.pdf', '.tiff', '.tif', '.jpeg', '.jpg', '.png', '.docx', '.txt', '.md', '.html', '.csv', '.xlsx'],
  images: ['.png', '.jpg', '.jpeg'],
  videos: ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
  audio: ['.amr', '.flac', '.m4a', '.mp3', '.ogg', '.wav']
};

const ALL_SUPPORTED_TYPES = [
  ...SUPPORTED_FILE_TYPES.documents,
  ...SUPPORTED_FILE_TYPES.videos,
  ...SUPPORTED_FILE_TYPES.audio
].join(',');

export function PromptInput({ onSendMessage, disabled = false, isLoading = false }: PromptInputProps) {
  const { t } = useLanguage();
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (message.trim() || files.length > 0) {
      onSendMessage(message.trim(), files.length > 0 ? files : undefined);
      setMessage('');
      setFiles([]);
      setUploadError(null);
    }
  };

  const handleKeyPress = (event: any) => {
    const e = event.detail as KeyboardEvent;
    if (e.key === 'Enter' && !e.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const validateFile = (file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    const isSupported = ALL_SUPPORTED_TYPES.split(',').includes(extension);
    
    if (!isSupported) {
      setUploadError(`${t.fileUpload.invalidType}: ${file.name}`);
      return false;
    }

    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setUploadError(`${t.fileUpload.tooLarge}: ${file.name} (${t.fileUpload.maxSize}: 50MB)`);
      return false;
    }

    return true;
  };

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const validFiles: File[] = [];
    setUploadError(null);

    Array.from(selectedFiles).forEach(file => {
      if (validateFile(file)) {
        validFiles.push(file);
      }
    });

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setUploadError(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Box padding="s">
      <SpaceBetween size="m">
        {/* File Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${isDragging ? '#0972d3' : '#e9ebed'}`,
            borderRadius: '8px',
            padding: '16px',
            backgroundColor: isDragging ? '#f2f8fd' : '#fafafa',
            transition: 'all 0.2s ease',
            cursor: 'pointer'
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <Box textAlign="center">
            <Icon name="upload" size="medium" />
            <Box fontSize="body-m" padding={{ top: 's' }}>
              {t.fileUpload.dragDrop}
            </Box>
            <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xs' }}>
              {t.fileUpload.supportedFormats}: PDF, TIFF, JPEG, PNG, DOCX, MP4, MOV, AVI, MKV, WEBM, AMR, FLAC, M4A, MP3, Ogg, WAV
            </Box>
          </Box>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ALL_SUPPORTED_TYPES}
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />
        </div>

        {/* Upload Error */}
        {uploadError && (
          <Alert type="error" dismissible onDismiss={() => setUploadError(null)}>
            {uploadError}
          </Alert>
        )}

        {/* Selected Files */}
        {files.length > 0 && (
          <Box>
            <SpaceBetween size="xs">
              {files.map((file, index) => (
                <div
                  key={index}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e9ebed',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Icon name="file" />
                    <div>
                      <Box fontSize="body-s" fontWeight="bold">
                        {file.name}
                      </Box>
                      <Box fontSize="body-s" color="text-body-secondary">
                        {formatFileSize(file.size)}
                      </Box>
                    </div>
                  </div>
                  <Button
                    variant="icon"
                    iconName="close"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                  />
                </div>
              ))}
            </SpaceBetween>
          </Box>
        )}

        {/* Message Input */}
        <FormField>
          <Textarea
            value={message}
            onChange={({ detail }) => setMessage(detail.value)}
            onKeyDown={handleKeyPress}
            placeholder={t.chat.placeholder}
            disabled={disabled || isLoading}
            rows={3}
          />
        </FormField>

        {/* Send Button */}
        <Box float="right">
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={disabled || isLoading || (!message.trim() && files.length === 0)}
            loading={isLoading}
          >
            {t.chat.send}
          </Button>
        </Box>
      </SpaceBetween>
    </Box>
  );
}

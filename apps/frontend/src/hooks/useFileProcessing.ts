/**
 * Custom hook for managing file processing status
 * Handles status polling and notifications
 */

import { useState, useCallback, useEffect } from 'react';
import { useNotifications } from '../components/common/NotificationSystem';
import { FileProcessingStatus } from '../components/notifications/FileUploadStatus';


interface UseFileProcessingOptions {
  pollInterval?: number;
  onStatusChange?: (fileId: string, status: FileProcessingStatus) => void;
}

export const useFileProcessing = (options: UseFileProcessingOptions = {}) => {
  const { pollInterval = 2000, onStatusChange } = options;
  const { showInfo, showSuccess, showError } = useNotifications();
  const [processingFiles, setProcessingFiles] = useState<Map<string, FileProcessingStatus>>(
    new Map()
  );

  // Add a file to the processing queue
  const addFile = useCallback(
    (fileId: string, fileName: string) => {
      const newStatus: FileProcessingStatus = {
        fileId,
        fileName,
        status: 'uploading',
        progress: 0,
        startTime: new Date(),
      };

      setProcessingFiles((prev) => new Map(prev).set(fileId, newStatus));
      showInfo('Procesamiento iniciado', `Archivo: ${fileName}`);

      if (onStatusChange) {
        onStatusChange(fileId, newStatus);
      }

      return fileId;
    },
    [showInfo, onStatusChange]
  );

  // Update file processing status
  const updateFileStatus = useCallback(
    (
      fileId: string,
      updates: Partial<Omit<FileProcessingStatus, 'fileId' | 'fileName' | 'startTime'>>
    ) => {
      setProcessingFiles((prev) => {
        const current = prev.get(fileId);
        if (!current) return prev;

        const updated: FileProcessingStatus = {
          ...current,
          ...updates,
          endTime: updates.status === 'completed' || updates.status === 'failed' 
            ? new Date() 
            : current.endTime,
        };

        const newMap = new Map(prev);
        newMap.set(fileId, updated);

        // Show notifications for status changes
        if (updates.status === 'completed' && current.status !== 'completed') {
          showSuccess(
            'Procesamiento completado',
            `Archivo: ${current.fileName}`
          );
        } else if (updates.status === 'failed' && current.status !== 'failed') {
          showError(
            'Error en procesamiento',
            updates.error || `Archivo: ${current.fileName}`
          );
        }

        if (onStatusChange) {
          onStatusChange(fileId, updated);
        }

        return newMap;
      });
    },
    [showSuccess, showError, onStatusChange]
  );

  // Remove a file from the processing queue
  const removeFile = useCallback((fileId: string) => {
    setProcessingFiles((prev) => {
      const newMap = new Map(prev);
      newMap.delete(fileId);
      return newMap;
    });
  }, []);

  // Clear all completed or failed files
  const clearCompleted = useCallback(() => {
    setProcessingFiles((prev) => {
      const newMap = new Map(prev);
      for (const [fileId, status] of newMap.entries()) {
        if (status.status === 'completed' || status.status === 'failed') {
          newMap.delete(fileId);
        }
      }
      return newMap;
    });
  }, []);

  // Poll for status updates (placeholder for actual API integration)
  const pollFileStatus = useCallback(
    async (_fileId: string): Promise<FileProcessingStatus | null> => {
      // TODO: Implement actual API call to check file processing status
      // This is a placeholder that would be replaced with actual backend integration
      
      // Example API call structure:
      // const response = await fetch(`/api/files/${_fileId}/status`);
      // const data = await response.json();
      // return data;
      
      return null;
    },
    []
  );

  // Auto-poll for active files
  useEffect(() => {
    const activeFiles = Array.from(processingFiles.values()).filter(
      (file) => file.status === 'uploading' || file.status === 'processing'
    );

    if (activeFiles.length === 0) return;

    const interval = setInterval(async () => {
      for (const file of activeFiles) {
        const status = await pollFileStatus(file.fileId);
        if (status && status.fileId) {
          updateFileStatus(status.fileId, {
            status: status.status,
            progress: status.progress,
            stage: status.stage,
            error: status.error,
          });
        }
      }
    }, pollInterval);

    return () => clearInterval(interval);
  }, [processingFiles, pollInterval, pollFileStatus, updateFileStatus]);

  // Get files as array for rendering
  const files = Array.from(processingFiles.values());

  return {
    files,
    addFile,
    updateFileStatus,
    removeFile,
    clearCompleted,
    pollFileStatus,
  };
};

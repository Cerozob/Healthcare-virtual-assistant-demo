/**
 * FileUploadStatus component for tracking file processing status
 * Displays processing stages with progress indicators
 */

import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  ProgressBar,
  StatusIndicator,
  SpaceBetween,
  Box,
  Button,
} from '@cloudscape-design/components';
export interface FileProcessingStatus {
  fileId: string;
  fileName: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage?: string;
  error?: string;
  startTime: Date;
  endTime?: Date;
}

interface FileUploadStatusProps {
  files: FileProcessingStatus[];
  onRetry?: (fileId: string) => void;
  onCancel?: (fileId: string) => void;
  onDismiss?: (fileId: string) => void;
  pollInterval?: number; // milliseconds
}

const FileUploadStatus: React.FC<FileUploadStatusProps> = ({
  files,
  onRetry,
  onCancel,
  onDismiss,
  pollInterval = 2000,
}) => {
  const [pollingEnabled, setPollingEnabled] = useState(true);

  // Enable polling for files that are in progress
  useEffect(() => {
    if (!pollingEnabled) return;

    const hasActiveFiles = files.some(
      (file) => file.status === 'uploading' || file.status === 'processing'
    );

    if (!hasActiveFiles) {
      setPollingEnabled(false);
      return;
    }

    const interval = setInterval(() => {
      // Polling logic would trigger parent component to refresh status
      // This is a placeholder for the actual polling mechanism
    }, pollInterval);

    return () => clearInterval(interval);
  }, [files, pollingEnabled, pollInterval]);

  const getStatusIndicator = (status: FileProcessingStatus['status']) => {
    switch (status) {
      case 'uploading':
        return <StatusIndicator type="in-progress">Subiendo</StatusIndicator>;
      case 'processing':
        return <StatusIndicator type="in-progress">Procesando</StatusIndicator>;
      case 'completed':
        return <StatusIndicator type="success">Completado</StatusIndicator>;
      case 'failed':
        return <StatusIndicator type="error">Error</StatusIndicator>;
      default:
        return <StatusIndicator type="pending">Pendiente</StatusIndicator>;
    }
  };

  const getStageLabel = (status: FileProcessingStatus['status'], stage?: string) => {
    if (stage) return stage;
    
    switch (status) {
      case 'uploading':
        return 'Subiendo archivo al servidor';
      case 'processing':
        return 'Procesando contenido del archivo';
      case 'completed':
        return 'Procesamiento completado exitosamente';
      case 'failed':
        return 'Error durante el procesamiento';
      default:
        return 'Esperando';
    }
  };

  const formatDuration = (startTime: Date, endTime?: Date) => {
    const end = endTime || new Date();
    const duration = Math.floor((end.getTime() - startTime.getTime()) / 1000);
    
    if (duration < 60) {
      return `${duration}s`;
    }
    
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  if (files.length === 0) {
    return null;
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Estado del procesamiento de archivos"
        >
          Archivos en Proceso
        </Header>
      }
    >
      <SpaceBetween size="l">
        {files.map((file) => (
          <Box key={file.fileId} padding={{ vertical: 's' }}>
            <SpaceBetween size="s">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box variant="strong">{file.fileName}</Box>
                {getStatusIndicator(file.status)}
              </div>

              <Box variant="small" color="text-body-secondary">
                {getStageLabel(file.status, file.stage)}
              </Box>

              {(file.status === 'uploading' || file.status === 'processing') && (
                <ProgressBar
                  value={file.progress}
                  label="Progreso"
                  description={`${file.progress}% completado`}
                  variant="standalone"
                />
              )}

              {file.error && (
                <Box variant="small" color="text-status-error">
                  {file.error}
                </Box>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box variant="small" color="text-body-secondary">
                  Tiempo: {formatDuration(file.startTime, file.endTime)}
                </Box>

                <SpaceBetween size="xs" direction="horizontal">
                  {file.status === 'failed' && onRetry && (
                    <Button
                      variant="primary"
                      iconName="refresh"
                      onClick={() => onRetry(file.fileId)}
                    >
                      Reintentar
                    </Button>
                  )}

                  {(file.status === 'uploading' || file.status === 'processing') && onCancel && (
                    <Button
                      variant="normal"
                      onClick={() => onCancel(file.fileId)}
                    >
                      Cancelar
                    </Button>
                  )}

                  {(file.status === 'completed' || file.status === 'failed') && onDismiss && (
                    <Button
                      variant="normal"
                      iconName="close"
                      onClick={() => onDismiss(file.fileId)}
                    >
                      Cerrar
                    </Button>
                  )}
                </SpaceBetween>
              </div>
            </SpaceBetween>
          </Box>
        ))}
      </SpaceBetween>
    </Container>
  );
};

export default FileUploadStatus;

/**
 * FileSizeWarning Component
 * Shows warnings for large files to maintain performance
 */

import {
  Alert,
  Box,
  Button,
  SpaceBetween,
} from '@cloudscape-design/components';
import { FileTypeDetector } from '../../utils/fileTypeDetector';

export interface FileSizeWarningProps {
  fileName: string;
  fileSize: number;
  onProceed: () => void;
  onCancel: () => void;
}

export function FileSizeWarning({
  fileName,
  fileSize,
  onProceed,
  onCancel,
}: FileSizeWarningProps) {
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round(bytes / k ** i * 100) / 100} ${sizes[i]}`;
  };

  const getWarningLevel = (size: number): 'warning' | 'error' => {
    const previewConfig = FileTypeDetector.getPreviewConfig(fileName);
    const maxSize = previewConfig?.maxSize || 5 * 1024 * 1024; // 5MB default
    
    if (size > maxSize) {
      return 'error';
    } else if (size > maxSize * 0.8) { // 80% of max size
      return 'warning';
    }
    
    return 'warning';
  };

  const getWarningMessage = (size: number): string => {
    const previewConfig = FileTypeDetector.getPreviewConfig(fileName);
    const maxSize = previewConfig?.maxSize || 5 * 1024 * 1024;
    const maxSizeMB = Math.round(maxSize / (1024 * 1024));
    
    if (size > maxSize) {
      return `Este archivo (${formatFileSize(size)}) excede el tamaño máximo permitido para vista previa (${maxSizeMB}MB).`;
    } else if (size > maxSize * 0.8) {
      return `Este archivo es grande (${formatFileSize(size)}) y puede tardar en cargar.`;
    }
    
    return `El archivo ${formatFileSize(size)} puede afectar el rendimiento.`;
  };

  const getRecommendation = (size: number): string => {
    const previewConfig = FileTypeDetector.getPreviewConfig(fileName);
    const maxSize = previewConfig?.maxSize || 5 * 1024 * 1024;
    
    if (size > maxSize) {
      return 'Se recomienda descargar el archivo para verlo en una aplicación externa.';
    } else if (size > 10 * 1024 * 1024) { // 10MB
      return 'Para archivos grandes, considere descargar el archivo si la vista previa es lenta.';
    }
    
    return 'La vista previa puede tardar unos segundos en cargar.';
  };

  const warningLevel = getWarningLevel(fileSize);
  const canProceed = fileSize <= (FileTypeDetector.getPreviewConfig(fileName)?.maxSize || 5 * 1024 * 1024);

  return (
    <Alert
      type={warningLevel}
      header={canProceed ? 'Archivo grande detectado' : 'Archivo demasiado grande'}
      action={
        <SpaceBetween direction="horizontal" size="xs">
          <Button variant="link" onClick={onCancel}>
            Cancelar
          </Button>
          {canProceed && (
            <Button variant="primary" onClick={onProceed}>
              Continuar con vista previa
            </Button>
          )}
        </SpaceBetween>
      }
    >
      <SpaceBetween size="s">
        <Box>
          <strong>Archivo:</strong> {fileName}
        </Box>
        <Box>
          {getWarningMessage(fileSize)}
        </Box>
        <Box>
          {getRecommendation(fileSize)}
        </Box>
        {!canProceed && (
          <Box color="text-status-error">
            <strong>Acción requerida:</strong> Use la opción de descarga para acceder al archivo.
          </Box>
        )}
      </SpaceBetween>
    </Alert>
  );
}

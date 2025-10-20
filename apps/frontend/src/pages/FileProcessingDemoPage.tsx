/**
 * Demo page for file processing notifications
 * This demonstrates how to use the NotificationCenter and FileUploadStatus components
 */

import React, { useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Box,
} from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import FileUploadStatus from '../components/notifications/FileUploadStatus';
import { useNotifications } from '../contexts/NotificationContext';
import { useFileProcessing } from '../hooks/useFileProcessing';

interface FileProcessingDemoPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

const FileProcessingDemoPage: React.FC<FileProcessingDemoPageProps> = ({ signOut, user }) => {
  const { showSuccess, showError, showWarning, showInfo } = useNotifications();
  const { files, addFile, updateFileStatus, removeFile, clearCompleted } = useFileProcessing();
  const [testFileName, setTestFileName] = useState('test-document.pdf');

  // Simulate file upload
  const handleSimulateUpload = () => {
    const fileId = `file-${Date.now()}`;
    addFile(fileId, testFileName);

    // Simulate upload progress
    let progress = 0;
    const uploadInterval = setInterval(() => {
      progress += 10;
      updateFileStatus(fileId, {
        status: 'uploading',
        progress,
      });

      if (progress >= 100) {
        clearInterval(uploadInterval);
        // Start processing
        handleSimulateProcessing(fileId);
      }
    }, 300);
  };

  // Simulate file processing
  const handleSimulateProcessing = (fileId: string) => {
    updateFileStatus(fileId, {
      status: 'processing',
      progress: 0,
      stage: 'Extrayendo texto del documento',
    });

    let progress = 0;
    const stages = [
      'Extrayendo texto del documento',
      'Analizando contenido médico',
      'Identificando entidades clínicas',
      'Generando resumen',
    ];
    let stageIndex = 0;

    const processingInterval = setInterval(() => {
      progress += 5;
      
      if (progress % 25 === 0 && stageIndex < stages.length - 1) {
        stageIndex++;
      }

      updateFileStatus(fileId, {
        status: 'processing',
        progress,
        stage: stages[stageIndex],
      });

      if (progress >= 100) {
        clearInterval(processingInterval);
        updateFileStatus(fileId, {
          status: 'completed',
          progress: 100,
        });
      }
    }, 200);
  };

  // Simulate file processing failure
  const handleSimulateFailure = () => {
    const fileId = `file-${Date.now()}`;
    addFile(fileId, 'error-document.pdf');

    setTimeout(() => {
      updateFileStatus(fileId, {
        status: 'failed',
        progress: 45,
        error: 'No se pudo procesar el archivo. Formato no compatible.',
      });
    }, 2000);
  };

  // Test different notification types
  const handleTestNotifications = () => {
    showSuccess('Operación exitosa', 'El archivo se procesó correctamente');
    
    setTimeout(() => {
      showInfo('Información', 'Este es un mensaje informativo');
    }, 500);
    
    setTimeout(() => {
      showWarning('Advertencia', 'El archivo es muy grande y puede tardar más tiempo');
    }, 1000);
    
    setTimeout(() => {
      showError('Error', 'No se pudo conectar con el servidor');
    }, 1500);
  };

  const handleRetry = (fileId: string) => {
    updateFileStatus(fileId, {
      status: 'uploading',
      progress: 0,
      error: undefined,
    });
    handleSimulateProcessing(fileId);
  };

  const handleCancel = (fileId: string) => {
    removeFile(fileId);
    showInfo('Cancelado', 'Procesamiento de archivo cancelado');
  };

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Container
          header={
            <Header
              variant="h1"
              description="Demostración del sistema de notificaciones y seguimiento de procesamiento de archivos"
            >
              Demo de Procesamiento de Archivos
            </Header>
          }
        >
          <SpaceBetween size="m">
            <Box variant="p">
              Esta página demuestra el sistema de notificaciones y seguimiento de estado de procesamiento de archivos.
              Use los botones a continuación para simular diferentes escenarios.
            </Box>

            <FormField label="Nombre del archivo de prueba">
              <Input
                value={testFileName}
                onChange={({ detail }) => setTestFileName(detail.value)}
                placeholder="Ingrese el nombre del archivo"
              />
            </FormField>

            <SpaceBetween size="s" direction="horizontal">
              <Button variant="primary" onClick={handleSimulateUpload}>
                Simular Carga Exitosa
              </Button>
              <Button onClick={handleSimulateFailure}>
                Simular Error
              </Button>
              <Button onClick={handleTestNotifications}>
                Probar Notificaciones
              </Button>
              <Button onClick={clearCompleted}>
                Limpiar Completados
              </Button>
            </SpaceBetween>
          </SpaceBetween>
        </Container>

        {files.length > 0 && (
          <FileUploadStatus
            files={files}
            onRetry={handleRetry}
            onCancel={handleCancel}
            onDismiss={removeFile}
          />
        )}

        <Container
          header={
            <Header variant="h2">
              Instrucciones de Uso
            </Header>
          }
        >
          <SpaceBetween size="s">
            <Box variant="h3">NotificationCenter</Box>
            <Box variant="p">
              El NotificationCenter muestra notificaciones toast en la esquina superior derecha.
              Las notificaciones se descartan automáticamente después de 5 segundos (excepto los errores).
            </Box>

            <Box variant="h3">FileUploadStatus</Box>
            <Box variant="p">
              El componente FileUploadStatus muestra el progreso de procesamiento de archivos con:
            </Box>
            <ul>
              <li>Indicadores de estado (Subiendo, Procesando, Completado, Error)</li>
              <li>Barras de progreso para operaciones en curso</li>
              <li>Etapas de procesamiento descriptivas</li>
              <li>Botones de acción (Reintentar, Cancelar, Cerrar)</li>
              <li>Duración del procesamiento</li>
            </ul>

            <Box variant="h3">Integración en Código</Box>
            <Box variant="code">
              {`// Usar el hook useNotifications
const { showSuccess, showError } = useNotifications();

// Usar el hook useFileProcessing
const { files, addFile, updateFileStatus } = useFileProcessing();

// Agregar un archivo
const fileId = addFile('file-123', 'documento.pdf');

// Actualizar estado
updateFileStatus(fileId, {
  status: 'processing',
  progress: 50,
  stage: 'Analizando contenido'
});`}
            </Box>
          </SpaceBetween>
        </Container>
      </SpaceBetween>
    </MainLayout>
  );
};

export default FileProcessingDemoPage;

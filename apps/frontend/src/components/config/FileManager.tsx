/**
 * FileManager Component
 * Interface for managing patient files with upload and download capabilities
 * Enhanced with unified file display and preview functionality
 */

import {
  Alert,
  Badge,
  Box,
  Button,
  Container,
  FileUpload,
  FormField,
  Header,
  Modal,
  ProgressBar,
  Select,
  type SelectProps,
  SpaceBetween,
  Table,
} from '@cloudscape-design/components';
import { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { processedFileService } from '../../services/processedFileService';
import { FilePreviewModal } from './FilePreviewModal';
import type { ProcessedFile } from './ProcessedFileManager';
import type { UnifiedFile } from '../../types/unifiedFile';
import { ErrorHandler } from '../../utils/errorHandler';
import { useFileOperationNotifications } from '../common/NotificationSystem';
import { FileOperationErrorBoundary } from '../common/ErrorBoundary';


export interface PatientFile {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadDate: string;
  category?: string;
  url?: string;
  autoClassified?: boolean;
  classificationConfidence?: number;
  originalClassification?: string;
}

export interface FileManagerProps {
  patientId?: string;
  files: PatientFile[];
  loading?: boolean;
  onUpload: (file: File, category: string, patientId?: string) => Promise<void>;
  onDownload: (file: PatientFile) => void;
  onDelete: (fileId: string) => Promise<void>;
  onRefresh?: () => Promise<void>;
  onClassificationOverride?: (fileId: string, newCategory: string) => Promise<void>;
  onPatientChange?: (patientId: string) => Promise<void>;
  patients?: Array<{ patient_id: string; full_name: string }>;
  enableAutoClassification?: boolean;
}

const fileCategoryOptions: SelectProps.Option[] = [
  { label: 'Clasificación automática', value: 'auto' },
  { label: 'Historia clínica', value: 'medical-history' },
  { label: 'Resultados de exámenes', value: 'exam-results' },
  { label: 'Imágenes médicas', value: 'medical-images' },
  { label: 'Documentos de identidad', value: 'identification' },
  { label: 'Otros', value: 'other' },
  { label: 'No identificado', value: 'not-identified' },
];

export function FileManager({
  patientId,
  files,
  loading = false,
  onUpload,
  onDownload,
  onDelete,
  onRefresh,
  onClassificationOverride,
  onPatientChange,
  patients = [],
  enableAutoClassification = true,
}: FileManagerProps) {
  const { t } = useLanguage();
  const notifications = useFileOperationNotifications();
  const [selectedPatient, setSelectedPatient] = useState<string>(patientId || '');
  const [selectedCategory, setSelectedCategory] = useState<SelectProps.Option | null>(fileCategoryOptions[0]); // Default to "auto"
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentUploadFile, setCurrentUploadFile] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [selectedTableItems, setSelectedTableItems] = useState<PatientFile[]>([]);
  const [classificationProcessing, setClassificationProcessing] = useState<Set<string>>(new Set());
  const [editingClassification, setEditingClassification] = useState<string | null>(null);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [deletingFiles, setDeletingFiles] = useState(false);

  // Processed files state
  const [processedFiles, setProcessedFiles] = useState<ProcessedFile[]>([]);
  const [loadingProcessedFiles, setLoadingProcessedFiles] = useState(false);
  const [processedFilesError, setProcessedFilesError] = useState<string>('');



  // Preview modal state
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewFile, setPreviewFile] = useState<UnifiedFile | null>(null);

  const patientOptions: SelectProps.Option[] = patients.map((p) => ({
    label: `${p.full_name} (${p.patient_id})`,
    value: p.patient_id,
  }));

  const selectedPatientOption = patientOptions.find((opt) => opt.value === selectedPatient) || null;

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Por favor seleccione un archivo');
      return;
    }

    if (!selectedPatient) {
      setError('Por favor seleccione un paciente');
      return;
    }

    setUploading(true);
    setError('');
    setUploadProgress(0);

    try {
      const patientData = patients.find(p => p.patient_id === selectedPatient);
      const patientName = patientData?.full_name || selectedPatient;

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setCurrentUploadFile(file.name);

        console.log(`Uploading file ${file.name} for patient ${patientName} following document workflow guidelines`);

        try {
          // Call the upload handler with patient context
          await onUpload(file, selectedCategory?.value || 'auto', selectedPatient);

          // Show individual file success notification
          notifications.notifyFileUploadSuccess(file.name, patientName);

        } catch (fileError) {
          const errorDetails = ErrorHandler.getErrorDetails(fileError, `Subida de ${file.name}`);
          notifications.notifyFileUploadError(file.name, errorDetails.userMessage);
          
          // Continue with other files but log the error
          console.error(`Failed to upload ${file.name}:`, errorDetails);
        }

        // Update overall progress
        const overallProgress = ((i + 1) / selectedFiles.length) * 100;
        setUploadProgress(overallProgress);
      }

      setSelectedFiles([]);
      setUploadProgress(0);
      setCurrentUploadFile('');

      // Show overall success message
      const message = selectedFiles.length === 1 
        ? `Archivo subido exitosamente para ${patientName}.`
        : `${selectedFiles.length} archivos procesados para ${patientName}.`;
      
      setSuccessMessage(`${message} Los documentos han sido almacenados en S3 y serán procesados automáticamente según las pautas del flujo de trabajo de documentos.`);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);

    } catch (err) {
      const errorDetails = ErrorHandler.getErrorDetails(err, 'Subida de archivos');
      setError(errorDetails.userMessage);
      notifications.notifyFileUploadError('archivos seleccionados', errorDetails.userMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteClick = () => {
    if (selectedTableItems.length === 0) return;
    setShowDeleteConfirmation(true);
  };

  const handleDeleteConfirm = async () => {
    if (selectedTableItems.length === 0) return;

    setDeletingFiles(true);
    setError('');
    setSuccessMessage('');


    let deletedFiles: string[] = [];
    let failedFiles: string[] = [];

    try {
      console.log(`Deleting ${selectedTableItems.length} files...`);

      for (const file of selectedTableItems) {
        try {
          console.log(`Deleting file: ${file.name} (ID: ${file.id})`);
          await onDelete(file.id);
          deletedFiles.push(file.name);
        } catch (fileError) {
          const errorDetails = ErrorHandler.getErrorDetails(fileError, `Eliminación de ${file.name}`);
          failedFiles.push(file.name);
          console.error(`Failed to delete ${file.name}:`, errorDetails);
        }
      }

      setSelectedTableItems([]);
      setShowDeleteConfirmation(false);

      // Show appropriate notifications
      if (deletedFiles.length > 0) {
        notifications.notifyFileDeleteSuccess(deletedFiles);
        
        const message = deletedFiles.length === 1
          ? `Archivo "${deletedFiles[0]}" eliminado exitosamente`
          : `${deletedFiles.length} archivos eliminados exitosamente`;
        setSuccessMessage(message);
        setTimeout(() => setSuccessMessage(''), 5000);
      }

      if (failedFiles.length > 0) {
        const errorMessage = failedFiles.length === 1
          ? `No se pudo eliminar el archivo "${failedFiles[0]}"`
          : `No se pudieron eliminar ${failedFiles.length} archivos: ${failedFiles.join(', ')}`;
        
        notifications.notifyFileDeleteError(errorMessage);
        setError(errorMessage);
      }

    } catch (err) {
      const errorDetails = ErrorHandler.getErrorDetails(err, 'Eliminación de archivos');
      setError(errorDetails.userMessage);
      notifications.notifyFileDeleteError(errorDetails.userMessage);
      console.error('File deletion error:', err);
    } finally {
      setDeletingFiles(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirmation(false);
  };

  const handlePatientSelectionChange = async (newPatientId: string) => {
    setSelectedPatient(newPatientId);
    setProcessedFiles([]);

    if (onPatientChange) {
      try {
        await onPatientChange(newPatientId);
      } catch (error) {
        console.error('Error changing patient filter:', error);
        setError('Error al cambiar el filtro de paciente');
      }
    }
  };

  // Load all processed files for the selected patient
  const loadAllProcessedFiles = useCallback(async () => {
    if (!selectedPatient) {
      setProcessedFiles([]);
      return;
    }

    setLoadingProcessedFiles(true);
    setProcessedFilesError('');

    try {
      const allProcessedFiles = await processedFileService.getProcessedFiles(selectedPatient);
      setProcessedFiles(allProcessedFiles);
      console.log(`Loaded ${allProcessedFiles.length} processed files for patient: ${selectedPatient}`);
    } catch (error) {
      console.error('Error loading processed files:', error);
      setProcessedFilesError(error instanceof Error ? error.message : 'Error loading processed files');
    } finally {
      setLoadingProcessedFiles(false);
    }
  }, [selectedPatient]);

  // Load processed files when patient changes
  useEffect(() => {
    loadAllProcessedFiles();
  }, [loadAllProcessedFiles]);

  // Handle processed file download
  const handleProcessedFileDownload = async (processedFile: ProcessedFile) => {
    try {
      console.log(`Starting download for processed file: ${processedFile.name}`);
      
      const blob = await processedFileService.downloadProcessedFile(processedFile);
      console.log(`Blob received, size: ${blob.size} bytes, type: ${blob.type}`);

      // Create and trigger download - simplified approach
      const url = URL.createObjectURL(blob);
      
      // Create a temporary link element
      const link = document.createElement('a');
      link.href = url;
      link.download = processedFile.name;
      
      // Add to DOM, click, and remove
      document.body.appendChild(link);
      console.log('Processed file: Link created and added to DOM, triggering click...');
      link.click();
      console.log('Processed file: Click triggered, removing link...');
      document.body.removeChild(link);
      
      // Clean up the blob URL after a delay
      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 1000);

      notifications.notifyFileDownloadSuccess(processedFile.name);
      console.log(`Download completed for processed file: ${processedFile.name}`);
    } catch (error) {
      console.error('Error downloading processed file:', error);
      const errorDetails = ErrorHandler.getErrorDetails(error, 'Descarga de archivo procesado');
      setError(errorDetails.userMessage);
      notifications.notifyFileDownloadError(processedFile.name, errorDetails.userMessage);
    }
  };

  // Handle unified file download
  const handleUnifiedFileDownload = async (unifiedFile: UnifiedFile) => {
    try {
      console.log(`Starting download for: ${unifiedFile.name}`);
      
      const blob = await processedFileService.downloadUnifiedFile(unifiedFile);
      console.log(`Blob received, size: ${blob.size} bytes, type: ${blob.type}`);

      // Create and trigger download - simplified approach
      const url = URL.createObjectURL(blob);
      console.log('Unified file: Blob URL created:', url);
      
      // Create a temporary link element
      const link = document.createElement('a');
      link.href = url;
      link.download = unifiedFile.name;
      console.log('Unified file: Link configured with href:', link.href, 'download:', link.download);
      
      // Add to DOM, click, and remove
      document.body.appendChild(link);
      console.log('Unified file: Link created and added to DOM, triggering click...');
      link.click();
      console.log('Unified file: Click triggered, removing link...');
      document.body.removeChild(link);
      
      // Clean up the blob URL after a delay
      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 1000);

      notifications.notifyFileDownloadSuccess(unifiedFile.name);
      console.log(`Download completed for: ${unifiedFile.name} from ${unifiedFile.source} bucket`);
    } catch (error) {
      console.error('Error downloading unified file:', error);
      const errorDetails = ErrorHandler.getErrorDetails(error, 'Descarga de archivo');
      setError(errorDetails.userMessage);
      notifications.notifyFileDownloadError(unifiedFile.name, errorDetails.userMessage);
    }
  };

  // Handle preview modal
  const handlePreviewFile = (file: UnifiedFile) => {
    if (!file.preview.previewSupported) {
      notifications.notifyUnsupportedFileType(file.name, file.type, () => handleUnifiedFileDownload(file));
      return;
    }
    
    setPreviewFile(file);
    setPreviewModalVisible(true);
  };

  const handlePreviewModalClose = () => {
    setPreviewModalVisible(false);
    setPreviewFile(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round(bytes / k ** i * 100) / 100} ${sizes[i]}`;
  };

  const getCategoryLabel = (category?: string): string => {
    // Show "pending" for auto classification that hasn't been processed yet
    if (category === 'auto') {
      return 'Pendiente de clasificación';
    }

    const option = fileCategoryOptions.find((opt) => opt.value === category);
    return option?.label || 'Sin categoría';
  };

  const handleClassificationOverride = async (fileId: string, newCategory: string) => {
    if (!onClassificationOverride) return;

    setClassificationProcessing(prev => new Set(prev).add(fileId));
    setError('');

    try {
      await onClassificationOverride(fileId, newCategory);
      setEditingClassification(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar clasificación');
    } finally {
      setClassificationProcessing(prev => {
        const newSet = new Set(prev);
        newSet.delete(fileId);
        return newSet;
      });
    }
  };

  // Get badge color based on category and status
  const getCategoryBadgeColor = (category?: string, isProcessing?: boolean, isAutoClassified?: boolean) => {
    if (isProcessing || category === 'auto') {
      return 'severity-medium'; // Orange for processing
    }
    
    if (category === 'not-identified') {
      return 'red'; // Red for unidentified
    }
    
    switch (category) {
      case 'medical-history':
        return 'blue'; // Blue for medical history
      case 'exam-results':
        return 'green'; // Green for exam results
      case 'medical-images':
        return 'severity-low'; // Yellow for medical images
      case 'prescriptions':
        return 'severity-high'; // Salmon for prescriptions
      case 'insurance':
        return 'severity-neutral'; // Grey for insurance
      case 'other':
        return isAutoClassified ? 'blue' : 'grey'; // Blue if auto-classified, grey otherwise
      default:
        return 'grey'; // Default grey
    }
  };

  const renderCategoryCell = (item: PatientFile) => {
    const isProcessing = classificationProcessing.has(item.id);
    const isEditing = editingClassification === item.id;
    const isAutoClassified = item.autoClassified;
    const isNotIdentified = item.category === 'not-identified';
    const isPending = item.category === 'auto';

    if (isEditing && onClassificationOverride) {
      return (
        <Select
          selectedOption={fileCategoryOptions.find(opt => opt.value === item.category) || null}
          onChange={({ detail }) => {
            if (detail.selectedOption.value) {
              handleClassificationOverride(item.id, detail.selectedOption.value);
            }
          }}
          options={fileCategoryOptions}
          placeholder="Seleccionar categoría"
          disabled={isProcessing}
          autoFocus
        />
      );
    }

    return (
      <Box>
        <Badge
          color={getCategoryBadgeColor(item.category, isProcessing || isPending, isAutoClassified)}
        >
          {getCategoryLabel(item.category)}
        </Badge>
        {isPending && (
          <Box fontSize="body-s" color="text-status-info" margin={{ top: 'xxxs' }}>
            Procesando con IA...
          </Box>
        )}
        {isAutoClassified && !isPending && (
          <Box fontSize="body-s" color="text-status-info" margin={{ top: 'xxxs' }}>
            Auto-clasificado ({item.classificationConfidence?.toFixed(0)}% confianza)
          </Box>
        )}
        {isNotIdentified && (
          <Box fontSize="body-s" color="text-status-warning" margin={{ top: 'xxxs' }}>
            Requiere clasificación manual
          </Box>
        )}
      </Box>
    );
  };

  return (
    <FileOperationErrorBoundary>
    <SpaceBetween size="l">
      {error && (
        <Alert type="error" dismissible onDismiss={() => setError('')}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert type="success" dismissible onDismiss={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      )}

      {/* Patient Filter Section */}
      <Container header={<Header variant="h2">Filtrar archivos por paciente</Header>}>

        <FormField label="Paciente" constraintText="Seleccione el paciente para asociar los archivos y para filtrar datos">
          <Select
            selectedOption={selectedPatientOption}
            onChange={({ detail }) => handlePatientSelectionChange(detail.selectedOption.value || '')}
            options={patientOptions}
            placeholder="Seleccione un paciente"
            disabled={uploading}
            filteringType="auto"
          />
        </FormField>
      </Container>

      <Container header={<Header variant="h2">Subir archivos</Header>}>
        <SpaceBetween size="m">

          <FormField
            label="Categoría"
            constraintText="La clasificación automática analizará el contenido del documento para determinar su tipo"
            info="Recomendado: Use 'Clasificación automática' para mejor precisión"
          >
            <Select
              selectedOption={selectedCategory}
              onChange={({ detail }) => setSelectedCategory(detail.selectedOption)}
              options={fileCategoryOptions}
              disabled={uploading}
            />
          </FormField>

          <FormField
            label="Archivo"
            constraintText="Seleccione uno o más archivos para subir"
            description={`${t.fileUpload.supportedFormats}: PDF, TIFF, JPEG, PNG, DOCX, MP4, MOV, AVI, MKV, WEBM, AMR, FLAC, M4A, MP3, Ogg, WAV`}
          >
            <FileUpload
              value={selectedFiles}
              onChange={({ detail }) => setSelectedFiles(detail.value)}
              multiple
              i18nStrings={{
                uploadButtonText: (e) => (e ? 'Elegir archivos' : 'Elegir archivo'),
                dropzoneText: (e) => (e ? 'Arrastre archivos aquí' : 'Arrastre un archivo aquí'),
                removeFileAriaLabel: (e) => `Eliminar archivo ${e + 1}`,
                limitShowFewer: 'Mostrar menos archivos',
                limitShowMore: 'Mostrar más archivos',
                errorIconAriaLabel: 'Error',
              }}
            />
          </FormField>

          {uploading && (
            <ProgressBar
              value={uploadProgress}
              label="Subiendo archivos a S3"
              description={currentUploadFile ? `Subiendo: ${currentUploadFile} (${Math.round(uploadProgress)}% completado)` : `${Math.round(uploadProgress)}% completado`}
            />
          )}

          {enableAutoClassification && selectedCategory?.value === 'auto' && (
            <Alert type="info" dismissible={false}>
              <strong>Clasificación automática habilitada:</strong> Los archivos serán analizados por IA para determinar automáticamente su categoría (Historia clínica, Resultados de exámenes, Imágenes médicas, etc.). Puedes editar la clasificación después si es necesario.
            </Alert>
          )}

          <Box float="right">
            <Button variant="primary" onClick={handleUpload} loading={uploading} disabled={!selectedPatient}>
              Subir archivos
            </Button>
          </Box>
        </SpaceBetween>
      </Container>

      <Table
        columnDefinitions={[
          {
            id: 'name',
            header: 'Nombre',
            cell: (item) => item.name,
            sortingField: 'name',
          },
          {
            id: 'category',
            header: 'Categoría',
            cell: renderCategoryCell,
          },
          {
            id: 'type',
            header: 'Tipo',
            cell: (item) => item.type,
          },
          {
            id: 'size',
            header: 'Tamaño',
            cell: (item) => formatFileSize(item.size),
          },
          {
            id: 'uploadDate',
            header: 'Fecha de subida',
            cell: (item) => new Date(item.uploadDate).toLocaleDateString('es-MX'),
            sortingField: 'uploadDate',
          },
          {
            id: 'actions',
            header: 'Acciones',
            cell: (item) => {
              // Convert PatientFile to UnifiedFile for preview
              const unifiedFile = processedFileService.convertPatientFilesToUnified([item], selectedPatient)[0];
              
              return (
                <SpaceBetween direction="horizontal" size="xs">
                  {unifiedFile?.preview.previewSupported && (
                    <Button
                      iconName="search"
                      variant="inline-icon"
                      onClick={() => handlePreviewFile(unifiedFile)}
                    >
                      Vista previa
                    </Button>
                  )}
                  <Button iconName="download" variant="inline-icon" onClick={() => onDownload(item)}>
                    Descargar
                  </Button>
                  {onClassificationOverride && (
                    <Button
                      iconName="edit"
                      variant="inline-icon"
                      onClick={() => setEditingClassification(item.id)}
                      disabled={classificationProcessing.has(item.id)}
                    >
                      Editar categoría
                    </Button>
                  )}
                </SpaceBetween>
              );
            },
          },
        ]}
        items={files}
        loading={loading}
        loadingText={t.common.loading}
        selectionType="multi"
        selectedItems={selectedTableItems}
        onSelectionChange={({ detail }) => setSelectedTableItems(detail.selectedItems)}
        trackBy="id"
        empty={
          <Box textAlign="center" color="inherit">
            <b>No hay archivos</b>
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              {selectedPatient ? 'No se encontraron archivos para este paciente' : 'Seleccione un paciente para ver sus archivos'}
            </Box>
          </Box>
        }
        header={
          <Header
            variant="h2"
            counter={`(${files.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                {onRefresh && (
                  <Button iconName="refresh" onClick={onRefresh} disabled={loading}>
                    Actualizar archivos
                  </Button>
                )}
                <Button
                  onClick={handleDeleteClick}
                  disabled={selectedTableItems.length === 0}
                  loading={deletingFiles}
                >
                  {t.common.delete}
                </Button>
              </SpaceBetween>
            }
          >
            Archivos del paciente
          </Header>
        }
      />

      {/* Processed Files Table - Always visible */}
      {processedFilesError && (
        <Alert type="error" dismissible onDismiss={() => setProcessedFilesError('')}>
          {processedFilesError}
        </Alert>
      )}

      <Table
        columnDefinitions={[
          {
            id: 'name',
            header: 'Archivo procesado',
            cell: (item) => item.name,
            sortingField: 'name',
          },
          {
            id: 'documentId',
            header: 'Documento original',
            cell: (item) => item.documentId || 'N/A',
          },
          {
            id: 'category',
            header: 'Categoría detectada',
            cell: (item) => (
              <Badge color={getCategoryBadgeColor(item.category, false, item.autoClassified)}>
                {item.category === 'medical-history' ? 'Historia clínica' :
                  item.category === 'exam-results' ? 'Resultados de exámenes' :
                    item.category === 'medical-images' ? 'Imágenes médicas' :
                      item.category === 'identification' ? 'Documentos de identidad' :
                        item.category === 'not-identified' ? 'No identificado' :
                          'Otros'}
              </Badge>
            ),
          },
          {
            id: 'confidence',
            header: 'Confianza',
            cell: (item) => item.confidence ? `${item.confidence.toFixed(1)}%` : 'N/A',
          },
          {
            id: 'processedDate',
            header: 'Fecha de procesamiento',
            cell: (item) => new Date(item.processedDate).toLocaleDateString('es-MX'),
            sortingField: 'processedDate',
          },
          {
            id: 'actions',
            header: 'Acciones',
            cell: (item) => {
              // Convert ProcessedFile to UnifiedFile for preview
              const unifiedFile = processedFileService.convertProcessedFilesToUnified([item])[0];
              
              return (
                <SpaceBetween direction="horizontal" size="xs">
                  {unifiedFile?.preview.previewSupported && (
                    <Button
                      iconName="search"
                      variant="inline-icon"
                      onClick={() => handlePreviewFile(unifiedFile)}
                    >
                      Vista previa
                    </Button>
                  )}
                  <Button
                    iconName="download"
                    variant="inline-icon"
                    onClick={() => handleProcessedFileDownload(item)}
                  >
                    Descargar
                  </Button>
                </SpaceBetween>
              );
            },
          },
        ]}
        items={processedFiles}
        loading={loadingProcessedFiles}
        loadingText="Cargando archivos procesados..."
        trackBy="id"
        empty={
          <Box textAlign="center" color="inherit">
            <b>No hay archivos procesados</b>
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              {selectedPatient
                ? 'Los archivos subidos serán procesados automáticamente por IA. Los resultados aparecerán aquí una vez completado el procesamiento.'
                : 'Seleccione un paciente para ver sus archivos procesados'}
            </Box>
          </Box>
        }
        header={
          <Header
            variant="h2"
            counter={`(${processedFiles.length})`}
            actions={
              <Button
                iconName="refresh"
                onClick={loadAllProcessedFiles}
                disabled={loadingProcessedFiles}
              >
                Actualizar
              </Button>
            }
          >
            Archivos procesados por IA
          </Header>
        }
      />



      {/* File Preview Modal */}
      <FilePreviewModal
        visible={previewModalVisible}
        file={previewFile}
        onDismiss={handlePreviewModalClose}
        onDownload={handleUnifiedFileDownload}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        visible={showDeleteConfirmation}
        onDismiss={handleDeleteCancel}
        header="Confirmar eliminación"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={handleDeleteCancel}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={handleDeleteConfirm}
                loading={deletingFiles}
              >
                Eliminar
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Alert type="warning">
            <strong>¿Está seguro que desea eliminar los siguientes archivos?</strong>
          </Alert>

          <Box>
            <strong>Archivos a eliminar:</strong>
            <ul>
              {selectedTableItems.map((file) => (
                <li key={file.id}>
                  <strong>{file.name}</strong> ({formatFileSize(file.size)})
                  {file.category && (
                    <span> - {getCategoryLabel(file.category)}</span>
                  )}
                </li>
              ))}
            </ul>
          </Box>

          <Alert type="error">
            <strong>Esta acción no se puede deshacer.</strong> Los archivos serán eliminados permanentemente del sistema de almacenamiento.
          </Alert>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
    </FileOperationErrorBoundary>
  );
}

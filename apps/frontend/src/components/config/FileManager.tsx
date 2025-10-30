/**
 * FileManager Component
 * Interface for managing patient files with upload and download capabilities
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
import type { ProcessedFile } from './ProcessedFileManager';

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

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setCurrentUploadFile(file.name);

        console.log(`Uploading file ${file.name} for patient ${patientData?.full_name || selectedPatient} following document workflow guidelines`);

        // Call the upload handler with patient context
        await onUpload(file, selectedCategory?.value || 'auto', selectedPatient);

        // Update overall progress
        const overallProgress = ((i + 1) / selectedFiles.length) * 100;
        setUploadProgress(overallProgress);
      }

      setSelectedFiles([]);
      setUploadProgress(0);
      setCurrentUploadFile('');

      // Show success message with workflow information
      setSuccessMessage(`Archivos subidos exitosamente para ${patientData?.full_name || selectedPatient}. Los documentos han sido almacenados en S3 y serán procesados automáticamente según las pautas del flujo de trabajo de documentos.`);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir archivo');
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

    try {
      console.log(`Deleting ${selectedTableItems.length} files...`);

      for (const file of selectedTableItems) {
        console.log(`Deleting file: ${file.name} (ID: ${file.id})`);
        await onDelete(file.id);
      }

      setSelectedTableItems([]);
      setShowDeleteConfirmation(false);

      // Show success message
      const fileCount = selectedTableItems.length;
      const message = fileCount === 1
        ? `Archivo "${selectedTableItems[0].name}" eliminado exitosamente`
        : `${fileCount} archivos eliminados exitosamente`;

      setSuccessMessage(message);

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al eliminar archivo(s)';
      setError(errorMessage);
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
      const blob = await processedFileService.downloadProcessedFile(processedFile);

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = processedFile.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log(`Downloaded processed file: ${processedFile.name}`);
    } catch (error) {
      console.error('Error downloading processed file:', error);
      setError(error instanceof Error ? error.message : 'Error downloading processed file');
    }
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
          color={isPending ? 'grey' : isNotIdentified ? 'red' : isAutoClassified ? 'blue' : 'grey'}
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
            cell: (item) => (
              <SpaceBetween direction="horizontal" size="xs">
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
            ),
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
              <Badge color={item.category === 'not-identified' ? 'red' : 'blue'}>
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
            cell: (item) => (
              <Button
                iconName="download"
                variant="inline-icon"
                onClick={() => handleProcessedFileDownload(item)}
              >
                Descargar
              </Button>
            ),
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
  );
}

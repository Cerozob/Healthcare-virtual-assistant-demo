/**
 * ProcessedFileManager Component
 * Interface for viewing processed files from the document processing workflow
 */

import {
  Alert,
  Badge,
  Box,
  Button,
  Container,
  FormField,
  Header,
  Modal,
  Select,
  type SelectProps,
  SpaceBetween,
  Table,
  Tabs,
} from '@cloudscape-design/components';
import { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

export interface ProcessedFile {
  id: string;
  name: string;
  type: string;
  size: number;
  processedDate: string;
  category?: string;
  confidence?: number;
  originalClassification?: string;
  autoClassified?: boolean;
  patientId?: string;
  documentId?: string;
  url?: string;
  extractedData?: any;
  bdaMetadata?: any;
}

export interface ProcessedFileManagerProps {
  patientId?: string;
  processedFiles: ProcessedFile[];
  loading?: boolean;
  onDownload: (file: ProcessedFile) => void;
  onRefresh?: () => Promise<void>;
  onPatientChange?: (patientId: string) => Promise<void>;
  patients?: Array<{ patient_id: string; full_name: string }>;
}

export function ProcessedFileManager({
  patientId,
  processedFiles,
  loading = false,
  onDownload,
  onRefresh,
  onPatientChange,
  patients = [],
}: ProcessedFileManagerProps) {
  const { t } = useLanguage();
  const [selectedPatient, setSelectedPatient] = useState<string>(patientId || '');
  const [selectedTableItems, setSelectedTableItems] = useState<ProcessedFile[]>([]);
  const [viewingFile, setViewingFile] = useState<ProcessedFile | null>(null);
  const [activeTab, setActiveTab] = useState<string>('extracted');

  const patientOptions: SelectProps.Option[] = patients.map((p) => ({
    label: `${p.full_name} (${p.patient_id})`,
    value: p.patient_id,
  }));

  const selectedPatientOption = patientOptions.find((opt) => opt.value === selectedPatient) || null;

  const handlePatientSelectionChange = async (newPatientId: string) => {
    setSelectedPatient(newPatientId);
    if (onPatientChange) {
      try {
        await onPatientChange(newPatientId);
      } catch (error) {
        console.error('Error changing patient filter:', error);
      }
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
    const categoryMap: { [key: string]: string } = {
      'medical-history': 'Historia clínica',
      'exam-results': 'Resultados de exámenes',
      'medical-images': 'Imágenes médicas',
      'identification': 'Documentos de identidad',
      'other': 'Otros',
      'not-identified': 'No identificado',
    };
    return categoryMap[category || 'other'] || 'Sin categoría';
  };

  // Get badge color based on category and status
  const getCategoryBadgeColor = (category?: string, isAutoClassified?: boolean) => {
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

  const renderCategoryCell = (item: ProcessedFile) => {
    const isAutoClassified = item.autoClassified;

    return (
      <Box>
        <Badge
          color={getCategoryBadgeColor(item.category, isAutoClassified)}
        >
          {getCategoryLabel(item.category)}
        </Badge>
        {isAutoClassified && item.confidence && (
          <Box fontSize="body-s" color="text-status-info" margin={{ top: 'xxxs' }}>
            Auto-clasificado ({item.confidence.toFixed(0)}% confianza)
          </Box>
        )}
        {item.originalClassification && item.originalClassification !== item.category && (
          <Box fontSize="body-s" color="text-status-warning" margin={{ top: 'xxxs' }}>
            Original: {item.originalClassification}
          </Box>
        )}
      </Box>
    );
  };

  const renderExtractedDataPreview = (extractedData: any) => {
    if (!extractedData) return <Box>No hay datos extraídos disponibles</Box>;

    const previewData = { ...extractedData };
    // Remove metadata fields for cleaner preview
    delete previewData.processing_metadata;
    delete previewData.classification;
    delete previewData.extraction_timestamp;

    return (
      <Box>
        <pre style={{
          whiteSpace: 'pre-wrap',
          fontSize: '12px',
          maxHeight: '400px',
          overflow: 'auto',
          backgroundColor: '#f5f5f5',
          padding: '10px',
          borderRadius: '4px'
        }}>
          {JSON.stringify(previewData, null, 2)}
        </pre>
      </Box>
    );
  };

  const renderBDAMetadata = (bdaMetadata: any) => {
    if (!bdaMetadata) return <Box>No hay metadatos de BDA disponibles</Box>;

    return (
      <Box>
        <pre style={{
          whiteSpace: 'pre-wrap',
          fontSize: '12px',
          maxHeight: '400px',
          overflow: 'auto',
          backgroundColor: '#f5f5f5',
          padding: '10px',
          borderRadius: '4px'
        }}>
          {JSON.stringify(bdaMetadata, null, 2)}
        </pre>
      </Box>
    );
  };

  return (
    <SpaceBetween size="l">
      {/* Patient Filter Section */}
      <Container header={<Header variant="h2">Filtrar archivos procesados por paciente</Header>}>
        <FormField
          label="Paciente"
          constraintText="Seleccione un paciente para ver solo sus archivos procesados, o deje vacío para ver todos"
        >
          <Select
            selectedOption={selectedPatientOption}
            onChange={({ detail }) => handlePatientSelectionChange(detail.selectedOption.value || '')}
            options={[
              { label: 'Todos los pacientes', value: '' },
              ...patientOptions
            ]}
            placeholder="Seleccione un paciente o vea todos"
            disabled={loading}
            filteringType="auto"
          />
        </FormField>
      </Container>

      <Table
        columnDefinitions={[
          {
            id: 'name',
            header: 'Nombre del documento',
            cell: (item) => item.name,
            sortingField: 'name',
          },
          {
            id: 'documentId',
            header: 'ID del documento',
            cell: (item) => item.documentId || 'N/A',
          },
          {
            id: 'patientId',
            header: 'ID del paciente',
            cell: (item) => item.patientId || 'N/A',
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
            id: 'processedDate',
            header: 'Fecha de procesamiento',
            cell: (item) => new Date(item.processedDate).toLocaleDateString('es-MX'),
            sortingField: 'processedDate',
          },
          {
            id: 'actions',
            header: 'Acciones',
            cell: (item) => (
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="expand"
                  variant="inline-icon"
                  onClick={() => setViewingFile(item)}
                >
                  Ver datos
                </Button>
                <Button
                  iconName="download"
                  variant="inline-icon"
                  onClick={() => onDownload(item)}
                >
                  Descargar
                </Button>
              </SpaceBetween>
            ),
          },
        ]}
        items={processedFiles}
        loading={loading}
        loadingText={t.common.loading}
        selectionType="multi"
        selectedItems={selectedTableItems}
        onSelectionChange={({ detail }) => setSelectedTableItems(detail.selectedItems)}
        empty={
          <Box textAlign="center" color="inherit">
            <b>No hay archivos procesados</b>
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              {selectedPatient ? 'No se encontraron archivos procesados para este paciente' : 'Seleccione un paciente para ver sus archivos procesados'}
            </Box>
          </Box>
        }
        header={
          <Header
            variant="h2"
            counter={`(${processedFiles.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                {onRefresh && (
                  <Button iconName="refresh" onClick={onRefresh} disabled={loading}>
                    Actualizar
                  </Button>
                )}
              </SpaceBetween>
            }
          >
            Archivos procesados por IA
          </Header>
        }
      />

      {/* File Details Modal */}
      <Modal
        visible={!!viewingFile}
        onDismiss={() => setViewingFile(null)}
        size="large"
        header={`Datos extraídos: ${viewingFile?.name || ''}`}
      >
        {viewingFile && (
          <SpaceBetween size="m">
            <Container>
              <SpaceBetween size="s">
                <Box>
                  <strong>Documento:</strong> {viewingFile.name}
                </Box>
                <Box>
                  <strong>ID del documento:</strong> {viewingFile.documentId || 'N/A'}
                </Box>
                <Box>
                  <strong>Paciente:</strong> {viewingFile.patientId || 'N/A'}
                </Box>
                <Box>
                  <strong>Categoría:</strong> {getCategoryLabel(viewingFile.category)}
                </Box>
                {viewingFile.confidence && (
                  <Box>
                    <strong>Confianza de clasificación:</strong> {viewingFile.confidence.toFixed(1)}%
                  </Box>
                )}
                <Box>
                  <strong>Fecha de procesamiento:</strong> {new Date(viewingFile.processedDate).toLocaleString('es-MX')}
                </Box>
              </SpaceBetween>
            </Container>

            <Tabs
              activeTabId={activeTab}
              onChange={({ detail }) => setActiveTab(detail.activeTabId)}
              tabs={[
                {
                  id: 'extracted',
                  label: 'Datos extraídos',
                  content: (
                    <Container>
                      <SpaceBetween size="m">
                        <Alert type="info">
                          Estos son los datos extraídos del documento mediante procesamiento de IA.
                        </Alert>
                        {renderExtractedDataPreview(viewingFile.extractedData)}
                      </SpaceBetween>
                    </Container>
                  ),
                },
                {
                  id: 'bda',
                  label: 'Metadatos BDA',
                  content: (
                    <Container>
                      <SpaceBetween size="m">
                        <Alert type="info">
                          Metadatos técnicos del procesamiento de Bedrock Data Automation.
                        </Alert>
                        {renderBDAMetadata(viewingFile.bdaMetadata)}
                      </SpaceBetween>
                    </Container>
                  ),
                },
              ]}
            />
          </SpaceBetween>
        )}
      </Modal>
    </SpaceBetween>
  );
}

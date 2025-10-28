import {
  Alert,
  Box,
  Container,
  FormField,
  Header,
  Modal,
  SpaceBetween,
  Tabs,
} from '@cloudscape-design/components';
import { useCallback, useEffect, useState } from 'react';
import { ThemeToggle } from '../components/common/ThemeToggle';
import {
  type EntityColumn,
  EntityManager,
  ExamForm,
  FileManager,
  MedicForm,
  type PatientFile,
  PatientForm,
  ReservationForm,
} from '../components/config';
import { MainLayout } from '../components/layout';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/apiClient';
import { examService } from '../services/examService';
import { medicService } from '../services/medicService';
import { patientService } from '../services/patientService';
import { reservationService } from '../services/reservationService';
import { storageService } from '../services/storageService';
import type {
  CreateExamRequest,
  CreateMedicRequest,
  CreatePatientRequest,
  CreateReservationRequest,
  Exam,
  Medic,
  Patient,
  Reservation,
} from '../types/api';

interface ConfigurationPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

type EntityType = 'patients' | 'medics' | 'exams' | 'reservations' | 'files' | 'settings';
type FormMode = 'create' | 'edit' | null;

export default function ConfigurationPage({ signOut, user }: ConfigurationPageProps) {
  const { t } = useLanguage();
  const { mode } = useTheme();
  const [activeTab, setActiveTab] = useState<EntityType>('patients');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Patients state
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatients, setSelectedPatients] = useState<Patient[]>([]);
  const [patientFormMode, setPatientFormMode] = useState<FormMode>(null);
  const [editingPatient, setEditingPatient] = useState<Patient | undefined>();

  // Medics state
  const [medics, setMedics] = useState<Medic[]>([]);
  const [selectedMedics, setSelectedMedics] = useState<Medic[]>([]);
  const [medicFormMode, setMedicFormMode] = useState<FormMode>(null);
  const [editingMedic, setEditingMedic] = useState<Medic | undefined>();

  // Exams state
  const [exams, setExams] = useState<Exam[]>([]);
  const [selectedExams, setSelectedExams] = useState<Exam[]>([]);
  const [examFormMode, setExamFormMode] = useState<FormMode>(null);
  const [editingExam, setEditingExam] = useState<Exam | undefined>();

  // Reservations state
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [selectedReservations, setSelectedReservations] = useState<Reservation[]>([]);
  const [reservationFormMode, setReservationFormMode] = useState<FormMode>(null);
  const [editingReservation, setEditingReservation] = useState<Reservation | undefined>();

  // Files state
  const [files, setFiles] = useState<PatientFile[]>([]);

  const loadFiles = useCallback(async () => {
    try {
      console.log('Loading files from S3...');
      const s3Files = await storageService.listFiles();

      // Convert S3 file items to PatientFile format
      const patientFiles: PatientFile[] = s3Files.map((s3File) => {
        // Extract patient ID and other metadata from the file key
        // Assuming file keys follow a pattern like: patients/{patientId}/{fileId}/{filename}
        const keyParts = s3File.key.split('/');
        const fileName = keyParts[keyParts.length - 1] || s3File.key;

        return {
          id: s3File.key,
          name: fileName,
          type: fileName.split('.').pop()?.toUpperCase() || 'UNKNOWN',
          size: s3File.size || 0,
          uploadDate: s3File.lastModified?.toISOString() || new Date().toISOString(),
          category: 'other', // Default category, could be enhanced with metadata
          url: s3File.key,
        };
      });

      setFiles(patientFiles);
      console.log(`Loaded ${patientFiles.length} files from S3`);
    } catch (err) {
      console.error('Failed to load files from S3:', err);
      setError(err instanceof Error ? err.message : 'Failed to load files');
    }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      switch (activeTab) {
        case 'patients': {
          const patientsData = await patientService.getPatients();
          setPatients(patientsData?.patients || []);
          break;
        }
        case 'medics': {
          const medicsData = await medicService.getMedics();
          setMedics(medicsData?.medics || []);
          break;
        }
        case 'exams': {
          const examsData = await examService.getExams();
          setExams(examsData?.exams || []);
          break;
        }
        case 'reservations': {
          const reservationsData = await reservationService.getReservations();
          setReservations(reservationsData?.reservations || []);
          break;
        }
        case 'files': {
          // Load files from S3 using storageService
          console.log('Loading files from S3...');
          await loadFiles();
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.errors.generic);
    } finally {
      setLoading(false);
    }
  }, [activeTab, t.errors.generic, loadFiles]);

  // Load data on mount and tab change
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Patient handlers
  const handleCreatePatient = async (data: CreatePatientRequest) => {
    await patientService.createPatient(data);
    setPatientFormMode(null);
    loadData();
  };

  const handleUpdatePatient = async (data: CreatePatientRequest) => {
    if (editingPatient) {
      await patientService.updatePatient(editingPatient.patient_id, data);
      setPatientFormMode(null);
      setEditingPatient(undefined);
      loadData();
    }
  };

  const handleDeletePatients = async (items: Patient[]) => {
    for (const patient of items) {
      await patientService.deletePatient(patient.patient_id);
    }
    setSelectedPatients([]);
    loadData();
  };

  // Medic handlers
  const handleCreateMedic = async (data: CreateMedicRequest) => {
    await medicService.createMedic(data);
    setMedicFormMode(null);
    loadData();
  };

  const handleUpdateMedic = async (data: CreateMedicRequest) => {
    if (editingMedic) {
      await medicService.updateMedic(editingMedic.medic_id, data);
      setMedicFormMode(null);
      setEditingMedic(undefined);
      loadData();
    }
  };

  const handleDeleteMedics = async (items: Medic[]) => {
    for (const medic of items) {
      await medicService.deleteMedic(medic.medic_id);
    }
    setSelectedMedics([]);
    loadData();
  };

  // Exam handlers
  const handleCreateExam = async (data: CreateExamRequest) => {
    await examService.createExam(data);
    setExamFormMode(null);
    loadData();
  };

  const handleUpdateExam = async (data: CreateExamRequest) => {
    if (editingExam) {
      await examService.updateExam(editingExam.exam_id, data);
      setExamFormMode(null);
      setEditingExam(undefined);
      loadData();
    }
  };

  const handleDeleteExams = async (items: Exam[]) => {
    for (const exam of items) {
      await examService.deleteExam(exam.exam_id);
    }
    setSelectedExams([]);
    loadData();
  };

  // Reservation handlers
  const handleCreateReservation = async (data: CreateReservationRequest) => {
    await reservationService.createReservation(data);
    setReservationFormMode(null);
    loadData();
  };

  const handleUpdateReservation = async (data: CreateReservationRequest) => {
    if (editingReservation) {
      await reservationService.updateReservation(editingReservation.reservation_id, data);
      setReservationFormMode(null);
      setEditingReservation(undefined);
      loadData();
    }
  };

  // Load all data for reservation form dependencies
  const loadAllData = async () => {
    try {
      const [patientsData, medicsData, examsData] = await Promise.all([
        patientService.getPatients(),
        medicService.getMedics(),
        examService.getExams(),
      ]);
      setPatients(patientsData?.patients || []);
      setMedics(medicsData?.medics || []);
      setExams(examsData?.exams || []);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleDeleteReservations = async (items: Reservation[]) => {
    for (const reservation of items) {
      await reservationService.deleteReservation(reservation.reservation_id);
    }
    setSelectedReservations([]);
    loadData();
  };

  // File handlers
  const handleUploadFile = async (file: File, category: string, selectedPatientId?: string) => {
    try {
      setLoading(true);
      setError('');

      // Get the selected patient from the FileManager component
      const targetPatient = selectedPatientId
        ? patients.find(p => p.patient_id === selectedPatientId)
        : patients.length > 0 ? patients[0] : null;

      if (!targetPatient) {
        throw new Error('No hay pacientes disponibles. Cree un paciente primero.');
      }

      // Create form data for file upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', targetPatient.patient_id);
      formData.append('category', category);
      formData.append('file_name', file.name);
      formData.append('file_type', file.type);

      console.log(`Uploading file ${file.name} for patient ${targetPatient.full_name} following document workflow guidelines`);

      // Import storage service
      const { storageService } = await import('../services/storageService');

      // Generate file ID and construct S3 path following document workflow guidelines
      const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

      // S3 path structure: {patient_id}/{category}/{timestamp}/{fileId}/{filename}
      const s3Key = `${targetPatient.patient_id}/${category}/${timestamp}/${fileId}/${file.name}`;

      // Prepare metadata following document workflow guidelines
      const fileMetadata = {
        'patient-id': targetPatient.patient_id,
        'document-category': category,
        'upload-timestamp': timestamp,
        'file-id': fileId,
        'workflow-stage': 'uploaded',
        'auto-classification-enabled': 'true',
        'original-filename': file.name
      };

      console.log(`📋 Document Workflow Metadata:`, fileMetadata);
      console.log(`📍 S3 Path (simplified): ${s3Key}`);

      // Get bucket name from config
      const { configService } = await import('../services/configService');
      const config = configService.getConfig();

      // Upload file to S3 with metadata following document workflow guidelines
      const uploadResult = await storageService.uploadFile(file, s3Key, {
        contentType: file.type,
        bucket: config.s3BucketName,
        metadata: fileMetadata,
        onProgress: (event) => {
          if (event.loaded && event.total) {
            const progress = (event.loaded / event.total) * 100;
            console.log(`Upload progress: ${progress.toFixed(1)}%`);
          }
        }
      });

      const response = {
        file_id: fileId,
        patient_id: targetPatient.patient_id,
        s3_key: uploadResult.key,
        message: `File uploaded successfully for patient ${targetPatient.full_name} following document workflow guidelines`,
        category: category,
        workflow_info: {
          next_stage: 'BDA processing and classification',
          expected_processing_time: '2-5 minutes',
          knowledge_base_integration: 'Automatic after processing'
        },
        note: 'File uploaded to S3 with simplified path structure and will be automatically processed by the document workflow'
      };

      console.log('File upload completed:', response);

      // Reload files data
      await loadFiles();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al subir archivo';
      setError(errorMessage);
      console.error('File upload error:', err);
      throw err; // Re-throw so FileManager can handle it
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFile = async (file: PatientFile) => {
    try {
      setLoading(true);
      setError('');

      // For demo purposes, show a message that download would work in full implementation
      alert(`En una implementación completa, se descargaría el archivo: ${file.name}`);

      console.log(`File ${file.name} download simulated`);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al descargar archivo';
      setError(errorMessage);
      console.error('Download error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      setLoading(true);
      setError('');

      // For demo purposes, show a message that delete would work in full implementation
      alert(`En una implementación completa, se eliminaría el archivo con ID: ${fileId}`);

      console.log(`File ${fileId} deletion simulated`);

      // Reload files data
      await loadFiles();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al eliminar archivo';
      setError(errorMessage);
      console.error('File deletion error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClassificationOverride = async (fileId: string, newCategory: string) => {
    try {
      setLoading(true);
      setError('');

      // Use API client for classification override
      const result = await apiClient.put(`/files/${fileId}/classification`, {
        category: newCategory
      });

      console.log('Classification updated:', result);

      // Show success message
      alert(`Clasificación actualizada a: ${newCategory}`);

      // Reload files data
      await loadFiles();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al actualizar clasificación';
      setError(errorMessage);
      console.error('Classification override error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshFiles = async () => {
    setLoading(true);
    setError('');
    try {
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh files');
    } finally {
      setLoading(false);
    }
  };

  // Column definitions
  const patientColumns: EntityColumn<Patient>[] = [
    { id: 'patient_id', header: 'ID', cell: (item) => item.patient_id, width: 150 },
    { id: 'full_name', header: 'Nombre completo', cell: (item) => item.full_name, sortingField: 'full_name' },
    { id: 'date_of_birth', header: 'Fecha de nacimiento', cell: (item) => item.date_of_birth },
    { id: 'created_at', header: 'Fecha de creación', cell: (item) => new Date(item.created_at).toLocaleDateString('es-MX') },
  ];

  const medicColumns: EntityColumn<Medic>[] = [
    { id: 'medic_id', header: 'ID', cell: (item) => item.medic_id, width: 150 },
    { id: 'full_name', header: 'Nombre completo', cell: (item) => item.full_name, sortingField: 'full_name' },
    { id: 'specialty', header: 'Especialidad', cell: (item) => item.specialty },
    { id: 'license_number', header: 'Número de licencia', cell: (item) => item.license_number },
  ];

  const examColumns: EntityColumn<Exam>[] = [
    { id: 'exam_id', header: 'ID', cell: (item) => item.exam_id, width: 150 },
    { id: 'exam_name', header: 'Nombre del examen', cell: (item) => item.exam_name, sortingField: 'exam_name' },
    { id: 'exam_type', header: 'Tipo', cell: (item) => item.exam_type },
    { id: 'duration_minutes', header: 'Duración (min)', cell: (item) => item.duration_minutes.toString() },
    { id: 'description', header: 'Descripción', cell: (item) => item.description || '-' },
  ];

  const reservationColumns: EntityColumn<Reservation>[] = [
    { id: 'reservation_id', header: 'ID', cell: (item) => item.reservation_id, width: 150 },
    { id: 'patient_id', header: 'ID Paciente', cell: (item) => item.patient_id },
    { id: 'medic_id', header: 'ID Médico', cell: (item) => item.medic_id },
    { id: 'exam_id', header: 'ID Examen', cell: (item) => item.exam_id },
    { id: 'appointment_date', header: 'Fecha de cita', cell: (item) => new Date(item.appointment_date).toLocaleString('es-MX') },
    { id: 'status', header: 'Estado', cell: (item) => item.status },
    { id: 'notes', header: 'Notas', cell: (item) => item.notes || '-' },
  ];

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">{t.config.title}</Header>

        {error && (
          <Alert type="error" dismissible onDismiss={() => setError('')}>
            {error}
          </Alert>
        )}

        <Tabs
          activeTabId={activeTab}
          onChange={({ detail }) => setActiveTab(detail.activeTabId as EntityType)}
          tabs={[
            {
              id: 'patients',
              label: t.config.patients,
              content: (
                <EntityManager
                  title={t.config.patients}
                  columns={patientColumns}
                  items={patients}
                  loading={loading}
                  selectedItems={selectedPatients}
                  onSelectionChange={setSelectedPatients}
                  onRefresh={loadData}
                  onCreate={() => setPatientFormMode('create')}
                  onEdit={(item) => {
                    setEditingPatient(item);
                    setPatientFormMode('edit');
                  }}
                  onDelete={handleDeletePatients}
                  getItemId={(item) => item.patient_id}
                  filteringPlaceholder="Buscar pacientes..."
                  emptyMessage="No hay pacientes registrados"
                />
              ),
            },
            {
              id: 'medics',
              label: t.config.medics,
              content: (
                <EntityManager
                  title={t.config.medics}
                  columns={medicColumns}
                  items={medics}
                  loading={loading}
                  selectedItems={selectedMedics}
                  onSelectionChange={setSelectedMedics}
                  onRefresh={loadData}
                  onCreate={() => setMedicFormMode('create')}
                  onEdit={(item) => {
                    setEditingMedic(item);
                    setMedicFormMode('edit');
                  }}
                  onDelete={handleDeleteMedics}
                  getItemId={(item) => item.medic_id}
                  filteringPlaceholder="Buscar médicos..."
                  emptyMessage="No hay médicos registrados"
                />
              ),
            },
            {
              id: 'exams',
              label: t.config.exams,
              content: (
                <EntityManager
                  title={t.config.exams}
                  columns={examColumns}
                  items={exams}
                  loading={loading}
                  selectedItems={selectedExams}
                  onSelectionChange={setSelectedExams}
                  onRefresh={loadData}
                  onCreate={() => setExamFormMode('create')}
                  onEdit={(item) => {
                    setEditingExam(item);
                    setExamFormMode('edit');
                  }}
                  onDelete={handleDeleteExams}
                  getItemId={(item) => item.exam_id}
                  filteringPlaceholder="Buscar exámenes..."
                  emptyMessage="No hay exámenes registrados"
                />
              ),
            },
            {
              id: 'reservations',
              label: t.config.reservations,
              content: (
                <EntityManager
                  title={t.config.reservations}
                  columns={reservationColumns}
                  items={reservations}
                  loading={loading}
                  selectedItems={selectedReservations}
                  onSelectionChange={setSelectedReservations}
                  onRefresh={loadData}
                  onCreate={() => {
                    loadAllData(); // Load all data for form dependencies
                    setReservationFormMode('create');
                  }}
                  onEdit={(item) => {
                    loadAllData(); // Load all data for form dependencies
                    setEditingReservation(item);
                    setReservationFormMode('edit');
                  }}
                  onDelete={handleDeleteReservations}
                  getItemId={(item) => item.reservation_id}
                  filteringPlaceholder="Buscar reservas..."
                  emptyMessage="No hay reservas registradas"
                />
              ),
            },
            {
              id: 'files',
              label: t.config.files,
              content: (
                <FileManager
                  files={files}
                  loading={loading}
                  onUpload={handleUploadFile}
                  onDownload={handleDownloadFile}
                  onDelete={handleDeleteFile}
                  onRefresh={handleRefreshFiles}
                  onClassificationOverride={handleClassificationOverride}
                  enableAutoClassification={true}
                  patients={(patients || []).map((p) => ({ patient_id: p.patient_id, full_name: p.full_name }))}
                />
              ),
            },
            {
              id: 'settings',
              label: t.config.settings,
              content: (
                <Container>
                  <SpaceBetween size="l">
                    <Header variant="h2">Configuración de la aplicación</Header>

                    <FormField
                      label="Tema de la aplicación"
                      description="Seleccione el tema visual para la aplicación"
                    >
                      <Box>
                        <SpaceBetween size="s" direction="horizontal" alignItems="center">
                          <Box>
                            <strong>Tema actual:</strong> {mode === 'light' ? '☀️ Claro' : '🌙 Oscuro'}
                          </Box>
                          <ThemeToggle variant="dropdown" />
                        </SpaceBetween>
                      </Box>
                    </FormField>

                    <FormField
                      label="Usuario"
                      description="Información del usuario actual"
                    >
                      <Box>
                        <strong>Email:</strong> {user?.signInDetails?.loginId || 'No disponible'}
                      </Box>
                    </FormField>

                    <FormField
                      label="Información del sistema"
                      description="Detalles técnicos de la aplicación"
                    >
                      <Box>
                        <SpaceBetween size="xs">
                          <div><strong>Versión:</strong> 1.0.0</div>
                          <div><strong>Última actualización:</strong> {new Date().toLocaleDateString('es-MX')}</div>
                          <div><strong>Región:</strong> us-east-1</div>
                        </SpaceBetween>
                      </Box>
                    </FormField>
                  </SpaceBetween>
                </Container>
              ),
            },
          ]}
        />

        {/* Patient Form Modal */}
        <Modal
          visible={patientFormMode !== null}
          onDismiss={() => {
            setPatientFormMode(null);
            setEditingPatient(undefined);
          }}
          size="medium"
        >
          <PatientForm
            patient={editingPatient}
            onSubmit={patientFormMode === 'edit' ? handleUpdatePatient : handleCreatePatient}
            onCancel={() => {
              setPatientFormMode(null);
              setEditingPatient(undefined);
            }}
          />
        </Modal>

        {/* Medic Form Modal */}
        <Modal
          visible={medicFormMode !== null}
          onDismiss={() => {
            setMedicFormMode(null);
            setEditingMedic(undefined);
          }}
          size="medium"
        >
          <MedicForm
            medic={editingMedic}
            onSubmit={medicFormMode === 'edit' ? handleUpdateMedic : handleCreateMedic}
            onCancel={() => {
              setMedicFormMode(null);
              setEditingMedic(undefined);
            }}
          />
        </Modal>

        {/* Exam Form Modal */}
        <Modal
          visible={examFormMode !== null}
          onDismiss={() => {
            setExamFormMode(null);
            setEditingExam(undefined);
          }}
          size="large"
        >
          <ExamForm
            exam={editingExam}
            onSubmit={examFormMode === 'edit' ? handleUpdateExam : handleCreateExam}
            onCancel={() => {
              setExamFormMode(null);
              setEditingExam(undefined);
            }}
          />
        </Modal>

        {/* Reservation Form Modal */}
        <Modal
          visible={reservationFormMode !== null}
          onDismiss={() => {
            setReservationFormMode(null);
            setEditingReservation(undefined);
          }}
          size="large"
        >
          <ReservationForm
            reservation={editingReservation}
            onSubmit={reservationFormMode === 'edit' ? handleUpdateReservation : handleCreateReservation}
            onCancel={() => {
              setReservationFormMode(null);
              setEditingReservation(undefined);
            }}
            patients={(patients || []).map((p) => ({ patient_id: p.patient_id, full_name: p.full_name }))}
            medics={(medics || []).map((m) => ({ medic_id: m.medic_id, full_name: m.full_name }))}
            exams={(exams || []).map((e) => ({ exam_id: e.exam_id, exam_name: e.exam_name, exam_type: e.exam_type }))}
          />
        </Modal>
      </SpaceBetween>
    </MainLayout>
  );
}

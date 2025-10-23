import { useState, useEffect } from 'react';
import {
  Header,
  SpaceBetween,
  Tabs,
  Modal,
  Alert,
} from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import { useLanguage } from '../contexts/LanguageContext';
import {
  EntityManager,
  PatientForm,
  MedicForm,
  ExamForm,
  ReservationForm,
  FileManager,
  type EntityColumn,
  type PatientFile,
} from '../components/config';
import { patientService } from '../services/patientService';
import { medicService } from '../services/medicService';
import { examService } from '../services/examService';
import { reservationService } from '../services/reservationService';
import type {
  Patient,
  Medic,
  Exam,
  Reservation,
  CreatePatientRequest,
  CreateMedicRequest,
  CreateExamRequest,
  CreateReservationRequest,
} from '../types/api';

interface ConfigurationPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

type EntityType = 'patients' | 'medics' | 'exams' | 'reservations' | 'files';
type FormMode = 'create' | 'edit' | null;

export default function ConfigurationPage({ signOut, user }: ConfigurationPageProps) {
  const { t } = useLanguage();
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
  const [files] = useState<PatientFile[]>([]);

  // Load data on mount and tab change
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      switch (activeTab) {
        case 'patients':
          const patientsData = await patientService.getPatients();
          setPatients(patientsData?.patients || []);
          break;
        case 'medics':
          const medicsData = await medicService.getMedics();
          setMedics(medicsData?.medics || []);
          break;
        case 'exams':
          const examsData = await examService.getExams();
          setExams(examsData?.exams || []);
          break;
        case 'reservations':
          const reservationsData = await reservationService.getReservations();
          setReservations(reservationsData?.reservations || []);
          break;
        case 'files':
          // Files are loaded per patient
          break;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.errors.generic);
    } finally {
      setLoading(false);
    }
  };

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

  const handleDeleteReservations = async (items: Reservation[]) => {
    for (const reservation of items) {
      await reservationService.deleteReservation(reservation.reservation_id);
    }
    setSelectedReservations([]);
    loadData();
  };

  // File handlers
  const handleUploadFile = async (file: File, category: string) => {
    // TODO: Implement file upload
    console.log('Upload file:', file, category);
  };

  const handleDownloadFile = (file: PatientFile) => {
    // TODO: Implement file download
    console.log('Download file:', file);
  };

  const handleDeleteFile = async (fileId: string) => {
    // TODO: Implement file deletion
    console.log('Delete file:', fileId);
  };

  const handleClassificationOverride = async (fileId: string, newCategory: string) => {
    // TODO: Implement classification override
    console.log('Override classification:', fileId, newCategory);
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
                  onCreate={() => setReservationFormMode('create')}
                  onEdit={(item) => {
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
                  onClassificationOverride={handleClassificationOverride}
                  enableAutoClassification={true}
                  patients={(patients || []).map((p) => ({ patient_id: p.patient_id, full_name: p.full_name }))}
                />
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
            patients={(patients || []).map((p) => ({ patient_id: p.patient_id, full_name: p.full_name }))}
            medics={(medics || []).map((m) => ({ medic_id: m.medic_id, full_name: m.full_name }))}
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
          />
        </Modal>
      </SpaceBetween>
    </MainLayout>
  );
}

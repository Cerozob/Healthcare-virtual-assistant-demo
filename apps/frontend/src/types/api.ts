/**
 * API Types
 * TypeScript interfaces for API requests and responses
 */

// Common types
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginationInfo {
  limit: number;
  offset: number;
  total: number;
  count: number;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  errorCode?: string;
}



// Patient types
export interface Address {
  street?: string;
  city?: string;
  province?: string;
  country?: string;
  postal_code?: string;
  numero?: string;
  calle?: string;
  ciudad?: string;
  pais?: string;
  codigo_postal?: string;
}

export interface MedicalCondition {
  codigo?: string;
  estado: string;
  descripcion: string;
  fecha_diagnostico: string;
}

export interface MedicalProcedure {
  fecha: string;
  nombre: string;
  notas?: string;
}

export interface Medication {
  nombre: string;
  dosis: string;
  frecuencia: string;
  fecha_inicio: string;
  activo: boolean;
}

export interface MedicalHistory {
  conditions: MedicalCondition[];
  procedures?: MedicalProcedure[];
  medications: Medication[];
  age?: number;
  gender?: string;
  document?: {
    type: string;
    number: string;
  };
}

export interface LabResult {
  fecha: string;
  nombre_prueba: string;
  valor: string;
  unidad: string;
  estado: 'normal' | 'anormal';
  rango_referencia: string;
}

export interface Patient {
  patient_id: string;
  first_name?: string;
  last_name?: string;
  full_name: string;
  email?: string;
  phone?: string;
  date_of_birth: string;
  age?: number;
  gender?: 'M' | 'F' | string;
  document_type?: string;
  document_number?: string;
  address?: Address;
  medical_history?: MedicalHistory;
  lab_results?: LabResult[];
  source_scan?: string;
  cedula?: string;
  created_at: string;
  updated_at: string;
}

export interface CreatePatientRequest {
  full_name: string;
  date_of_birth: string;
}

export interface UpdatePatientRequest {
  full_name?: string;
  date_of_birth?: string;
}

export interface PatientsResponse {
  patients: Patient[];
  pagination: PaginationInfo;
}

// Medic types
export interface Medic {
  medic_id: string;
  full_name: string;
  specialty: string;
  license_number: string;
  created_at: string;
  updated_at: string;
}

export interface CreateMedicRequest {
  full_name: string;
  specialty: string;
  license_number: string;
}

export interface UpdateMedicRequest {
  full_name?: string;
  specialty?: string;
  license_number?: string;
}

export interface MedicsResponse {
  medics: Medic[];
  pagination: PaginationInfo;
}

// Exam types (these are exam templates/types, not individual exam instances)
export interface Exam {
  exam_id: string;
  exam_name: string;
  exam_type: string;
  description?: string;
  duration_minutes: number;
  preparation_instructions?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateExamRequest {
  exam_name: string;
  exam_type: string;
  description?: string;
  duration_minutes: number;
  preparation_instructions?: string;
}

export interface UpdateExamRequest {
  exam_name?: string;
  exam_type?: string;
  description?: string;
  duration_minutes?: number;
  preparation_instructions?: string;
}

export interface ExamsResponse {
  exams: Exam[];
  pagination: PaginationInfo;
}

// Reservation types (appointments)
export interface Reservation {
  reservation_id: string;
  patient_id: string;
  medic_id: string;
  exam_id: string;
  appointment_date: string; // Combined date+time from backend
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  notes?: string;
  created_at: string;
  updated_at: string;
  // Joined fields from backend
  patient_name?: string;
  medic_name?: string;
  exam_name?: string;
}

export interface CreateReservationRequest {
  patient_id: string;
  medic_id: string;
  exam_id: string;
  appointment_date: string; // ISO string format
  notes?: string;
}

export interface UpdateReservationRequest {
  appointment_date?: string;
  status?: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  notes?: string;
}

export interface ReservationsResponse {
  reservations: Reservation[];
  pagination: PaginationInfo;
}

// Chat types
export interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  processingStatus?: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface ExternalSource {
  title: string;
  url: string;
  description?: string;
  type: 'document' | 'website' | 'database';
}

export interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'agent' | 'system';
  agentType?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  attachments?: FileAttachment[];
  sources?: ExternalSource[];
}

export interface ChatSession {
  sessionId: string;
  title?: string;
  createdAt: string;
  updatedAt?: string;
  isActive: boolean;
  messageCount?: number;
}

// Chat request interface for normal messaging
export interface ChatRequest {
  message: string;
  sessionId: string;
  files?: Array<{
    fileId: string;
    fileName: string;
    fileType: string;
    s3Location: string;
    metadata?: any;
  }>;
  patientContext?: {
    currentPatientId?: string;
    sessionContext?: any;
  };
}

// Chat response interface for normal messaging
export interface ChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string;
  metadata?: {
    processingTimeMs?: number;
    agentUsed?: string;
    toolsExecuted?: string[];
    requestId?: string;
    timestamp?: string;
    patientContext?: unknown;
    [key: string]: unknown;
  };
  patientContext?: {
    patientId?: string;
    patientName?: string;
    contextChanged?: boolean;
    identificationSource?: string;
  };
  fileProcessingResults?: Array<{
    fileId: string;
    fileName: string;
    status: 'processed' | 'failed' | 'skipped';
    classification?: string;
    analysisResults?: any;
    s3Location?: string;
    errorMessage?: string;
  }>;
  errors?: Array<{
    code: string;
    message: string;
    details?: any;
  }>;
  success: boolean;
}

// Strands-compatible multimodal content blocks
export interface TextBlock {
  text: string;
}

export interface ImageBlock {
  image: {
    format: 'jpeg' | 'jpg' | 'png' | 'gif' | 'webp';
    source: {
      bytes: string; // base64 encoded image data
    };
  };
}

export interface DocumentBlock {
  document: {
    format: 'pdf' | 'txt' | 'doc' | 'docx' | 'md' | 'csv' | 'xls' | 'xlsx' | 'html';
    name: string;
    source: {
      bytes: string; // base64 encoded document data
    };
  };
}

export type ContentBlock = TextBlock | ImageBlock | DocumentBlock;

export interface SendMessageRequest {
  content: ContentBlock[];
  sessionId?: string;
}

// Structured output interfaces for normal messaging
export interface StructuredOutput {
  content: {
    message: string;
    type: 'text' | 'markdown';
  };
  metadata: {
    processingTimeMs: number;
    agentUsed: string;
    toolsExecuted: string[];
    requestId: string;
    timestamp: string;
    sessionId: string;
    [key: string]: unknown;
  };
  patientContext?: {
    patientId?: string;
    patientName?: string;
    contextChanged: boolean;
    identificationSource?: string;
  };
  fileProcessingResults?: Array<{
    fileId: string;
    fileName: string;
    status: 'processed' | 'failed' | 'skipped';
    classification?: string;
    analysisResults?: any;
    s3Location?: string;
    errorMessage?: string;
  }>;
  errors?: Array<{
    code: string;
    message: string;
    details?: any;
  }>;
  success: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  stage: 'uploading' | 'processing' | 'analyzing' | 'completing';
  
  progress?: number;
}

export interface SendMessageResponse {
  response?: string;
  message?: string;
  sessionId?: string;
  timestamp?: string;
  // Patient context information from agent
  patient_context?: {
    patient_id?: string;
    patient_name?: string;
    has_patient_context?: boolean;
    patient_found?: boolean;
    patient_data?: Patient;
  };
  // Structured output for normal messaging
  structuredOutput?: StructuredOutput;
}

// Session management is handled by AgentCore internally
// Frontend generates session IDs and uses them consistently

// Document types - removed DocumentUploadRequest/Response, using direct S3 upload via Amplify Storage

export interface DocumentStatus {
  documentId: string;
  status: string;
  processingProgress?: number;
  extractedText?: string;
  metadata?: Record<string, unknown>;
  error?: string;
}

// Agent types
export interface AgentRequest {
  query: string;
  context?: Record<string, unknown>;
  agentType?: string;
}

export interface AgentResponse {
  response: string;
  agentType: string;
  metadata?: Record<string, unknown>;
  confidence?: number;
}

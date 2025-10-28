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
export interface Patient {
  patient_id: string;
  full_name: string;
  date_of_birth: string;
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

export interface SendMessageRequest {
  message: string;
  sessionId?: string;
  attachments?: Array<{
    fileName: string;
    fileSize: number;
    fileType: string;
    category: string;
    s3Key: string;
    // For AgentCore multi-modal support
    content?: string; // base64 encoded content for images
    mimeType?: string; // MIME type for proper processing
  }>;
}

export interface SendMessageResponse {
  response?: string;
  message?: string;
  sessionId?: string;
  timestamp?: string;
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

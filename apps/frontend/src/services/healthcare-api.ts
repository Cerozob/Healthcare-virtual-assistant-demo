/**
 * Healthcare API Service
 * 
 * Service layer for interacting with the CDK-managed REST API Gateway.
 * Uses Amplify's REST API client to make authenticated requests.
 */

import { get, post, put, del } from 'aws-amplify/api';
import { API_ENDPOINTS } from '../config/api-config';

const API_NAME = 'HealthcareAPI';

// Types
export interface Patient {
  id: string;
  name: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  address: string;
  emergencyContact: string;
  medicalHistory?: string;
}

export interface Medic {
  id: string;
  fullName: string;
  specialty: string;
  licenseNumber: string;
  createdAt: string;
}

export interface Exam {
  id: string;
  patientId: string;
  medicId: string;
  examType: string;
  scheduledDate: string;
  status: string;
  results?: string;
}

export interface Reservation {
  id: string;
  patientId: string;
  medicId: string;
  appointmentDate: string;
  status: string;
  notes?: string;
}

export interface ChatMessage {
  sessionId: string;
  content: string;
  attachments?: any[];
}

export interface ChatSession {
  sessionId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

// Patient API
export const patientApi = {
  async getAll(params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.PATIENTS,
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },

  async getById(id: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.PATIENT_BY_ID(id),
    }).response;
    return response.body.json();
  },

  async create(patient: Omit<Patient, 'id'>) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.PATIENTS,
      options: {
        body: patient,
      },
    }).response;
    return response.body.json();
  },

  async update(id: string, patient: Partial<Patient>) {
    const response = await put({
      apiName: API_NAME,
      path: API_ENDPOINTS.PATIENT_BY_ID(id),
      options: {
        body: patient,
      },
    }).response;
    return response.body.json();
  },

  async delete(id: string) {
    const response = await del({
      apiName: API_NAME,
      path: API_ENDPOINTS.PATIENT_BY_ID(id),
    }).response;
    return response.body.json();
  },
};

// Medic API
export const medicApi = {
  async getAll(params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.MEDICS,
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },

  async getById(id: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.MEDIC_BY_ID(id),
    }).response;
    return response.body.json();
  },

  async create(medic: Omit<Medic, 'id' | 'createdAt'>) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.MEDICS,
      options: {
        body: medic,
      },
    }).response;
    return response.body.json();
  },

  async update(id: string, medic: Partial<Medic>) {
    const response = await put({
      apiName: API_NAME,
      path: API_ENDPOINTS.MEDIC_BY_ID(id),
      options: {
        body: medic,
      },
    }).response;
    return response.body.json();
  },

  async delete(id: string) {
    const response = await del({
      apiName: API_NAME,
      path: API_ENDPOINTS.MEDIC_BY_ID(id),
    }).response;
    return response.body.json();
  },
};

// Exam API
export const examApi = {
  async getAll(params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.EXAMS,
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },

  async getById(id: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.EXAM_BY_ID(id),
    }).response;
    return response.body.json();
  },

  async create(exam: Omit<Exam, 'id'>) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.EXAMS,
      options: {
        body: exam,
      },
    }).response;
    return response.body.json();
  },

  async update(id: string, exam: Partial<Exam>) {
    const response = await put({
      apiName: API_NAME,
      path: API_ENDPOINTS.EXAM_BY_ID(id),
      options: {
        body: exam,
      },
    }).response;
    return response.body.json();
  },

  async delete(id: string) {
    const response = await del({
      apiName: API_NAME,
      path: API_ENDPOINTS.EXAM_BY_ID(id),
    }).response;
    return response.body.json();
  },
};

// Reservation API
export const reservationApi = {
  async getAll(params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.RESERVATIONS,
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },

  async getById(id: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.RESERVATION_BY_ID(id),
    }).response;
    return response.body.json();
  },

  async create(reservation: Omit<Reservation, 'id'>) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.RESERVATIONS,
      options: {
        body: reservation,
      },
    }).response;
    return response.body.json();
  },

  async update(id: string, reservation: Partial<Reservation>) {
    const response = await put({
      apiName: API_NAME,
      path: API_ENDPOINTS.RESERVATION_BY_ID(id),
      options: {
        body: reservation,
      },
    }).response;
    return response.body.json();
  },

  async delete(id: string) {
    const response = await del({
      apiName: API_NAME,
      path: API_ENDPOINTS.RESERVATION_BY_ID(id),
    }).response;
    return response.body.json();
  },
};

// Chat API
export const chatApi = {
  async sendMessage(message: ChatMessage) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.CHAT_MESSAGE,
      options: {
        body: message,
      },
    }).response;
    return response.body.json();
  },

  async getSessions(params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.CHAT_SESSIONS,
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },

  async createSession(title?: string) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.CHAT_SESSIONS,
      options: {
        body: { title },
      },
    }).response;
    return response.body.json();
  },

  async getSessionMessages(sessionId: string, params?: { limit?: number; offset?: number }) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.CHAT_SESSION_MESSAGES(sessionId),
      options: {
        queryParams: params,
      },
    }).response;
    return response.body.json();
  },
};

// ICD-10 API
export const icd10Api = {
  async getByCode(code: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.ICD10_BY_CODE(code),
    }).response;
    return response.body.json();
  },
};

// Agent API
export const agentApi = {
  async query(query: string, sessionId?: string) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.AGENT_QUERY,
      options: {
        body: { query, sessionId },
      },
    }).response;
    return response.body.json();
  },

  async healthCheck() {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.AGENT_HEALTH,
    }).response;
    return response.body.json();
  },
};

// Document API
export const documentApi = {
  async uploadMetadata(metadata: {
    documentId: string;
    s3Key: string;
    fileName: string;
    contentType?: string;
    fileSize?: number;
    patientId?: string;
    chatSessionId?: string;
  }) {
    const response = await post({
      apiName: API_NAME,
      path: API_ENDPOINTS.DOCUMENT_UPLOAD,
      options: {
        body: metadata,
      },
    }).response;
    return response.body.json();
  },

  async getStatus(documentId: string) {
    const response = await get({
      apiName: API_NAME,
      path: API_ENDPOINTS.DOCUMENT_STATUS(documentId),
    }).response;
    return response.body.json();
  },
};

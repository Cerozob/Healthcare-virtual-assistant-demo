/**
 * API Configuration for Healthcare System
 * 
 * This configuration connects the Amplify frontend to the CDK-managed REST API.
 * The API Gateway endpoint is deployed via CDK and referenced here.
 */

// API configuration that will be set by environment variables or build process
export const API_CONFIG = {
  HealthcareAPI: {
    endpoint: import.meta.env.VITE_API_ENDPOINT || 'https://api.healthcare.local/v1',
    region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
  },
};

// API endpoints for different resources
export const API_ENDPOINTS = {
  // Patient management
  PATIENTS: '/patients',
  PATIENT_BY_ID: (id: string) => `/patients/${id}`,
  
  // Medical staff
  MEDICS: '/medics',
  MEDIC_BY_ID: (id: string) => `/medics/${id}`,
  
  // Examinations
  EXAMS: '/exams',
  EXAM_BY_ID: (id: string) => `/exams/${id}`,
  
  // Reservations/Appointments
  RESERVATIONS: '/reservations',
  RESERVATION_BY_ID: (id: string) => `/reservations/${id}`,
  
  // ICD-10 codes
  ICD10_BY_CODE: (code: string) => `/icd10/${code}`,
  
  // Chat functionality
  CHAT_MESSAGE: '/chat/message',
  CHAT_SESSIONS: '/chat/sessions',
  CHAT_SESSION_MESSAGES: (sessionId: string) => `/chat/sessions/${sessionId}/messages`,
  
  // Agent integration
  AGENT_QUERY: '/agent',
  AGENT_HEALTH: '/agent/health',
  
  // Document management
  DOCUMENT_UPLOAD: '/documents/upload',
  DOCUMENT_STATUS: (id: string) => `/documents/status/${id}`,
} as const;

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.HealthcareAPI.endpoint}${endpoint}`;
};

// API configuration for Amplify.configure()
export const getAmplifyApiConfig = () => ({
  API: {
    REST: {
      HealthcareAPI: API_CONFIG.HealthcareAPI,
    },
  },
});

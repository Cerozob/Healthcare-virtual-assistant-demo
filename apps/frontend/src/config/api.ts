/**
 * API Configuration
 * Centralized configuration for API endpoints and settings
 */

import { configService } from '../services/configService';

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}

// Default configuration - will be updated with runtime config
const defaultConfig: ApiConfig = {
  baseUrl: 'http://localhost:3000/v1', // fallback only
  timeout: 30000, // 30 seconds
  retries: 3
};

/**
 * Get API configuration with runtime base URL
 */
export async function getApiConfig(): Promise<ApiConfig> {
  try {
    const runtimeConfig = await configService.loadConfig();
    return {
      ...defaultConfig,
      baseUrl: runtimeConfig.apiBaseUrl
    };
  } catch (error) {
    console.warn('Failed to load runtime config, using default:', error);
    return defaultConfig;
  }
}

// Legacy export for backward compatibility (use getApiConfig() instead)
export const apiConfig = defaultConfig;

// API endpoints
export const API_ENDPOINTS = {
  // Patient endpoints
  patients: '/patients',
  patient: (id: string) => `/patients/${id}`,
  
  // Medic endpoints
  medics: '/medics',
  medic: (id: string) => `/medics/${id}`,
  
  // Exam endpoints
  exams: '/exams',
  exam: (id: string) => `/exams/${id}`,
  
  // Reservation endpoints
  reservations: '/reservations',
  reservation: (id: string) => `/reservations/${id}`,
  
  // Chat endpoints
  chatMessage: '/chat/message',
  chatSessions: '/chat/sessions',
  chatSessionMessages: (sessionId: string) => `/chat/sessions/${sessionId}/messages`,
  
  // Agent endpoints
  agent: '/agent',
  
  // Document endpoints
  documentUpload: '/documents/upload',
  documentStatus: (id: string) => `/documents/status/${id}`
} as const;

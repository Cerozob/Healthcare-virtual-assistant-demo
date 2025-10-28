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

// Default configuration
const defaultConfig: ApiConfig = {
  baseUrl: 'http://localhost:3000/v1', // Fallback for development
  timeout: 30000, // 30 seconds
  retries: 3
};

/**
 * Get API configuration with runtime base URL
 */
export function getApiConfig(): ApiConfig {
  try {
    const runtimeConfig = configService.getConfig();
    console.log('Runtime config loaded:', runtimeConfig)
    return {
      ...defaultConfig,
      baseUrl: runtimeConfig.apiBaseUrl
    };
  } catch (error) {
    console.warn('Failed to load runtime config, using default:', error);
    return defaultConfig;
  }
}

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

  // AgentCore endpoints
  agentCoreChat: '/agentcore/chat',
  agentCoreHealth: '/agentcore/health',

  // Document endpoints - removed, using direct S3 upload via Amplify Storage
} as const;

/**
 * Services Index
 * Centralized export for all service classes
 */

export { apiClient, ApiError } from './apiClient';
export { patientService, PatientService } from './patientService';
export { medicService, MedicService } from './medicService';
export { examService, ExamService } from './examService';
export { reservationService, ReservationService } from './reservationService';
export { chatService, ChatService } from './chatService';
// documentService removed - using direct S3 upload via Amplify Storage
// Note: chatService updated to use AgentCore instead of old chat endpoints
export { agentService, AgentService } from './agentService';

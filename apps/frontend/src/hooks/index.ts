/**
 * Hooks Index
 * Centralized export for all custom hooks
 */

export { useApi } from './useApi';
export {
  useChatMessages, useChatSessions,
  useCreateChatSession, useSendMessage
} from './useChat';
// Document hooks removed - using direct S3 upload via Amplify Storage
export {
  useCreatePatient, useDeletePatient, usePatient, usePatients, useUpdatePatient
} from './usePatients';
export { useFileProcessing } from './useFileProcessing';

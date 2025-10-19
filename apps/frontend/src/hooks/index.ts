/**
 * Hooks Index
 * Centralized export for all custom hooks
 */

export { useApi } from './useApi';
export {
  useChatMessages, useChatSessions,
  useCreateChatSession, useSendMessage
} from './useChat';
export {
  useDocumentStatus, useDocumentUpload
} from './useDocuments';
export {
  useCreatePatient, useDeletePatient, usePatient, usePatients, useUpdatePatient
} from './usePatients';

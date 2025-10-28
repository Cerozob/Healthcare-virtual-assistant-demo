/**
 * Hooks Index
 * Centralized export for all custom hooks
 */

export { useApi } from './useApi';
export { useSendMessage } from './useChat';
// Document hooks removed - using direct S3 upload via Amplify Storage
export { useFileProcessing } from './useFileProcessing';
export {
  useCreatePatient, useDeletePatient, usePatient, usePatients, useUpdatePatient
} from './usePatients';


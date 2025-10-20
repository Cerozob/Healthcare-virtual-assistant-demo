/**
 * Notification types and interfaces
 */

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  description?: string;
  dismissible?: boolean;
  autoDismiss?: boolean;
  duration?: number; // in milliseconds
  timestamp: Date;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface FileProcessingNotification extends Notification {
  fileId: string;
  fileName: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
}

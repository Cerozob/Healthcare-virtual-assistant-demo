/**
 * Notification System Component
 * Provides user feedback through Cloudscape Flashbar component
 */

import { Flashbar, type FlashbarProps } from '@cloudscape-design/components';
import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import type { NotificationMessage } from '../../utils/errorHandler';

export interface NotificationContextType {
  addNotification: (notification: NotificationMessage) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  showSuccess: (title: string, message: string, autoHide?: boolean, duration?: number) => void;
  showError: (title: string, message: string, action?: { label: string; handler: () => void }) => void;
  showWarning: (title: string, message: string, action?: { label: string; handler: () => void }) => void;
  showInfo: (title: string, message: string, autoHide?: boolean, duration?: number) => void;
}

interface NotificationItem extends NotificationMessage {
  id: string;
  timestamp: number;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export function useNotifications(): NotificationContextType {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: ReactNode;
  maxNotifications?: number;
}

export function NotificationProvider({ children, maxNotifications = 5 }: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Auto-hide notifications
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    notifications.forEach((notification) => {
      if (notification.autoHide && notification.duration) {
        const timer = setTimeout(() => {
          removeNotification(notification.id);
        }, notification.duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [notifications]);

  const generateId = useCallback(() => {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  const addNotification = useCallback((notification: NotificationMessage) => {
    const id = generateId();
    const newNotification: NotificationItem = {
      ...notification,
      id,
      timestamp: Date.now(),
    };

    setNotifications(prev => {
      const updated = [newNotification, ...prev];
      
      // Limit number of notifications
      if (updated.length > maxNotifications) {
        return updated.slice(0, maxNotifications);
      }
      
      return updated;
    });

    return id;
  }, [generateId, maxNotifications]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const showSuccess = useCallback((
    title: string,
    message: string,
    autoHide = true,
    duration = 5000
  ) => {
    addNotification({
      type: 'success',
      title,
      message,
      dismissible: true,
      autoHide,
      duration,
    });
  }, [addNotification]);

  const showError = useCallback((
    title: string,
    message: string,
    action?: { label: string; handler: () => void }
  ) => {
    addNotification({
      type: 'error',
      title,
      message,
      dismissible: true,
      autoHide: false,
      action,
    });
  }, [addNotification]);

  const showWarning = useCallback((
    title: string,
    message: string,
    action?: { label: string; handler: () => void }
  ) => {
    addNotification({
      type: 'warning',
      title,
      message,
      dismissible: true,
      autoHide: false,
      action,
    });
  }, [addNotification]);

  const showInfo = useCallback((
    title: string,
    message: string,
    autoHide = true,
    duration = 3000
  ) => {
    addNotification({
      type: 'info',
      title,
      message,
      dismissible: true,
      autoHide,
      duration,
    });
  }, [addNotification]);

  const contextValue: NotificationContextType = {
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <NotificationDisplay notifications={notifications} onDismiss={removeNotification} />
    </NotificationContext.Provider>
  );
}

interface NotificationDisplayProps {
  notifications: NotificationItem[];
  onDismiss: (id: string) => void;
}

function NotificationDisplay({ notifications, onDismiss }: NotificationDisplayProps) {
  if (notifications.length === 0) {
    return null;
  }

  const flashbarItems: FlashbarProps.MessageDefinition[] = notifications.map((notification) => ({
    type: notification.type,
    header: notification.title,
    content: notification.message,
    dismissible: notification.dismissible,
    dismissLabel: 'Cerrar notificación',
    onDismiss: () => onDismiss(notification.id),
    id: notification.id,
    action: notification.action ? (
      <button 
        onClick={notification.action.handler}
        style={{
          background: 'none',
          border: '1px solid #0073bb',
          color: '#0073bb',
          padding: '4px 8px',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        {notification.action.label}
      </button>
    ) : undefined,
  }));

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 9999,
      maxWidth: '400px',
      width: '100%',
    }}>
      <Flashbar items={flashbarItems} />
    </div>
  );
}

/**
 * Hook for file operation notifications
 */
export function useFileOperationNotifications() {
  const notifications = useNotifications();

  const notifyFileUploadSuccess = useCallback((fileName: string, patientName?: string) => {
    const message = patientName 
      ? `El archivo "${fileName}" se subió exitosamente para ${patientName}.`
      : `El archivo "${fileName}" se subió exitosamente.`;
    
    notifications.showSuccess('Archivo subido', message);
  }, [notifications]);

  const notifyFileUploadError = useCallback((fileName: string, error: string) => {
    notifications.showError(
      'Error al subir archivo',
      `No se pudo subir "${fileName}": ${error}`
    );
  }, [notifications]);

  const notifyFileDownloadSuccess = useCallback((fileName: string) => {
    notifications.showSuccess(
      'Descarga iniciada',
      `La descarga de "${fileName}" ha comenzado.`,
      true,
      3000
    );
  }, [notifications]);

  const notifyFileDownloadError = useCallback((fileName: string, error: string) => {
    notifications.showError(
      'Error en descarga',
      `No se pudo descargar "${fileName}": ${error}`
    );
  }, [notifications]);

  const notifyFileDeleteSuccess = useCallback((fileNames: string[]) => {
    const message = fileNames.length === 1
      ? `El archivo "${fileNames[0]}" se eliminó exitosamente.`
      : `Se eliminaron ${fileNames.length} archivos exitosamente.`;
    
    notifications.showSuccess('Archivos eliminados', message);
  }, [notifications]);

  const notifyFileDeleteError = useCallback((error: string) => {
    notifications.showError(
      'Error al eliminar archivos',
      `No se pudieron eliminar los archivos: ${error}`
    );
  }, [notifications]);

  const notifyPreviewSuccess = useCallback((fileName: string) => {
    notifications.showInfo(
      'Vista previa cargada',
      `Se cargó la vista previa de "${fileName}".`,
      true,
      2000
    );
  }, [notifications]);

  const notifyPreviewError = useCallback((fileName: string, error: string, onDownload?: () => void) => {
    notifications.showError(
      'Error en vista previa',
      `No se pudo mostrar la vista previa de "${fileName}": ${error}`,
      onDownload ? {
        label: 'Descargar archivo',
        handler: onDownload,
      } : undefined
    );
  }, [notifications]);

  const notifyUnsupportedFileType = useCallback((fileName: string, fileType: string, onDownload?: () => void) => {
    notifications.showWarning(
      'Tipo de archivo no soportado',
      `El archivo "${fileName}" (${fileType}) no es compatible con la vista previa.`,
      onDownload ? {
        label: 'Descargar archivo',
        handler: onDownload,
      } : undefined
    );
  }, [notifications]);

  const notifyFileSizeWarning = useCallback((fileName: string, fileSize: string, maxSize: string) => {
    notifications.showWarning(
      'Archivo grande detectado',
      `El archivo "${fileName}" (${fileSize}) es mayor al límite recomendado (${maxSize}). La vista previa puede ser lenta.`
    );
  }, [notifications]);

  const notifyRetryAttempt = useCallback((fileName: string, attempt: number, maxAttempts: number) => {
    notifications.showInfo(
      'Reintentando operación',
      `Reintentando cargar "${fileName}" (intento ${attempt} de ${maxAttempts})...`,
      true,
      2000
    );
  }, [notifications]);

  return {
    notifyFileUploadSuccess,
    notifyFileUploadError,
    notifyFileDownloadSuccess,
    notifyFileDownloadError,
    notifyFileDeleteSuccess,
    notifyFileDeleteError,
    notifyPreviewSuccess,
    notifyPreviewError,
    notifyUnsupportedFileType,
    notifyFileSizeWarning,
    notifyRetryAttempt,
  };
}

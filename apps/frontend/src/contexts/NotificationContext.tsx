/**
 * Notification Context for managing application-wide notifications
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Notification } from '../types/notifications';

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  showSuccess: (message: string, description?: string) => string;
  showError: (message: string, description?: string) => string;
  showWarning: (message: string, description?: string) => string;
  showInfo: (message: string, description?: string) => string;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      dismissible: notification.dismissible ?? true,
      autoDismiss: notification.autoDismiss ?? true,
      duration: notification.duration ?? 5000,
    };

    setNotifications((prev) => [...prev, newNotification]);

    // Auto-dismiss if enabled
    if (newNotification.autoDismiss) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const showSuccess = useCallback((message: string, description?: string) => {
    return addNotification({
      type: 'success',
      message,
      description,
    });
  }, [addNotification]);

  const showError = useCallback((message: string, description?: string) => {
    return addNotification({
      type: 'error',
      message,
      description,
      autoDismiss: false, // Errors should be manually dismissed
    });
  }, [addNotification]);

  const showWarning = useCallback((message: string, description?: string) => {
    return addNotification({
      type: 'warning',
      message,
      description,
    });
  }, [addNotification]);

  const showInfo = useCallback((message: string, description?: string) => {
    return addNotification({
      type: 'info',
      message,
      description,
    });
  }, [addNotification]);

  const value: NotificationContextType = {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

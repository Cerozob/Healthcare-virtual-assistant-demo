/**
 * NotificationCenter component for displaying application notifications
 * Uses Cloudscape Alert components for notification display
 */

import React from 'react';
import { Flashbar, FlashbarProps } from '@cloudscape-design/components';
import { useNotifications } from '../../contexts/NotificationContext';
import { Notification, NotificationType } from '../../types/notifications';

const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useNotifications();

  // Convert our notification type to Cloudscape Flashbar type
  const mapNotificationType = (type: NotificationType): FlashbarProps.Type => {
    switch (type) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'info';
    }
  };

  // Convert notifications to Flashbar items
  const flashbarItems: FlashbarProps.MessageDefinition[] = notifications.map((notification: Notification) => ({
    type: mapNotificationType(notification.type),
    header: notification.message,
    content: notification.description,
    dismissible: notification.dismissible,
    dismissLabel: 'Cerrar',
    onDismiss: () => removeNotification(notification.id),
    id: notification.id,
    action: notification.action ? (
      <button onClick={notification.action.onClick}>
        {notification.action.label}
      </button>
    ) : undefined,
  }));

  return (
    <div
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 9999,
        maxWidth: '500px',
        width: '100%',
      }}
    >
      <Flashbar items={flashbarItems} />
    </div>
  );
};

export default NotificationCenter;

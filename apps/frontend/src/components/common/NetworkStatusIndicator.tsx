import React, { useEffect, useState } from 'react';
import { Flashbar, FlashbarProps } from '@cloudscape-design/components';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';

export const NetworkStatusIndicator: React.FC = () => {
  const { isOnline, wasOffline } = useNetworkStatus();
  const [items, setItems] = useState<FlashbarProps.MessageDefinition[]>([]);

  useEffect(() => {
    if (!isOnline) {
      setItems([
        {
          type: 'error',
          content: 'Sin conexión a internet. Algunas funciones pueden no estar disponibles.',
          id: 'offline-notification',
          dismissible: false
        }
      ]);
    } else if (wasOffline) {
      setItems([
        {
          type: 'success',
          content: 'Conexión restaurada.',
          id: 'online-notification',
          dismissible: true,
          onDismiss: () => setItems([])
        }
      ]);
      
      // Auto-dismiss after 3 seconds
      setTimeout(() => {
        setItems([]);
      }, 3000);
    } else {
      setItems([]);
    }
  }, [isOnline, wasOffline]);

  if (items.length === 0) {
    return null;
  }

  return <Flashbar items={items} />;
};

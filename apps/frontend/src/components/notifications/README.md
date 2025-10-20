# Notification System

This directory contains the notification system components for displaying alerts, file processing status, and toast notifications throughout the application.

## Components

### NotificationCenter

The `NotificationCenter` component displays toast-style notifications in the top-right corner of the screen using Cloudscape's Flashbar component.

**Features:**
- Success, error, warning, and info notification types
- Auto-dismiss functionality (configurable per notification)
- Manual dismissal for error notifications
- Action buttons support
- Queue management

**Usage:**

```tsx
import { useNotifications } from '../../contexts/NotificationContext';

function MyComponent() {
  const { showSuccess, showError, showWarning, showInfo } = useNotifications();

  const handleAction = () => {
    showSuccess('Operación exitosa', 'Los datos se guardaron correctamente');
  };

  const handleError = () => {
    showError('Error al guardar', 'No se pudo conectar con el servidor');
  };

  return (
    <button onClick={handleAction}>Guardar</button>
  );
}
```

### FileUploadStatus

The `FileUploadStatus` component displays the status of file uploads and processing with progress indicators.

**Features:**
- Real-time progress tracking
- Multiple processing stages display
- Status indicators (uploading, processing, completed, failed)
- Retry, cancel, and dismiss actions
- Duration tracking
- Error message display

**Usage:**

```tsx
import FileUploadStatus from './FileUploadStatus';
import { useFileProcessing } from '../../hooks/useFileProcessing';

function MyUploadComponent() {
  const { files, addFile, updateFileStatus, removeFile } = useFileProcessing();

  const handleUpload = async (file: File) => {
    // Add file to tracking
    const fileId = addFile(`file-${Date.now()}`, file.name);

    // Simulate upload
    updateFileStatus(fileId, {
      status: 'uploading',
      progress: 50,
    });

    // Update to processing
    updateFileStatus(fileId, {
      status: 'processing',
      progress: 75,
      stage: 'Analizando contenido',
    });

    // Complete
    updateFileStatus(fileId, {
      status: 'completed',
      progress: 100,
    });
  };

  return (
    <div>
      <input type="file" onChange={(e) => handleUpload(e.target.files[0])} />
      <FileUploadStatus
        files={files}
        onRetry={(fileId) => console.log('Retry', fileId)}
        onCancel={(fileId) => removeFile(fileId)}
        onDismiss={(fileId) => removeFile(fileId)}
      />
    </div>
  );
}
```

## Hooks

### useNotifications

Hook for managing application-wide notifications.

**Methods:**
- `addNotification(notification)` - Add a custom notification
- `removeNotification(id)` - Remove a specific notification
- `clearAllNotifications()` - Clear all notifications
- `showSuccess(message, description?)` - Show success notification
- `showError(message, description?)` - Show error notification
- `showWarning(message, description?)` - Show warning notification
- `showInfo(message, description?)` - Show info notification

### useFileProcessing

Hook for managing file processing status with automatic polling.

**Methods:**
- `addFile(fileId, fileName)` - Add a file to tracking
- `updateFileStatus(fileId, updates)` - Update file status
- `removeFile(fileId)` - Remove a file from tracking
- `clearCompleted()` - Clear all completed/failed files
- `pollFileStatus(fileId)` - Poll for status updates (placeholder)

**Properties:**
- `files` - Array of current file processing statuses

## Context

### NotificationProvider

Wrap your application with `NotificationProvider` to enable notifications throughout the app.

```tsx
import { NotificationProvider } from './contexts/NotificationContext';
import { NotificationCenter } from './components/notifications';

function App() {
  return (
    <NotificationProvider>
      <NotificationCenter />
      {/* Your app components */}
    </NotificationProvider>
  );
}
```

## Types

### Notification

```typescript
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  description?: string;
  dismissible?: boolean;
  autoDismiss?: boolean;
  duration?: number; // milliseconds
  timestamp: Date;
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

### FileProcessingStatus

```typescript
interface FileProcessingStatus {
  fileId: string;
  fileName: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage?: string;
  error?: string;
  startTime: Date;
  endTime?: Date;
}
```

## Demo

Visit `/demo-notifications` to see a live demonstration of the notification system with simulated file uploads and processing.

## Integration with Backend

The file processing system includes placeholder polling logic that should be replaced with actual backend integration:

```typescript
// In useFileProcessing.ts
const pollFileStatus = async (fileId: string) => {
  const response = await fetch(`/api/files/${fileId}/status`);
  const data = await response.json();
  return data;
};
```

The backend should return a `FileProcessingStatus` object with the current status, progress, and any error information.

## Spanish Localization

All notification messages use Spanish translations from `i18n/es.ts`. Add new notification messages there:

```typescript
notifications: {
  fileProcessingStarted: 'Procesamiento de archivo iniciado',
  fileProcessingCompleted: 'Procesamiento de archivo completado',
  fileProcessingFailed: 'Error al procesar archivo',
  // Add more messages here
}
```

# Notification System Implementation

## Overview

This document describes the notification and file processing status tracking system implemented for the medical AI frontend application.

## Components Implemented

### 1. NotificationCenter Component
**Location:** `src/components/notifications/NotificationCenter.tsx`

A fixed-position notification display using Cloudscape's Flashbar component that shows toast-style notifications in the top-right corner.

**Features:**
- Four notification types: success, error, warning, info
- Auto-dismiss functionality (5 seconds by default, disabled for errors)
- Manual dismissal support
- Action button support
- Queue management

### 2. FileUploadStatus Component
**Location:** `src/components/notifications/FileUploadStatus.tsx`

A comprehensive file processing status tracker with progress indicators and stage information.

**Features:**
- Real-time progress bars for uploads and processing
- Status indicators (uploading, processing, completed, failed)
- Processing stage descriptions in Spanish
- Duration tracking
- Action buttons (Retry, Cancel, Dismiss)
- Error message display
- Automatic polling support

## Context and State Management

### NotificationContext
**Location:** `src/contexts/NotificationContext.tsx`

Provides application-wide notification management with the following API:

```typescript
interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  showSuccess: (message: string, description?: string) => string;
  showError: (message: string, description?: string) => string;
  showWarning: (message: string, description?: string) => string;
  showInfo: (message: string, description?: string) => string;
}
```

## Custom Hooks

### useFileProcessing Hook
**Location:** `src/hooks/useFileProcessing.ts`

Manages file processing status with automatic polling and notifications.

**API:**
```typescript
const {
  files,              // Array of FileProcessingStatus
  addFile,            // Add file to tracking
  updateFileStatus,   // Update file status
  removeFile,         // Remove file from tracking
  clearCompleted,     // Clear completed/failed files
  pollFileStatus,     // Poll for status updates
} = useFileProcessing();
```

**Features:**
- Automatic status polling for active files
- Integrated notifications for status changes
- Configurable poll interval
- Status change callbacks

## Types

### Notification Types
**Location:** `src/types/notifications.ts`

```typescript
type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  description?: string;
  dismissible?: boolean;
  autoDismiss?: boolean;
  duration?: number;
  timestamp: Date;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface FileProcessingNotification extends Notification {
  fileId: string;
  fileName: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
}
```

### File Processing Status
**Location:** `src/components/notifications/FileUploadStatus.tsx`

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

## Integration

### App Integration
The notification system is integrated at the app level in `src/app.tsx`:

```tsx
<NotificationProvider>
  <NotificationCenter />
  {/* Rest of app */}
</NotificationProvider>
```

### Usage Example

```tsx
import { useNotifications } from '../contexts/NotificationContext';
import { useFileProcessing } from '../hooks/useFileProcessing';

function MyComponent() {
  const { showSuccess, showError } = useNotifications();
  const { files, addFile, updateFileStatus } = useFileProcessing();

  const handleFileUpload = async (file: File) => {
    // Add file to tracking
    const fileId = addFile(`file-${Date.now()}`, file.name);

    try {
      // Upload file
      updateFileStatus(fileId, {
        status: 'uploading',
        progress: 50,
      });

      // Process file
      updateFileStatus(fileId, {
        status: 'processing',
        progress: 75,
        stage: 'Analizando contenido médico',
      });

      // Complete
      updateFileStatus(fileId, {
        status: 'completed',
        progress: 100,
      });

      showSuccess('Archivo procesado', 'El archivo se procesó correctamente');
    } catch (error) {
      updateFileStatus(fileId, {
        status: 'failed',
        error: error.message,
      });
      showError('Error', 'No se pudo procesar el archivo');
    }
  };

  return (
    <div>
      <FileUploadStatus
        files={files}
        onRetry={(id) => handleFileUpload(/* retry logic */)}
        onCancel={(id) => removeFile(id)}
        onDismiss={(id) => removeFile(id)}
      />
    </div>
  );
}
```

## Spanish Localization

All notification messages are in Spanish (Latin American). New messages added to `src/i18n/es.ts`:

```typescript
notifications: {
  title: 'Notificaciones',
  fileProcessingStarted: 'Procesamiento de archivo iniciado',
  fileProcessingCompleted: 'Procesamiento de archivo completado',
  fileProcessingFailed: 'Error al procesar archivo',
  fileUploading: 'Subiendo archivo',
  fileProcessing: 'Procesando archivo',
  dismiss: 'Cerrar',
  retry: 'Reintentar',
  cancel: 'Cancelar',
}
```

## Demo Page

A comprehensive demo page is available at `/demo-notifications` that demonstrates:
- All notification types
- File upload simulation with progress
- File processing simulation with stages
- Error handling and retry functionality
- Complete integration examples

**Location:** `src/pages/FileProcessingDemoPage.tsx`

## Backend Integration

The system includes placeholder polling logic that should be replaced with actual backend API calls:

```typescript
// TODO: Replace with actual API integration
const pollFileStatus = async (fileId: string) => {
  const response = await fetch(`/api/files/${fileId}/status`);
  const data = await response.json();
  return data;
};
```

Expected backend response format:
```json
{
  "fileId": "file-123",
  "fileName": "document.pdf",
  "status": "processing",
  "progress": 75,
  "stage": "Analyzing medical content",
  "error": null,
  "startTime": "2025-01-20T10:00:00Z",
  "endTime": null
}
```

## Requirements Satisfied

This implementation satisfies **Requirement 5** from the requirements document:

✅ 5.1 - File processing start notifications with Cloudscape Alert component  
✅ 5.2 - File processing completion notifications with results  
✅ 5.3 - Error notifications with appropriate error messages  
✅ 5.4 - Individual status tracking for multiple files  
✅ 5.5 - Background status maintenance after dismissal  

## Files Created

1. `src/types/notifications.ts` - Type definitions
2. `src/contexts/NotificationContext.tsx` - Notification state management
3. `src/components/notifications/NotificationCenter.tsx` - Toast notifications
4. `src/components/notifications/FileUploadStatus.tsx` - File status tracking
5. `src/components/notifications/index.ts` - Component exports
6. `src/components/notifications/README.md` - Component documentation
7. `src/hooks/useFileProcessing.ts` - File processing hook
8. `src/pages/FileProcessingDemoPage.tsx` - Demo page
9. `apps/frontend/NOTIFICATION_SYSTEM.md` - This document

## Files Modified

1. `src/app.tsx` - Added NotificationProvider and NotificationCenter
2. `src/hooks/index.ts` - Added useFileProcessing export
3. `src/i18n/es.ts` - Added notification translations

## Next Steps

To complete the integration:

1. **Connect to Backend API**: Replace the placeholder `pollFileStatus` function with actual API calls
2. **Integrate with Chat**: Add file upload notifications to the chat interface
3. **Add WebSocket Support**: Implement real-time notifications (optional subtask 5.3)
4. **Testing**: Add unit tests for notification components and hooks
5. **Error Handling**: Enhance error messages with more specific guidance

## Testing

To test the notification system:

1. Start the development server: `npm run dev`
2. Navigate to `/demo-notifications`
3. Use the demo buttons to simulate different scenarios
4. Verify notifications appear in the top-right corner
5. Verify file processing status displays correctly
6. Test retry, cancel, and dismiss actions

## Notes

- Error notifications do not auto-dismiss to ensure users see important errors
- File processing polling is disabled when no files are actively processing
- The system supports multiple simultaneous file uploads
- All text is in Latin American Spanish as per requirements
- Uses Cloudscape Design System components exclusively

import React from 'react';
import { Alert, Box, Button, SpaceBetween } from '@cloudscape-design/components';

export type ErrorSeverity = 'error' | 'warning' | 'info';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  severity?: ErrorSeverity;
  onRetry?: () => void;
  onDismiss?: () => void;
  dismissible?: boolean;
  retryLabel?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title = 'Error',
  message,
  severity = 'error',
  onRetry,
  onDismiss,
  dismissible = false,
  retryLabel = 'Reintentar'
}) => (
  <Alert
    type={severity}
    header={title}
    dismissible={dismissible}
    onDismiss={onDismiss}
    action={
      onRetry ? (
        <Button onClick={onRetry} variant="primary">
          {retryLabel}
        </Button>
      ) : undefined
    }
  >
    {message}
  </Alert>
);

interface InlineErrorProps {
  message: string;
  onRetry?: () => void;
}

export const InlineError: React.FC<InlineErrorProps> = ({ message, onRetry }) => (
  <Box color="text-status-error" fontSize="body-s">
    <SpaceBetween direction="horizontal" size="xs">
      <span>⚠️ {message}</span>
      {onRetry && (
        <Button variant="inline-link" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </SpaceBetween>
  </Box>
);

interface FullPageErrorProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onGoBack?: () => void;
}

export const FullPageError: React.FC<FullPageErrorProps> = ({
  title = 'Ha ocurrido un error',
  message,
  onRetry,
  onGoBack
}) => (
  <Box textAlign="center" padding="xxl" margin={{ vertical: 'xxl' }}>
    <Box fontSize="heading-xl" fontWeight="bold" margin={{ bottom: 's' }}>
      {title}
    </Box>
    <Box variant="p" color="text-body-secondary" margin={{ bottom: 'l' }}>
      {message}
    </Box>
    <SpaceBetween direction="horizontal" size="s">
      {onGoBack && (
        <Button onClick={onGoBack}>
          Volver
        </Button>
      )}
      {onRetry && (
        <Button variant="primary" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </SpaceBetween>
  </Box>
);

interface NetworkErrorProps {
  onRetry?: () => void;
  isOffline?: boolean;
}

export const NetworkError: React.FC<NetworkErrorProps> = ({ 
  onRetry,
  isOffline = false 
}) => (
  <ErrorDisplay
    title={isOffline ? 'Sin conexión' : 'Error de red'}
    message={
      isOffline
        ? 'No hay conexión a internet. Por favor, verifica tu conexión y vuelve a intentarlo.'
        : 'No se pudo conectar con el servidor. Por favor, verifica tu conexión e intenta nuevamente.'
    }
    severity="error"
    onRetry={onRetry}
    retryLabel="Reintentar"
  />
);

interface ValidationErrorProps {
  errors: string[];
  onDismiss?: () => void;
}

export const ValidationError: React.FC<ValidationErrorProps> = ({ 
  errors,
  onDismiss 
}) => (
  <Alert
    type="error"
    header="Errores de validación"
    dismissible={!!onDismiss}
    onDismiss={onDismiss}
  >
    <ul style={{ margin: 0, paddingLeft: '20px' }}>
      {errors.map((error, index) => (
        <li key={index}>{error}</li>
      ))}
    </ul>
  </Alert>
);

/**
 * ErrorState Component
 * Enhanced error display for chat interactions
 */

import { Box, Alert, Button, SpaceBetween, Icon } from '@cloudscape-design/components';

interface ErrorStateProps {
  error: string;
  type?: 'connection' | 'processing' | 'validation' | 'general';
  onRetry?: () => void;
  onDismiss?: () => void;
  retryable?: boolean;
}

export function ErrorState({ 
  error, 
  type = 'general', 
  onRetry, 
  onDismiss, 
  retryable = true 
}: ErrorStateProps) {
  
  const getErrorConfig = () => {
    switch (type) {
      case 'connection':
        return {
          icon: 'status-warning' as const,
          title: 'Connection Error',
          description: 'Unable to connect to the AI service. Please check your internet connection.',
          actionText: 'Retry Connection'
        };
      case 'processing':
        return {
          icon: 'status-negative' as const,
          title: 'Processing Error',
          description: 'The AI encountered an error while processing your request.',
          actionText: 'Try Again'
        };
      case 'validation':
        return {
          icon: 'status-info' as const,
          title: 'Invalid Request',
          description: 'Please check your input and try again.',
          actionText: 'Retry'
        };
      default:
        return {
          icon: 'status-negative' as const,
          title: 'Error',
          description: 'An unexpected error occurred.',
          actionText: 'Retry'
        };
    }
  };

  const config = getErrorConfig();

  return (
    <Box padding="s" variant="div">
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '12px',
          alignItems: 'flex-start'
        }}
      >
        {/* Error Avatar */}
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: '#d91515',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          <Icon name={config.icon} variant="inverted" size="medium" />
        </div>

        {/* Error Content */}
        <div style={{ flex: 1 }}>
          <Alert
            type="error"
            header={config.title}
            dismissible={!!onDismiss}
            onDismiss={onDismiss}
            action={
              retryable && onRetry ? (
                <Button onClick={onRetry} variant="primary">
                  {config.actionText}
                </Button>
              ) : undefined
            }
          >
            <SpaceBetween size="s">
              <Box>{config.description}</Box>
              {error && (
                <Box fontSize="body-s" color="text-body-secondary">
                  <strong>Details:</strong> {error}
                </Box>
              )}
            </SpaceBetween>
          </Alert>
        </div>
      </div>
    </Box>
  );
}

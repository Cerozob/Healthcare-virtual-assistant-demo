/**
 * Error Boundary Component
 * Catches JavaScript errors in component tree and provides fallback UI
 */

import { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Box, Button, Container, Header, SpaceBetween } from '@cloudscape-design/components';
import { ErrorHandler } from '../../utils/errorHandler';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo, errorId: string) => void;
  showDetails?: boolean;
  context?: string;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Generate unique error ID for tracking
    const errorId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      errorInfo,
    });

    // Log error details
    console.error('Error Boundary caught an error:', {
      error,
      errorInfo,
      errorId: this.state.errorId,
      context: this.props.context,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo, this.state.errorId);
    }

    // Report error to monitoring service (if available)
    this.reportError(error, errorInfo);
  }

  private reportError(error: Error, errorInfo: ErrorInfo) {
    // This would integrate with error monitoring services like Sentry, LogRocket, etc.
    // For now, we'll just log to console
    const errorDetails = ErrorHandler.getErrorDetails(error, this.props.context);
    
    console.error('Error Boundary Report:', {
      errorId: this.state.errorId,
      context: this.props.context,
      errorDetails,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    });
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Container
          header={
            <Header variant="h2">
              Ha ocurrido un error inesperado
            </Header>
          }
        >
          <SpaceBetween size="l">
            <Alert
              type="error"
              header="Error en la aplicación"
              action={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={this.handleRetry}>
                    Intentar nuevamente
                  </Button>
                  <Button variant="primary" onClick={this.handleReload}>
                    Recargar página
                  </Button>
                </SpaceBetween>
              }
            >
              <Box>
                La aplicación ha encontrado un error y no puede continuar. 
                Puede intentar nuevamente o recargar la página para resolver el problema.
              </Box>
              
              {this.props.showDetails && this.state.error && (
                <Box margin={{ top: 'm' }}>
                  <details>
                    <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                      Detalles técnicos (para soporte)
                    </summary>
                    <Box margin={{ top: 's' }} fontSize="body-s">
                      <Box>
                        <strong>ID del Error:</strong> {this.state.errorId}
                      </Box>
                      <Box margin={{ top: 'xs' }}>
                        <strong>Mensaje:</strong> {this.state.error.message}
                      </Box>
                      <Box margin={{ top: 'xs' }}>
                        <strong>Contexto:</strong> {this.props.context || 'No especificado'}
                      </Box>
                      <Box margin={{ top: 'xs' }}>
                        <strong>Timestamp:</strong> {new Date().toLocaleString('es-MX')}
                      </Box>
                      {this.state.error.stack && (
                        <Box margin={{ top: 'xs' }}>
                          <strong>Stack Trace:</strong>
                          <pre style={{ 
                            fontSize: '12px', 
                            overflow: 'auto', 
                            maxHeight: '200px',
                            backgroundColor: '#f5f5f5',
                            padding: '8px',
                            borderRadius: '4px',
                            marginTop: '4px'
                          }}>
                            {this.state.error.stack}
                          </pre>
                        </Box>
                      )}
                    </Box>
                  </details>
                </Box>
              )}
            </Alert>

            <Alert type="info">
              <Box>
                <strong>¿Qué puede hacer?</strong>
                <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                  <li>Haga clic en "Intentar nuevamente" para volver a cargar el componente</li>
                  <li>Recargue la página completa si el problema persiste</li>
                  <li>Verifique su conexión a internet</li>
                  <li>Si el problema continúa, contacte al soporte técnico con el ID del error</li>
                </ul>
              </Box>
            </Alert>
          </SpaceBetween>
        </Container>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component for wrapping components with error boundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, 'children'>
) {
  const WithErrorBoundaryComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  );

  WithErrorBoundaryComponent.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithErrorBoundaryComponent;
}

/**
 * Specialized error boundary for file operations
 */
export function FileOperationErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      context="File Operations"
      showDetails={true}
      fallback={
        <Alert
          type="error"
          header="Error en operación de archivos"
          action={
            <Button onClick={() => window.location.reload()}>
              Recargar página
            </Button>
          }
        >
          <Box>
            Ha ocurrido un error durante la operación con archivos. 
            Por favor, recargue la página e intente nuevamente.
          </Box>
        </Alert>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

/**
 * Specialized error boundary for preview operations
 */
export function PreviewErrorBoundary({ children, onRetry }: { children: ReactNode; onRetry?: () => void }) {
  return (
    <ErrorBoundary
      context="File Preview"
      showDetails={false}
      fallback={
        <Alert
          type="error"
          header="Error en vista previa"
          action={
            onRetry ? (
              <Button onClick={onRetry}>
                Intentar nuevamente
              </Button>
            ) : undefined
          }
        >
          <Box>
            No se pudo cargar la vista previa del archivo. 
            {onRetry ? ' Puede intentar nuevamente o' : ' Puede'} descargar el archivo para verlo externamente.
          </Box>
        </Alert>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

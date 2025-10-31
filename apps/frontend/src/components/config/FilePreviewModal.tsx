/**
 * FilePreviewModal Component
 * Modal container for file content preview with appropriate viewers
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Header,
  Modal,
  SpaceBetween,
  Spinner,
} from '@cloudscape-design/components';
import { CodeView } from '@cloudscape-design/code-view';

import { useState, useEffect, useRef } from 'react';
import type { UnifiedFile, PreviewState } from '../../types/unifiedFile';
import { FileError } from '../../types/unifiedFile';
import { FileTypeDetector } from '../../utils/fileTypeDetector';
import { processedFileService } from '../../services/processedFileService';
import { MarkdownRenderer } from '../chat/MarkdownRenderer';

import { blobUrlManager } from '../../utils/blobUrlManager';
import { ErrorHandler } from '../../utils/errorHandler';
import { createFileOperationRetryManager } from '../../utils/retryManager';
import { useFileOperationNotifications } from '../common/NotificationSystem';
import { PreviewErrorBoundary } from '../common/ErrorBoundary';

export interface FilePreviewModalProps {
  visible: boolean;
  file: UnifiedFile | null;
  onDismiss: () => void;
  onDownload: (file: UnifiedFile) => void;
}

export function FilePreviewModal({
  visible,
  file,
  onDismiss,
  onDownload,
}: FilePreviewModalProps) {
  const notifications = useFileOperationNotifications();
  const [previewState, setPreviewState] = useState<PreviewState>({
    loading: false,
    content: null,
    error: null,
  });
  const [retryCount, setRetryCount] = useState<number>(0);
  const [showSizeWarning, setShowSizeWarning] = useState<boolean>(false);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);

  const [retryManager] = useState(() => createFileOperationRetryManager({
    onRetryAttempt: (attempt, _delay, _error) => {
      setIsRetrying(true);
      setRetryCount(attempt);
      notifications.notifyRetryAttempt(file?.name || 'archivo', attempt, 3);
    },
    onRetrySuccess: (attempt) => {
      setIsRetrying(false);
      if (attempt > 1) {
        notifications.notifyPreviewSuccess(file?.name || 'archivo');
      }
    },
    onRetryFailed: (error, _totalAttempts) => {
      setIsRetrying(false);
      if (file) {
        notifications.notifyPreviewError(file.name, error);
      }
    },
  }));
  const abortControllerRef = useRef<AbortController | null>(null);
  const isFirstLoadRef = useRef<boolean>(true);
  const shouldAutoLoadRef = useRef<boolean>(false);
  const loadContentRef = useRef<(() => void) | null>(null);

  // Cleanup blob URL when component unmounts or file changes
  useEffect(() => {
    return () => {
      if (file) {
        blobUrlManager.revokeBlobUrl(file.id);
      }
    };
  }, [file]);

  const loadFileContent = async () => {
    if (!file) return;

    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();

    // Validate file for preview
    const validation = FileTypeDetector.validateFileForPreview(file.name, file.size);
    if (!validation.supported) {
      const errorDetails = ErrorHandler.getErrorDetails(FileError.UNSUPPORTED_TYPE, 'Vista previa');
      setPreviewState({
        loading: false,
        content: null,
        error: validation.reason || errorDetails.userMessage,
      });

      // Show unsupported file type notification
      notifications.notifyUnsupportedFileType(file.name, file.type);
      return;
    }

    setPreviewState({
      loading: true,
      content: null,
      error: null,
    });

    try {
      // Use retry manager for robust file loading
      const result = await retryManager.execute(async () => {
        // Load file content using the service (simplified)
        const serviceResult = await processedFileService.getFileContent(file);

        if (!serviceResult.success) {
          // Convert service error to throwable error for retry manager
          const errorDetails = ErrorHandler.getErrorDetails(
            serviceResult.error?.type || FileError.NETWORK_ERROR,
            'Carga de archivo'
          );
          throw new Error(errorDetails.userMessage);
        }

        if (!serviceResult.data) {
          throw new Error('No se pudo obtener el contenido del archivo');
        }

        return serviceResult.data;
      });

      // Create blob URL for media files if needed
      if (result.content instanceof Blob) {
        const newBlobUrl = blobUrlManager.createBlobUrl(result.content, file.id);
        setBlobUrl(newBlobUrl);
      } else {
        setBlobUrl(null);
      }

      setPreviewState({
        loading: false,
        content: result,
        error: null,
        loadedAt: new Date().toISOString(),
      });

      // Reset retry count on success
      setRetryCount(0);
      setIsRetrying(false);

      // Show success notification for first load
      if (isFirstLoadRef.current) {
        notifications.notifyPreviewSuccess(file.name);
        isFirstLoadRef.current = false;
      }

    } catch (error) {
      console.error('Error loading file content:', error);

      // Handle abort errors gracefully
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }

      // Get enhanced error details
      const errorDetails = ErrorHandler.getErrorDetails(error, 'Vista previa');

      setPreviewState({
        loading: false,
        content: null,
        error: errorDetails.userMessage,
      });

      // Show error notification
      notifications.notifyPreviewError(file.name, errorDetails.userMessage);

    } finally {
      abortControllerRef.current = null;
    }
  };

  // Store the function in a ref to avoid dependency issues
  loadContentRef.current = loadFileContent;

  // Reset preview state when file changes
  useEffect(() => {
    if (!file || !visible) {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }

      // Cleanup blob URL
      if (file) {
        blobUrlManager.revokeBlobUrl(file.id);
      }
      setBlobUrl(null);

      setPreviewState({
        loading: false,
        content: null,
        error: null,
      });
      setRetryCount(0);
      setShowSizeWarning(false);
      isFirstLoadRef.current = true;
      shouldAutoLoadRef.current = false;
      return;
    }

    // Check if file size warning should be shown, but don't load content yet
    const previewConfig = FileTypeDetector.getPreviewConfig(file.name);
    const maxSize = previewConfig?.maxSize || 5 * 1024 * 1024; // 5MB default
    const warningThreshold = Math.max(maxSize * 0.5, 2 * 1024 * 1024); // 50% of max or 2MB minimum

    if (file.size > warningThreshold) {
      setShowSizeWarning(true);
    } else {
      // For small files, auto-load content
      setShowSizeWarning(false);
      shouldAutoLoadRef.current = true;
      // Auto-load content after a short delay
      setTimeout(() => {
        if (shouldAutoLoadRef.current && loadContentRef.current) {
          loadContentRef.current();
          shouldAutoLoadRef.current = false;
        }
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, visible]);



  const handleSizeWarningProceed = () => {
    setShowSizeWarning(false);
    // Now load the content since user confirmed
    loadFileContent();
  };

  const handleSizeWarningCancel = () => {
    setShowSizeWarning(false);
    // Don't load content, just close the warning
  };

  const handleRetry = async () => {
    if (!file || !retryManager.canRetry()) {
      return;
    }

    try {
      setIsRetrying(true);
      await loadFileContent(); // Retry loading
    } catch (error) {
      console.error('Manual retry failed:', error);
      const errorDetails = ErrorHandler.getErrorDetails(error, 'Reintento manual');
      notifications.notifyPreviewError(file.name, errorDetails.userMessage);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    setPreviewState({
      loading: false,
      content: null,
      error: null,
    });
  };

  const renderViewer = () => {
    if (!file || !previewState.content) return null;

    const previewConfig = FileTypeDetector.getPreviewConfig(file.name);
    if (!previewConfig) return null;

    // Handle blob content for media files (images)
    if (previewState.content.content instanceof Blob) {
      if (!blobUrl) {
        return <div>Loading...</div>;
      }



      return (
        <img
          src={blobUrl}
          alt={file.name}
          style={{ maxWidth: '100%', maxHeight: '600px' }}
        />
      );
    }

    // Handle text-based content
    const content = previewState.content.content as string;
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    
    // Check if this is a markdown result file from BDS
    const isMarkdownResult = file.name.includes('markdown_result.txt') || 
                            file.name.endsWith('_markdown.txt') ||
                            fileExtension === 'md' || 
                            fileExtension === 'markdown';

    // Markdown files (including BDS markdown results)
    if (isMarkdownResult) {
      // Handle empty content
      if (!content || content.trim().length === 0) {
        return (
          <Alert type="info">
            El archivo Markdown está vacío.
          </Alert>
        );
      }

      // Handle very large content (show warning)
      const isLargeFile = content.length > 200000; // 200KB
      const displayContent = isLargeFile
        ? `${content.substring(0, 200000)}\n\n---\n\n*... (contenido truncado)*`
        : content;

      // Count markdown elements for info display
      const lineCount = content.split('\n').length;
      const wordCount = content.split(/\s+/).filter(word => word.length > 0).length;
      const headingCount = (content.match(/^#+\s/gm) || []).length;

      return (
        <SpaceBetween size="m">
          {isLargeFile && (
            <Alert type="warning">
              <strong>Archivo grande detectado:</strong> Solo se muestran los primeros 200KB del contenido.
              Descargue el archivo para ver el contenido completo.
            </Alert>
          )}

          <Box>
            <Header
              variant="h3"
              description={`Archivo Markdown: ${file.name}`}
            >
              Contenido renderizado
            </Header>
          </Box>

          <Container>
            <Box padding="m">
              <MarkdownRenderer
                content={displayContent}
                className="file-preview-markdown"
              />
            </Box>
          </Container>

          <Box fontSize="body-s" color="text-status-info">
            <SpaceBetween direction="horizontal" size="l">
              <span>
                <strong>Líneas:</strong> {lineCount}
              </span>
              <span>
                <strong>Palabras:</strong> {wordCount}
              </span>
              <span>
                <strong>Encabezados:</strong> {headingCount}
              </span>
              <span>
                <strong>Caracteres:</strong> {content.length}
              </span>
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      );
    }

    // HTML files - display as code for now
    if (fileExtension === 'html' || fileExtension === 'htm') {
      return (
        <SpaceBetween size="m">
          <Box>
            <Header 
              variant="h3" 
              description={`Archivo HTML: ${file.name}`}
            >
              Código HTML
            </Header>
          </Box>
          <CodeView
            content={content}
            lineNumbers
            wrapLines
          />
        </SpaceBetween>
      );
    }

    // JSON files - format if valid
    if (fileExtension === 'json') {
      let formattedContent: string;
      try {
        const parsed = JSON.parse(content);
        formattedContent = JSON.stringify(parsed, null, 2);
      } catch {
        formattedContent = content;
      }

      return (
        <CodeView
          content={formattedContent}
          lineNumbers
          wrapLines
        />
      );
    }

    // All other text files
    return (
      <CodeView
        content={content}
        lineNumbers
        wrapLines
      />
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round(bytes / k ** i * 100) / 100} ${sizes[i]}`;
  };

  const getSourceLabel = (source: string): string => {
    return source === 'raw' ? 'Archivo original' : 'Archivo procesado';
  };

  if (!file) return null;

  return (
    <Modal
      visible={visible}
      onDismiss={onDismiss}
      header={`Vista previa: ${file.name}`}
      size="max"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onDismiss}>
              Cerrar
            </Button>
            <Button
              variant="primary"
              iconName="download"
              onClick={() => onDownload(file)}
              disabled={previewState.loading}
            >
              Descargar archivo
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <PreviewErrorBoundary onRetry={() => file && loadFileContent()}>
        <SpaceBetween size="l">
          {/* File metadata */}
          <Container
            header={<Header variant="h3">Información del archivo</Header>}
          >
            <SpaceBetween size="s">
              <Box>
                <strong>Nombre:</strong> {file.name}
              </Box>
              <Box>
                <strong>Tamaño:</strong> {formatFileSize(file.size)}
              </Box>
              <Box>
                <strong>Tipo:</strong> {file.type}
              </Box>
              <Box>
                <strong>Fuente:</strong> {getSourceLabel(file.source)}
              </Box>
              <Box>
                <strong>Paciente:</strong> {file.patientId}
              </Box>
              {previewState.loadedAt && (
                <Box>
                  <strong>Cargado:</strong> {new Date(previewState.loadedAt).toLocaleString('es-MX')}
                </Box>
              )}
            </SpaceBetween>
          </Container>

          {/* File size warning */}
          {showSizeWarning && (
            <Alert
              type="warning"
              header="Archivo grande detectado"
              action={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button variant="link" onClick={handleSizeWarningCancel}>
                    Cancelar
                  </Button>
                  <Button variant="primary" onClick={handleSizeWarningProceed}>
                    Continuar con vista previa
                  </Button>
                  <Button iconName="download" onClick={() => file && onDownload(file)}>
                    Descargar archivo
                  </Button>
                </SpaceBetween>
              }
            >
              <SpaceBetween size="s">
                <Box>
                  El archivo <strong>{file.name}</strong> ({formatFileSize(file.size)}) es más grande
                  de lo recomendado para vista previa. La carga puede ser lenta o fallar.
                </Box>
                <Box>
                  <strong>Opciones disponibles:</strong>
                  <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                    <li><strong>Continuar:</strong> Intentar cargar la vista previa (puede ser lento)</li>
                    <li><strong>Descargar:</strong> Descargar el archivo para verlo externamente (recomendado)</li>
                    <li><strong>Cancelar:</strong> Volver sin realizar ninguna acción</li>
                  </ul>
                </Box>
              </SpaceBetween>
            </Alert>
          )}

          {/* Preview content */}
          {!showSizeWarning && (
            <Container
              header={
                <Header
                  variant="h3"
                  actions={
                    previewState.loading ? (
                      <Button
                        variant="link"
                        iconName="close"
                        onClick={handleCancel}
                      >
                        Cancelar
                      </Button>
                    ) : !previewState.content && !previewState.error ? (
                      <Button
                        variant="primary"
                        iconName="search"
                        onClick={loadFileContent}
                      >
                        Cargar vista previa
                      </Button>
                    ) : null
                  }
                >
                  Vista previa del contenido
                </Header>
              }
            >
              {previewState.loading && (
                <Box textAlign="center" padding="l">
                  <SpaceBetween size="m" alignItems="center">
                    <Spinner size="large" />
                    <Box>
                      {isRetrying
                        ? `Reintentando carga (intento ${retryCount})...`
                        : 'Cargando contenido del archivo...'
                      }
                    </Box>
                    <SpaceBetween direction="horizontal" size="l">
                      <Box variant="small" color="text-status-info">
                        Tamaño: {formatFileSize(file?.size || 0)}
                      </Box>
                      <Box variant="small" color="text-status-info">
                        Tipo: {file?.type}
                      </Box>
                      <Box variant="small" color="text-status-info">
                        Fuente: {file?.source === 'raw' ? 'Original' : 'Procesado'}
                      </Box>
                      {isRetrying && (
                        <Box variant="small" color="text-status-warning">
                          Reintentando...
                        </Box>
                      )}
                    </SpaceBetween>
                  </SpaceBetween>
                </Box>
              )}

              {previewState.error && (
                <Alert
                  type="error"
                  header="Error al cargar vista previa"
                  action={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button
                        onClick={handleRetry}
                        iconName="refresh"
                        disabled={!retryManager.canRetry() || isRetrying}
                        loading={isRetrying}
                      >
                        {!retryManager.canRetry()
                          ? 'Máximo de reintentos alcanzado'
                          : isRetrying
                            ? 'Reintentando...'
                            : `Reintentar (${retryManager.getRemainingAttempts()} restantes)`
                        }
                      </Button>
                      <Button
                        variant="primary"
                        iconName="download"
                        onClick={() => file && onDownload(file)}
                      >
                        Descargar archivo
                      </Button>
                    </SpaceBetween>
                  }
                >
                  {previewState.error}
                  <Box margin={{ top: 's' }}>
                    {retryCount > 0 && (
                      <Box variant="small" color="text-status-info">
                        Intentos realizados: {retryCount}/{retryManager.getState().maxAttempts}
                      </Box>
                    )}
                    <Box margin={{ top: 'xs' }}>
                      <strong>Sugerencias:</strong>
                      <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                        <li>Verifique su conexión a internet</li>
                        <li>Descargue el archivo para verlo en una aplicación externa</li>
                        <li>Intente nuevamente en unos momentos</li>
                        {file && file.size > 10 * 1024 * 1024 && (
                          <li>El archivo es grande ({formatFileSize(file.size)}), considere usar la descarga</li>
                        )}
                      </ul>
                    </Box>
                  </Box>
                </Alert>
              )}

              {!previewState.loading && !previewState.error && previewState.content && (
                <Box>
                  {renderViewer()}
                </Box>
              )}

              {!previewState.loading && !previewState.error && !previewState.content && (
                <Box textAlign="center" padding="l">
                  <SpaceBetween size="m" alignItems="center">
                    <Box fontSize="heading-m" color="text-status-info">
                      Vista previa no cargada
                    </Box>
                    <Box>
                      Haga clic en "Cargar vista previa" para ver el contenido del archivo.
                    </Box>
                    <Button
                      variant="primary"
                      iconName="search"
                      onClick={loadFileContent}
                    >
                      Cargar vista previa
                    </Button>
                  </SpaceBetween>
                </Box>
              )}
            </Container>
          )}
        </SpaceBetween>
      </PreviewErrorBoundary>
    </Modal>
  );
}

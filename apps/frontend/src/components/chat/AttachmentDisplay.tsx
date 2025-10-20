/**
 * AttachmentDisplay Component
 * Displays file attachments from AI responses with download and preview functionality
 */

import { Box, Button, Icon, SpaceBetween } from '@cloudscape-design/components';

export interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  processingStatus?: 'pending' | 'processing' | 'completed' | 'failed';
}

interface AttachmentDisplayProps {
  attachments: FileAttachment[];
  onDownload?: (attachment: FileAttachment) => void;
  onPreview?: (attachment: FileAttachment) => void;
}

export function AttachmentDisplay({ 
  attachments, 
  onDownload,
  onPreview 
}: AttachmentDisplayProps) {
  if (!attachments || attachments.length === 0) {
    return null;
  }

  // Get icon name based on file type
  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return 'file' as const;
    if (type.includes('image')) return 'file' as const;
    if (type.includes('video')) return 'file' as const;
    if (type.includes('audio')) return 'file' as const;
    if (type.includes('word') || type.includes('document')) return 'file' as const;
    if (type.includes('excel') || type.includes('spreadsheet')) return 'file' as const;
    return 'file' as const;
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Get status color
  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return '#037f0c';
      case 'processing': return '#0972d3';
      case 'failed': return '#d91515';
      case 'pending': return '#8d6605';
      default: return '#5f6b7a';
    }
  };

  // Handle download
  const handleDownload = (attachment: FileAttachment) => {
    if (onDownload) {
      onDownload(attachment);
    } else {
      // Default download behavior
      const link = document.createElement('a');
      link.href = attachment.url;
      link.download = attachment.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  // Handle preview
  const handlePreview = (attachment: FileAttachment) => {
    if (onPreview) {
      onPreview(attachment);
    } else {
      // Default preview behavior - open in new tab
      window.open(attachment.url, '_blank');
    }
  };

  // Check if file can be previewed
  const canPreview = (type: string): boolean => {
    return type.includes('image') || type.includes('pdf') || type.includes('text');
  };

  return (
    <Box padding={{ top: 's' }}>
      <SpaceBetween size="xs">
        {attachments.map((attachment) => (
          <div
            key={attachment.id}
            style={{
              border: '1px solid #e9ebed',
              borderRadius: '8px',
              padding: '12px',
              backgroundColor: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            {/* File Icon */}
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '4px',
                backgroundColor: '#f2f8fd',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <Icon name={getFileIcon(attachment.type)} size="medium" />
            </div>

            {/* File Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <Box fontSize="body-m" fontWeight="bold">
                {attachment.name}
              </Box>
              <Box fontSize="body-s" color="text-body-secondary">
                {formatFileSize(attachment.size)}
                {attachment.processingStatus && (
                  <span
                    style={{
                      marginLeft: '8px',
                      color: getStatusColor(attachment.processingStatus)
                    }}
                  >
                    • {attachment.processingStatus === 'completed' ? 'Completado' :
                       attachment.processingStatus === 'processing' ? 'Procesando' :
                       attachment.processingStatus === 'failed' ? 'Fallido' :
                       attachment.processingStatus === 'pending' ? 'Pendiente' :
                       attachment.processingStatus}
                  </span>
                )}
              </Box>
            </div>

            {/* Actions */}
            <SpaceBetween direction="horizontal" size="xs">
              {canPreview(attachment.type) && (
                <Button
                  variant="inline-icon"
                  iconName="view-full"
                  ariaLabel="Vista previa"
                  onClick={() => handlePreview(attachment)}
                />
              )}
              <Button
                variant="inline-icon"
                iconName="download"
                ariaLabel="Descargar"
                onClick={() => handleDownload(attachment)}
              />
            </SpaceBetween>
          </div>
        ))}
      </SpaceBetween>
    </Box>
  );
}

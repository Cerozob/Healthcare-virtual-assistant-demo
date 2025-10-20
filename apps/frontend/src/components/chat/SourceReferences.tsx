/**
 * SourceReferences Component
 * Displays external source citations with clickable links and metadata
 */

import { Box, Icon, SpaceBetween, Link } from '@cloudscape-design/components';

export interface ExternalSource {
  title: string;
  url: string;
  description?: string;
  type: 'document' | 'website' | 'database';
}

interface SourceReferencesProps {
  sources: ExternalSource[];
  onSourceClick?: (source: ExternalSource) => void;
}

export function SourceReferences({ 
  sources, 
  onSourceClick 
}: SourceReferencesProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  // Get icon based on source type
  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'document': return 'file' as const;
      case 'website': return 'external' as const;
      case 'database': return 'folder' as const;
      default: return 'status-info' as const;
    }
  };

  // Get source type label
  const getSourceTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      document: 'Documento',
      website: 'Sitio web',
      database: 'Base de datos'
    };
    return labels[type] || type;
  };

  // Handle source click
  const handleSourceClick = (source: ExternalSource) => {
    if (onSourceClick) {
      onSourceClick(source);
    } else {
      // Default behavior - open in new tab
      window.open(source.url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <Box padding={{ top: 's' }}>
      <Box
        padding={{ bottom: 'xs' }}
        fontSize="body-s"
        fontWeight="bold"
        color="text-label"
      >
        Fuentes
      </Box>
      <SpaceBetween size="xs">
        {sources.map((source, index) => (
          <div
            key={`${source.url}-${index}`}
            style={{
              border: '1px solid #e9ebed',
              borderRadius: '8px',
              padding: '12px',
              backgroundColor: '#fafafa',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}
          >
            {/* Source Type Icon */}
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '4px',
                backgroundColor: '#ffffff',
                border: '1px solid #e9ebed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <Icon name={getSourceIcon(source.type)} size="medium" />
            </div>

            {/* Source Info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {/* Source Title */}
              <Box fontSize="body-m" fontWeight="bold">
                <Link
                  href={source.url}
                  external
                  onFollow={(e) => {
                    e.preventDefault();
                    handleSourceClick(source);
                  }}
                >
                  {source.title}
                </Link>
              </Box>

              {/* Source Type Badge */}
              <Box fontSize="body-s" color="text-body-secondary" padding={{ top: 'xxs' }}>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: '#e9ebed',
                    fontSize: '12px'
                  }}
                >
                  {getSourceTypeLabel(source.type)}
                </span>
              </Box>

              {/* Source Description */}
              {source.description && (
                <Box 
                  fontSize="body-s" 
                  color="text-body-secondary" 
                  padding={{ top: 'xs' }}
                >
                  {source.description}
                </Box>
              )}

              {/* Source URL */}
              <div 
                style={{ 
                  fontSize: '12px',
                  color: '#5f6b7a',
                  marginTop: '4px',
                  wordBreak: 'break-all',
                  opacity: 0.7
                }}
              >
                {source.url}
              </div>
            </div>
          </div>
        ))}
      </SpaceBetween>
    </Box>
  );
}

import React from 'react';
import { Spinner, Box, ProgressBar } from '@cloudscape-design/components';

interface LoadingSpinnerProps {
  size?: 'normal' | 'big' | 'large';
  variant?: 'normal' | 'disabled';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'normal',
  variant = 'normal'
}) => (
  <Box textAlign="center" padding="l">
    <Spinner size={size} variant={variant} />
  </Box>
);

interface FullPageLoadingProps {
  message?: string;
}

export const FullPageLoading: React.FC<FullPageLoadingProps> = ({ 
  message = 'Cargando...' 
}) => (
  <Box 
    textAlign="center" 
    padding="xxl"
    margin={{ vertical: 'xxl' }}
  >
    <Spinner size="large" />
    {message && (
      <Box variant="p" color="text-body-secondary" margin={{ top: 's' }}>
        {message}
      </Box>
    )}
  </Box>
);

interface InlineLoadingProps {
  message?: string;
}

export const InlineLoading: React.FC<InlineLoadingProps> = ({ 
  message = 'Cargando...' 
}) => (
  <Box display="inline-block">
    <Spinner size="normal" /> {message}
  </Box>
);

interface SkeletonTextProps {
  lines?: number;
}

export const SkeletonText: React.FC<SkeletonTextProps> = ({ lines = 3 }) => (
  <Box>
    {Array.from({ length: lines }).map((_, index) => (
      <Box
        key={index}
        margin={{ bottom: 's' }}
        padding="s"
        color="text-body-secondary"
      >
        <Box 
          color='text-body-secondary'
          padding="xs"
        />
      </Box>
    ))}
  </Box>
);

interface ProgressLoadingProps {
  value: number;
  label?: string;
  description?: string;
}

export const ProgressLoading: React.FC<ProgressLoadingProps> = ({
  value,
  label = 'Procesando...',
  description
}) => (
  <Box>
    <Box variant="p" fontWeight="bold" margin={{ bottom: 'xs' }}>
      {label}
    </Box>
    <Box 
      color='text-status-info'
      padding="xxs"
    >
      <ProgressBar value={value} label="Procesando..." />
    </Box>
    {description && (
      <Box variant="small" color="text-body-secondary" margin={{ top: 'xs' }}>
        {description}
      </Box>
    )}
  </Box>
);

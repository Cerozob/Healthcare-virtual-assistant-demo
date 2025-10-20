# Common Components

This directory contains reusable common components for error handling, loading states, and network status.

## Components

### LoadingStates

Various loading indicators for different use cases:

- **LoadingSpinner**: Basic spinner for inline or centered loading
- **FullPageLoading**: Full-page loading indicator with optional message
- **InlineLoading**: Inline loading indicator with text
- **SkeletonText**: Skeleton placeholder for text content
- **ProgressLoading**: Progress bar with percentage and description

### ErrorDisplay

Error display components with Spanish messages:

- **ErrorDisplay**: Flexible alert-based error display with retry option
- **InlineError**: Compact inline error message
- **FullPageError**: Full-page error display with action buttons
- **NetworkError**: Specialized network error display
- **ValidationError**: Display multiple validation errors in a list

### NetworkStatusIndicator

Automatic network status indicator that shows:
- Offline notification when connection is lost
- Success notification when connection is restored
- Auto-dismisses after 3 seconds

## Hooks

### useApiCall

Custom hook for API calls with built-in error handling and retry logic:

```typescript
const { data, loading, error, execute, retry, reset } = useApiCall(apiFunction, {
  onSuccess: (data) => console.log('Success', data),
  onError: (error) => console.error('Error', error),
  enableRetry: true,
  maxRetries: 3
});
```

### useNetworkStatus

Hook for monitoring network connectivity:

```typescript
const { isOnline, wasOffline } = useNetworkStatus();
```

## Utilities

### errorHandling

Utilities for error parsing and handling:

- **parseApiError**: Parse unknown errors into structured ApiError
- **getErrorMessage**: Get user-friendly Spanish error message
- **isRetryableError**: Check if error should be retried
- **withRetry**: Retry function with exponential backoff

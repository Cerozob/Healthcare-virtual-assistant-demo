/**
 * Datetime utility functions for ISO8601 standardization
 * All datetime handling should use ISO8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)
 */

/**
 * Get current datetime in ISO8601 format
 * @returns Current datetime as ISO8601 string
 */
export function getCurrentISO8601(): string {
  return new Date().toISOString();
}

/**
 * Format a date to ISO8601 string
 * @param date - Date object or date string to format
 * @returns ISO8601 formatted string
 */
export function toISO8601(date: Date | string): string {
  if (typeof date === 'string') {
    return new Date(date).toISOString();
  }
  return date.toISOString();
}

/**
 * Parse ISO8601 string to Date object
 * @param iso8601String - ISO8601 formatted string
 * @returns Date object
 */
export function fromISO8601(iso8601String: string): Date {
  return new Date(iso8601String);
}

/**
 * Format ISO8601 datetime for display (time only)
 * @param iso8601String - ISO8601 formatted string
 * @param locale - Locale for formatting (defaults to 'es-LATAM')
 * @returns Formatted time string
 */
export function formatTimeFromISO8601(iso8601String: string, locale: string = 'es-LATAM'): string {
  const date = fromISO8601(iso8601String);
  return date.toLocaleTimeString(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false // Use 24-hour format as specified in requirements
  });
}

/**
 * Format ISO8601 datetime for display (date only)
 * @param iso8601String - ISO8601 formatted string
 * @param locale - Locale for formatting (defaults to 'es-LATAM')
 * @returns Formatted date string
 */
export function formatDateFromISO8601(iso8601String: string, locale: string = 'es-LATAM'): string {
  const date = fromISO8601(iso8601String);
  return date.toLocaleDateString(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
}

/**
 * Format ISO8601 datetime for display (full datetime)
 * @param iso8601String - ISO8601 formatted string
 * @param locale - Locale for formatting (defaults to 'es-LATAM')
 * @returns Formatted datetime string
 */
export function formatDateTimeFromISO8601(iso8601String: string, locale: string = 'es-LATAM'): string {
  const date = fromISO8601(iso8601String);
  return date.toLocaleString(locale, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false // Use 24-hour format as specified in requirements
  });
}

/**
 * Validate if a string is in valid ISO8601 format
 * @param dateString - String to validate
 * @returns True if valid ISO8601 format
 */
export function isValidISO8601(dateString: string): boolean {
  try {
    const date = new Date(dateString);
    return date.toISOString() === dateString;
  } catch {
    return false;
  }
}

/**
 * Generate unique ID with timestamp (using ISO8601)
 * @param prefix - Optional prefix for the ID
 * @returns Unique ID string
 */
export function generateTimestampId(prefix: string = ''): string {
  const timestamp = getCurrentISO8601().replace(/[:.]/g, '').replace('T', '').replace('Z', '');
  return prefix ? `${prefix}-${timestamp}` : timestamp;
}

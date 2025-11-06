/**
 * Debug utilities for safe object serialization and display
 */

/**
 * Safely stringify an object, handling circular references and complex objects
 */
export function safeStringify(obj: any, indent: number = 2): string {
  const seen = new WeakSet();
  
  return JSON.stringify(obj, (key, value) => {
    // Handle null and undefined
    if (value === null) return null;
    if (value === undefined) return '[undefined]';
    
    // Handle functions
    if (typeof value === 'function') {
      return `[Function: ${value.name || 'anonymous'}]`;
    }
    
    // Handle circular references
    if (typeof value === 'object' && value !== null) {
      if (seen.has(value)) {
        return '[Circular Reference]';
      }
      seen.add(value);
      
      // Handle specific object types
      if (value instanceof Date) {
        return value.toISOString();
      }
      
      if (value instanceof Error) {
        return {
          name: value.name,
          message: value.message,
          stack: value.stack
        };
      }
      
      // Handle DOM elements
      if (value instanceof Element) {
        return `[${value.tagName}]`;
      }
      
      // Handle other complex objects
      if (value.constructor && value.constructor !== Object && value.constructor !== Array) {
        return `[${value.constructor.name}]`;
      }
    }
    
    return value;
  }, indent);
}

/**
 * Create a debug-friendly representation of an object
 */
export function createDebugObject(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }
  
  if (typeof obj !== 'object') {
    return obj;
  }
  
  if (Array.isArray(obj)) {
    return obj.map(createDebugObject);
  }
  
  const debugObj: any = {};
  
  for (const [key, value] of Object.entries(obj)) {
    try {
      if (typeof value === 'function') {
        debugObj[key] = `[Function: ${value.name || 'anonymous'}]`;
      } else if (value instanceof Date) {
        debugObj[key] = value.toISOString();
      } else if (value instanceof Error) {
        debugObj[key] = {
          type: 'Error',
          name: value.name,
          message: value.message
        };
      } else if (typeof value === 'object' && value !== null) {
        // Prevent deep nesting
        if (value.constructor === Object || Array.isArray(value)) {
          debugObj[key] = createDebugObject(value);
        } else {
          debugObj[key] = `[${value.constructor?.name || 'Object'}]`;
        }
      } else {
        debugObj[key] = value;
      }
    } catch (error) {
      debugObj[key] = `[Error accessing property: ${error instanceof Error ? error.message : 'unknown'}]`;
    }
  }
  
  return debugObj;
}

/**
 * Log an object safely to console with proper formatting
 */
export function debugLog(label: string, obj: any): void {
  console.group(`🔍 ${label}`);
  
  try {
    // Try native console.log first (best formatting)
    console.log(obj);
    
    // Also provide stringified version for copying
    console.log('Stringified:', safeStringify(obj));
  } catch (error) {
    // Fallback to safe stringify
    console.log('Safe stringify:', safeStringify(createDebugObject(obj)));
  }
  
  console.groupEnd();
}

/**
 * Extract readable text from complex response objects
 */
export function extractResponseText(response: any): string {
  if (typeof response === 'string') {
    return response;
  }
  
  if (!response || typeof response !== 'object') {
    return String(response || '');
  }
  
  // Try common response text fields
  const textFields = ['response', 'content', 'message', 'text', 'data'];
  
  for (const field of textFields) {
    if (response[field] && typeof response[field] === 'string') {
      return response[field];
    }
  }
  
  // If no text field found, return safe stringify
  return safeStringify(response);
}

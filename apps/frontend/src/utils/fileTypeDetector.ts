/**
 * File Type Detection and Preview Configuration Utilities
 * Determines appropriate preview methods based on file characteristics
 */

export interface PreviewConfig {
  component: 'codeview' | 'markdown' | 'container';
  language?: string;
  mediaType?: 'image' | 'pdf';
  maxSize?: number; // Maximum file size in bytes for preview
}

export interface FileTypeInfo {
  extension: string;
  mimeType: string;
  category: 'text' | 'code' | 'document' | 'image' | 'other';
  previewSupported: boolean;
  previewConfig?: PreviewConfig;
}

/**
 * Supported file types with their preview configurations
 */
const SUPPORTED_FILE_TYPES: Record<string, FileTypeInfo> = {
  // Text files
  txt: {
    extension: 'txt',
    mimeType: 'text/plain',
    category: 'text',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'text',
      maxSize: 10 * 1024 * 1024, // 10MB
    },
  },
  log: {
    extension: 'log',
    mimeType: 'text/plain',
    category: 'text',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'text',
      maxSize: 10 * 1024 * 1024, // 10MB
    },
  },
  csv: {
    extension: 'csv',
    mimeType: 'text/csv',
    category: 'text',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'text',
      maxSize: 5 * 1024 * 1024, // 5MB
    },
  },

  // JSON files
  json: {
    extension: 'json',
    mimeType: 'application/json',
    category: 'code',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'json',
      maxSize: 5 * 1024 * 1024, // 5MB
    },
  },

  // HTML files
  html: {
    extension: 'html',
    mimeType: 'text/html',
    category: 'code',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'html',
      maxSize: 5 * 1024 * 1024, // 5MB
    },
  },
  htm: {
    extension: 'htm',
    mimeType: 'text/html',
    category: 'code',
    previewSupported: true,
    previewConfig: {
      component: 'codeview',
      language: 'html',
      maxSize: 5 * 1024 * 1024, // 5MB
    },
  },

  // Markdown files
  md: {
    extension: 'md',
    mimeType: 'text/markdown',
    category: 'document',
    previewSupported: true,
    previewConfig: {
      component: 'markdown',
      maxSize: 2 * 1024 * 1024, // 2MB
    },
  },
  markdown: {
    extension: 'markdown',
    mimeType: 'text/markdown',
    category: 'document',
    previewSupported: true,
    previewConfig: {
      component: 'markdown',
      maxSize: 2 * 1024 * 1024, // 2MB
    },
  },

  // PDF files - preview disabled to prevent unwanted downloads
  pdf: {
    extension: 'pdf',
    mimeType: 'application/pdf',
    category: 'document',
    previewSupported: false,
    previewConfig: {
      component: 'container',
      mediaType: 'pdf',
      maxSize: 50 * 1024 * 1024, // 50MB
    },
  },

  // Image files
  png: {
    extension: 'png',
    mimeType: 'image/png',
    category: 'image',
    previewSupported: true,
    previewConfig: {
      component: 'container',
      mediaType: 'image',
      maxSize: 20 * 1024 * 1024, // 20MB
    },
  },
  jpg: {
    extension: 'jpg',
    mimeType: 'image/jpeg',
    category: 'image',
    previewSupported: true,
    previewConfig: {
      component: 'container',
      mediaType: 'image',
      maxSize: 20 * 1024 * 1024, // 20MB
    },
  },
  jpeg: {
    extension: 'jpeg',
    mimeType: 'image/jpeg',
    category: 'image',
    previewSupported: true,
    previewConfig: {
      component: 'container',
      mediaType: 'image',
      maxSize: 20 * 1024 * 1024, // 20MB
    },
  },
};

/**
 * FileTypeDetector utility class for determining file types and preview configurations
 */
export class FileTypeDetector {
  /**
   * Extract file extension from filename
   */
  static getFileExtension(fileName: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase();
    return extension || '';
  }

  /**
   * Get file type information based on filename
   */
  static getFileTypeInfo(fileName: string): FileTypeInfo | null {
    const extension = this.getFileExtension(fileName);
    return SUPPORTED_FILE_TYPES[extension] || null;
  }

  /**
   * Check if file type is supported for preview
   */
  static isPreviewSupported(fileName: string): boolean {
    const fileTypeInfo = this.getFileTypeInfo(fileName);
    return fileTypeInfo?.previewSupported || false;
  }

  /**
   * Get preview configuration for a file
   */
  static getPreviewConfig(fileName: string): PreviewConfig | null {
    // Special handling for BDS markdown result files
    if (fileName.includes('markdown_result.txt') || fileName.endsWith('_markdown.txt')) {
      return SUPPORTED_FILE_TYPES.md.previewConfig || null;
    }
    
    const fileTypeInfo = this.getFileTypeInfo(fileName);
    return fileTypeInfo?.previewConfig || null;
  }

  /**
   * Check if file size is within preview limits
   */
  static isFileSizeSupported(fileName: string, fileSize: number): boolean {
    const previewConfig = this.getPreviewConfig(fileName);
    if (!previewConfig || !previewConfig.maxSize) {
      return false;
    }
    return fileSize <= previewConfig.maxSize;
  }

  /**
   * Get human-readable file category
   */
  static getFileCategory(fileName: string): string {
    const fileTypeInfo = this.getFileTypeInfo(fileName);
    if (!fileTypeInfo) {
      return 'Archivo desconocido';
    }

    switch (fileTypeInfo.category) {
      case 'text':
        return 'Archivo de texto';
      case 'code':
        return 'Archivo de código';
      case 'document':
        return 'Documento';
      case 'image':
        return 'Imagen';
      default:
        return 'Otro archivo';
    }
  }

  /**
   * Get all supported file extensions
   */
  static getSupportedExtensions(): string[] {
    return Object.keys(SUPPORTED_FILE_TYPES);
  }

  /**
   * Get supported extensions by category
   */
  static getSupportedExtensionsByCategory(category: FileTypeInfo['category']): string[] {
    return Object.entries(SUPPORTED_FILE_TYPES)
      .filter(([, info]) => info.category === category)
      .map(([extension]) => extension);
  }

  /**
   * Validate file for preview based on name and size
   */
  static validateFileForPreview(fileName: string, fileSize: number): {
    supported: boolean;
    reason?: string;
    config?: PreviewConfig;
  } {
    // Check if file type is supported
    if (!this.isPreviewSupported(fileName)) {
      return {
        supported: false,
        reason: `Tipo de archivo no soportado para vista previa. Tipos soportados: ${this.getSupportedExtensions().join(', ')}`,
      };
    }

    // Check file size limits
    if (!this.isFileSizeSupported(fileName, fileSize)) {
      const config = this.getPreviewConfig(fileName);
      const maxSizeMB = config?.maxSize ? Math.round(config.maxSize / (1024 * 1024)) : 0;
      return {
        supported: false,
        reason: `Archivo demasiado grande para vista previa. Tamaño máximo: ${maxSizeMB}MB`,
      };
    }

    return {
      supported: true,
      config: this.getPreviewConfig(fileName)!,
    };
  }
}

/**
 * Convenience function to get preview configuration
 */
export function getPreviewConfig(fileName: string): PreviewConfig | null {
  return FileTypeDetector.getPreviewConfig(fileName);
}

/**
 * Convenience function to check if preview is supported
 */
export function isPreviewSupported(fileName: string, fileSize?: number): boolean {
  if (!FileTypeDetector.isPreviewSupported(fileName)) {
    return false;
  }
  
  if (fileSize !== undefined) {
    return FileTypeDetector.isFileSizeSupported(fileName, fileSize);
  }
  
  return true;
}

/**
 * Get file type display information
 */
export function getFileTypeDisplay(fileName: string): {
  extension: string;
  category: string;
  previewSupported: boolean;
} {
  const extension = FileTypeDetector.getFileExtension(fileName);
  const category = FileTypeDetector.getFileCategory(fileName);
  const previewSupported = FileTypeDetector.isPreviewSupported(fileName);

  return {
    extension: extension.toUpperCase(),
    category,
    previewSupported,
  };
}

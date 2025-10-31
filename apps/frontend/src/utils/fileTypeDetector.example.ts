/**
 * Example usage of FileTypeDetector utility
 * This file demonstrates how to use the file type detection and preview configuration
 */

import { FileTypeDetector, getPreviewConfig, isPreviewSupported, getFileTypeDisplay } from './fileTypeDetector';

// Example: Check if a file supports preview
const fileName = 'medical-report.pdf';
const fileSize = 2 * 1024 * 1024; // 2MB

console.log('File:', fileName);
console.log('Preview supported:', isPreviewSupported(fileName, fileSize));

// Example: Get preview configuration
const config = getPreviewConfig(fileName);
if (config) {
  console.log('Preview config:', {
    component: config.component,
    mediaType: config.mediaType,
    maxSize: config.maxSize
  });
}

// Example: Get display information
const display = getFileTypeDisplay(fileName);
console.log('Display info:', display);

// Example: Validate file for preview
const validation = FileTypeDetector.validateFileForPreview(fileName, fileSize);
console.log('Validation result:', validation);

// Example: Get all supported extensions
console.log('Supported extensions:', FileTypeDetector.getSupportedExtensions());

// Example: Get extensions by category
console.log('Image extensions:', FileTypeDetector.getSupportedExtensionsByCategory('image'));
console.log('Text extensions:', FileTypeDetector.getSupportedExtensionsByCategory('text'));

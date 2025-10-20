#!/usr/bin/env node

/**
 * Generate runtime configuration from CDK outputs
 * This script reads infrastructure/outputs.json and generates a config file
 * that can be bundled with the frontend application
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read the CDK outputs file
const outputsPath = path.join(__dirname, '../../../infrastructure/outputs.json');
const outputsContent = fs.readFileSync(outputsPath, 'utf8');
const outputs = JSON.parse(outputsContent);

// Extract the required values
const apiEndpoint = outputs['AWSomeBuilder2-ApiStack']?.ApiEndpoint;
const rawBucketName = outputs['AWSomeBuilder2-DocumentWorkflowStack']?.RawBucketName;

if (!apiEndpoint || !rawBucketName) {
  console.error('Error: Required outputs not found in infrastructure/outputs.json');
  console.error('Expected: ApiEndpoint and RawBucketName');
  process.exit(1);
}

// Extract region from API endpoint or bucket name
const region = apiEndpoint.match(/\.([a-z0-9-]+)\.amazonaws\.com/)?.[1] || 'us-east-1';

// Generate the config object
const config = {
  apiBaseUrl: apiEndpoint,
  s3BucketName: rawBucketName,
  region: region
};

// Write to public directory so it's available at runtime
const publicDir = path.join(__dirname, '../public');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

const configPath = path.join(publicDir, 'runtime-config.json');
fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

console.log('✅ Generated runtime-config.json:');
console.log(JSON.stringify(config, null, 2));

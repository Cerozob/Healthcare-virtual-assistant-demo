import { defineBackend } from '@aws-amplify/backend';
import { storage } from './storage/resource';
import { data } from './data/resource';

export const backend = defineBackend({
  storage,
  data,
});

// The REST API configuration will be added dynamically
// The CDK stack stores the API endpoint in SSM parameters
// Frontend will read these at runtime

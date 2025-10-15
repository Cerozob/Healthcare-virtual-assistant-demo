import { defineStorage } from '@aws-amplify/backend';

export const storage = defineStorage({
  name: 'healthcareDocuments',
  access: (allow) => ({
    // Public documents - anyone can read, authenticated users can upload
    'public/*': [
      allow.guest.to(['read']),
      allow.authenticated.to(['read', 'write', 'delete'])
    ],
    
    // Patient-specific documents - only authenticated users can access
    'patients/{patient_id}/*': [
      allow.authenticated.to(['read', 'write', 'delete'])
    ],
    
    // Chat session documents - only authenticated users can access
    'chat-sessions/{session_id}/*': [
      allow.authenticated.to(['read', 'write', 'delete'])
    ],
    
    // Processed documents - only authenticated users can read
    'processed/*': [
      allow.authenticated.to(['read'])
    ],
    
    // Temporary uploads - authenticated users can upload, system can process
    'temp-uploads/*': [
      allow.authenticated.to(['read', 'write', 'delete'])
    ]
  })
});

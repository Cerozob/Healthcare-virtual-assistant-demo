import { defineStorage } from '@aws-amplify/backend';

export const storage = defineStorage({
  name: 'healthcareRawData',
  access: (allow) => ({
    'patients/*': [
      // Allow authenticated users to read, write, and delete their own files
      allow.authenticated.to(['read', 'write', 'delete']),
      // Allow guest users to read files (for public access if needed)
      allow.guest.to(['read'])
    ],
    'public/*': [
      // Allow both authenticated and guest users to read public files
      allow.authenticated.to(['read', 'write', 'delete']),
      allow.guest.to(['read'])
    ]
  })
});

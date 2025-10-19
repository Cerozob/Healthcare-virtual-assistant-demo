import { defineAuth } from '@aws-amplify/backend';

/**
 * Define and configure your auth resource
 * @see https://docs.amplify.aws/react/build-a-backend/auth
 */
export const auth = defineAuth({
  loginWith: {
    email: true,
  },
  userAttributes: {
    email: {
      required: true,
      mutable: true,
    },
    fullname: {
      required: true,
      mutable: true,
    },
  },
  // Configure password policy
  accountRecovery: 'EMAIL_ONLY',
  // Configure MFA (disabled for now)
  multifactor: {
    mode: 'OFF',
  },
});

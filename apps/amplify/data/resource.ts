import { defineData, type ClientSchema } from '@aws-amplify/backend';

// Define a minimal schema since we're using external API
const schema = /* GraphQL */ `
  type Todo @model @auth(rules: [{ allow: public }]) {
    id: ID!
    content: String
  }
`;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'apiKey',
    apiKeyAuthorizationMode: {
      expiresInDays: 30,
    },
  },
});

export type Schema = ClientSchema<typeof data>;

/**
 * Type definitions for Amplify outputs and configuration
 */

export interface AmplifyOutputs {
  version: string;
  auth: {
    user_pool_id: string;
    aws_region: string;
    user_pool_client_id: string;
    identity_pool_id: string;
    username_attributes: string[];
    standard_required_attributes: string[];
    user_verification_types: string[];
    password_policy: {
      min_length: number;
      require_numbers: boolean;
      require_lowercase: boolean;
      require_uppercase: boolean;
      require_symbols: boolean;
    };
    unauthenticated_identities_enabled: boolean;
  };
  custom: {
    healthcareSystem: string;
    version: string;
    apiGatewayEndpoint: string | SecretObject;
    s3BucketName: string | SecretObject;
    awsRegion: string | SecretObject;
  };
}

export interface SecretObject {
  secretName: string;
  secretResourceFactory: {
    secretProviderFactory: Record<string, unknown>;
  };
}

export function isSecretObject(value: unknown): value is SecretObject {
  return (
    typeof value === 'object' &&
    value !== null &&
    'secretName' in value &&
    'secretResourceFactory' in value
  );
}

export function resolveSecretValue(value: string | SecretObject): string {
  if (typeof value === 'string') {
    return value;
  }
  if (isSecretObject(value)) {
    // In development, secret objects won't be resolved
    // In production, Amplify replaces these with actual values
    return `[SECRET:${value.secretName}]`;
  }
  return String(value || '');
}

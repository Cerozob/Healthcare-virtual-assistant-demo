import { defineBackend, secret } from '@aws-amplify/backend';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { auth } from './auth/resource';

/**
 * Healthcare System Backend
 * Only defines auth - API Gateway and S3 are managed by CDK
 * External resource values are retrieved from Amplify secrets
 */
const backend = defineBackend({
  auth,
});

// Reference existing CDK resources
const { cfnUserPool } = backend.auth.resources.cfnResources;

// Configure the user pool to use email as username
cfnUserPool.usernameAttributes = ['email'];
cfnUserPool.autoVerifiedAttributes = ['email'];

// Get CDK resource values from Amplify secrets
const apiGatewayEndpoint = secret('CDK_API_GATEWAY_ENDPOINT');
const s3BucketName = secret('CDK_S3_BUCKET_NAME');
const awsRegion = secret('AWS_REGION');
// Add custom outputs for existing CDK resources
backend.addOutput({
  auth: {
    password_policy: {
      min_length:8,
      require_lowercase:false,
      require_uppercase: false,
      require_numbers: false,
      require_symbols: false
    }
  },
  custom: {
    api_endpoint: apiGatewayEndpoint,
    s3_bucket_name: s3BucketName,
    aws_region: awsRegion,
  },
});

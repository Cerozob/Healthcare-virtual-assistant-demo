import { defineBackend, secret } from '@aws-amplify/backend';
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
  custom: {
    apiGatewayEndpoint,
    s3BucketName,
    awsRegion,
  },
});

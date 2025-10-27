import { defineBackend, secret } from '@aws-amplify/backend';
import { Effect, Policy, PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { auth } from './auth/resource';
import { storage } from './storage/resource';

/**
 * Healthcare System Backend
 * Defines auth and storage with additional custom bucket configuration
 */
const backend = defineBackend({
  auth,
  storage,
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

// Create a custom stack for additional S3 bucket configuration
const customBucketStack = backend.createStack('custom-s3-bucket-stack');

// Import your existing CDK bucket
const existingBucket = Bucket.fromBucketName(
  customBucketStack, 
  'ExistingHealthcareBucket', 
  'ab2-cerozob-rawdata-us-east-1'
);

// Define IAM policy for authenticated users to access your existing S3 bucket
const customBucketPolicy = new Policy(customBucketStack, 'CustomHealthcareS3Policy', {
  statements: [
    // Allow file operations on patient files in your existing bucket
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:PutObject', 
        's3:DeleteObject'
      ],
      resources: [
        `${existingBucket.bucketArn}/patients/*`,
        `${existingBucket.bucketArn}/public/*`,
      ],
    }),
    // Allow listing bucket contents with prefix
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: ['s3:ListBucket'],
      resources: [existingBucket.bucketArn],
      conditions: {
        StringLike: {
          's3:prefix': ['patients/*', 'public/*'],
        },
      },
    }),
  ],
});

// Attach the policy to both authenticated and unauthenticated user roles for guest access
backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);
backend.auth.resources.unauthenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);

// Add custom outputs for your existing bucket
backend.addOutput({
  custom: {
    api_endpoint: apiGatewayEndpoint,
    s3_bucket_name: s3BucketName,
    aws_region: awsRegion,
    // Add your existing bucket info
    existing_bucket_name: 'ab2-cerozob-rawdata-us-east-1',
    existing_bucket_region: 'us-east-1',
  },
});

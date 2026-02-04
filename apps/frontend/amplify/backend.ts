import { defineBackend } from '@aws-amplify/backend';
import { Effect, ManagedPolicy, Policy, PolicyStatement } from 'aws-cdk-lib/aws-iam';
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

// Create a custom stack for additional S3 bucket configuration
const customBucketStack = backend.createStack('custom-s3-bucket-stack');

// Import your existing CDK buckets using environment variables
const existingRawBucket = Bucket.fromBucketName(
  customBucketStack,
  'ExistingHealthcareRawBucket',
  process.env.VITE_S3_BUCKET_NAME || 'demo-healthcareva-dfx5-rawdata-us-east-1'
);

const existingProcessedBucket = Bucket.fromBucketName(
  customBucketStack,
  'ExistingHealthcareProcessedBucket',
  process.env.VITE_S3_PROCESSED_BUCKET_NAME || 'demo-healthcareva-dfx5-processeddata-us-east-1'
);


cfnUserPool.policies = {
  passwordPolicy:
  {
    minimumLength: 8,
    requireLowercase: true,
    requireNumbers: true,
    requireSymbols: false,
    requireUppercase: true
  }
}

// Define IAM policy for authenticated users to access your existing S3 buckets
const customBucketPolicy = new Policy(customBucketStack, 'CustomHealthcareS3Policy', {
  statements: [
    // Allow file operations on patient files in your existing raw bucket
    // Updated to support document workflow path structure: {patient_id}/{category}/{timestamp}/{fileId}/{filename}
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:PutObject',
        's3:DeleteObject',
        's3:ListBucket'
      ],
      resources: [
        `${existingRawBucket.bucketArn}/*`, // Allow all paths for authenticated users
        existingRawBucket.bucketArn,
        existingProcessedBucket.bucketArn,
        `${existingProcessedBucket.bucketArn}/*`,
      ],
    }),
  ],
});


// No direct AgentCore permissions needed for frontend users

// Attach the S3 policy to both authenticated and unauthenticated user roles
backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);
backend.auth.resources.unauthenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);
backend.auth.resources.authenticatedUserIamRole.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName("BedrockAgentCoreFullAccess"));

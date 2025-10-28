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

cfnUserPool.policies = {
  passwordPolicy:
  {
    minimumLength:8,
    requireLowercase:true,
    requireNumbers:true,
    requireSymbols:false,
    requireUppercase:true
  }
}

// Define IAM policy for authenticated users to access your existing S3 bucket
const customBucketPolicy = new Policy(customBucketStack, 'CustomHealthcareS3Policy', {
  statements: [
    // Allow file operations on patient files in your existing bucket
    // Updated to support document workflow path structure: {patient_id}/{category}/{timestamp}/{fileId}/{filename}
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        's3:GetObject',
        's3:PutObject', 
        's3:DeleteObject'
      ],
      resources: [
        `${existingBucket.bucketArn}/*`, // Allow all paths for authenticated users
      ],
    }),
    // Allow listing bucket contents
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: ['s3:ListBucket'],
      resources: [existingBucket.bucketArn],
    }),
  ],
});

// Define IAM policy for AgentCore access
// Following AWS best practices for least privilege access
const agentCorePolicy = new Policy(customBucketStack, 'AgentCoreAccessPolicy', {
  statements: [
    // Core AgentCore Runtime permissions for healthcare assistant
    new PolicyStatement({
      effect: Effect.ALLOW,
      actions: [
        'bedrock-agentcore:GetAgentRuntime',
        'bedrock-agentcore:InvokeAgent',
        'bedrock-agentcore:ListAgentRuntimes',
        'bedrock-agentcore:GetAgentRuntimeStatus'
      ],
      resources: [
        // Specific healthcare assistant runtime
        'arn:aws:bedrock-agentcore:us-east-1:711387129682:runtime/healthcare_assistant-*',
        // Allow access to any runtime in this account for flexibility
        'arn:aws:bedrock-agentcore:us-east-1:711387129682:runtime/*'
      ],
    }),
  ],
});

// Attach the policies to authenticated and unauthenticated user roles
backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);
backend.auth.resources.unauthenticatedUserIamRole.attachInlinePolicy(customBucketPolicy);

// Attach AgentCore policy only to authenticated users (for security)
backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(agentCorePolicy);

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

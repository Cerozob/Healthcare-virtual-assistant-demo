# Frontend Environment Variables

The frontend application requires the following environment variables to be set in the Amplify Console:

## Required Environment Variables

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `VITE_API_BASE_URL` | The API Gateway endpoint URL | `https://pg5pv01t3j.execute-api.us-east-1.amazonaws.com/v1` |
| `VITE_S3_BUCKET_NAME` | The S3 bucket name for raw data uploads | `ab2-cerozob-rawdata-us-east-1` |
| `VITE_AWS_REGION` | The AWS region where resources are deployed | `us-east-1` |

## How to Set in Amplify Console

1. Go to your Amplify app in the AWS Console
2. Navigate to "App settings" > "Environment variables"
3. Add each of the variables above with their corresponding values
4. Redeploy your app

## Current Values

Based on your deployed infrastructure:

```
VITE_API_BASE_URL=https://pg5pv01t3j.execute-api.us-east-1.amazonaws.com/v1
VITE_S3_BUCKET_NAME=ab2-cerozob-rawdata-us-east-1
VITE_AWS_REGION=us-east-1
```

## Development

For local development, create a `.env.local` file in the `apps/frontend` directory with these variables.

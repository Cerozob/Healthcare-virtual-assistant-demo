# Runtime Configuration

## Overview

The frontend application now dynamically loads configuration from CDK outputs at build time, eliminating hardcoded values for API endpoints and S3 bucket names.

## How It Works

1. **Build Time Generation**: During the Amplify build process, `scripts/generate-config.js` reads `infrastructure/outputs.json` and generates `public/runtime-config.json`

2. **Runtime Loading**: The app loads this configuration file on startup before rendering (see `src/main.tsx`)

3. **Service Access**: All services access configuration through `configService.getConfig()`

## Configuration Values

The following values are extracted from CDK outputs:

- `apiBaseUrl`: From `AWSomeBuilder2-ApiStack.ApiEndpoint`
- `s3BucketName`: From `AWSomeBuilder2-DocumentWorkflowStack.RawBucketName`
- `region`: Extracted from the API endpoint URL

## Build Process

The Amplify build configuration (`amplify.yml`) includes:

```yaml
preBuild:
  commands:
    - node scripts/generate-config.js
```

This ensures the config is generated before the Vite build runs.

## Local Development

For local development, the config service falls back to development defaults if `runtime-config.json` is not available:

```typescript
{
  apiBaseUrl: 'http://localhost:3000/v1',
  s3BucketName: 'dev-bucket',
  region: 'us-east-1'
}
```

To test with production values locally:

```bash
cd apps/frontend
node scripts/generate-config.js
npm run dev
```

## Files Modified

- `scripts/generate-config.js` - New script to generate config from CDK outputs
- `amplify.yml` - Added config generation to preBuild phase
- `src/services/configService.ts` - Updated to load from runtime-config.json
- `src/main.tsx` - Added config loading before app initialization

## Benefits

- No hardcoded values in source code
- Automatic sync with deployed infrastructure
- Single source of truth (CDK outputs)
- Easy to update when infrastructure changes

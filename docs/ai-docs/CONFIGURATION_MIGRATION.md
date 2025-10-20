# Configuration Migration Summary

## What Changed

Migrated from hardcoded API Gateway URL and S3 bucket name to dynamic configuration loaded from CDK outputs at build time.

## Changes Made

### 1. New Build Script
- **File**: `scripts/generate-config.js`
- **Purpose**: Reads `infrastructure/outputs.json` and generates `public/runtime-config.json`
- **Runs**: During Amplify preBuild phase

### 2. Updated Amplify Build
- **File**: `amplify.yml`
- **Change**: Added `node scripts/generate-config.js` to preBuild commands
- **Effect**: Config is generated before Vite build runs

### 3. Updated Config Service
- **File**: `src/services/configService.ts`
- **Before**: Returned hardcoded values
- **After**: Loads from `/runtime-config.json` at app startup
- **Fallback**: Development defaults if config file not available

### 4. App Initialization
- **File**: `src/main.tsx`
- **Change**: Calls `configService.loadConfig()` before rendering
- **Effect**: Ensures config is loaded before any API calls

### 5. Gitignore Update
- **File**: `.gitignore`
- **Change**: Added `public/runtime-config.json` to ignore list
- **Reason**: File is generated at build time, not committed

## Configuration Values

Extracted from `infrastructure/outputs.json`:

| Config Key | CDK Output Source |
|------------|-------------------|
| `apiBaseUrl` | `AWSomeBuilder2-ApiStack.ApiEndpoint` |
| `s3BucketName` | `AWSomeBuilder2-DocumentWorkflowStack.RawBucketName` |
| `region` | Extracted from API endpoint URL |

## Testing

### Local Test
```bash
cd apps/frontend
node scripts/generate-config.js
npm run dev
```

### Verify Generated Config
```bash
cat apps/frontend/public/runtime-config.json
```

Expected output:
```json
{
  "apiBaseUrl": "https://pg5pv01t3j.execute-api.us-east-1.amazonaws.com/v1",
  "s3BucketName": "ab2-cerozob-rawdata-us-east-1",
  "region": "us-east-1"
}
```

## Benefits

✅ No hardcoded infrastructure values in source code
✅ Automatic sync with deployed infrastructure
✅ Single source of truth (CDK outputs)
✅ Easy to update when infrastructure changes
✅ Works across different environments/deployments

## Next Deployment

On the next Amplify deployment, the build will:
1. Run `node scripts/generate-config.js` in preBuild
2. Generate `public/runtime-config.json` from latest CDK outputs
3. Build the app with Vite (includes the config file)
4. App loads config at startup and uses dynamic values

No manual intervention required!

# Dynamic Bucket Configuration Setup

## ✅ Problem Solved: Dynamic S3 Bucket Configuration

### **Issue**
The error `NoBucket: Missing bucket name while accessing object` occurred because the S3 bucket name was hardcoded instead of being configured dynamically like the API endpoint.

### **Solution Applied**

#### 1. **Removed Hardcoded Storage Configuration**
- Removed the hardcoded `storage` section from `amplify_outputs.json`
- Kept only the dynamic `custom` section with secrets

#### 2. **Enhanced App Configuration (`apps/frontend/src/app.tsx`)**
```typescript
// Get runtime configuration for dynamic bucket name
const runtimeConfig = configService.getConfig();

// Configure Amplify with dynamic storage configuration
Amplify.configure({
  ...outputs,
  Storage: {
    S3: {
      bucket: runtimeConfig.s3BucketName,
      region: runtimeConfig.region,
    }
  }
});
```

#### 3. **Added Configuration Logging**
The app now logs the configuration being used:
```
🔧 Configuring Amplify with dynamic settings:
📍 S3 Bucket: ab2-cerozob-rawdata-us-east-1
🌍 Region: us-east-1
🔗 API Base URL: https://your-api-gateway-url.com/v1
✅ Amplify configured successfully with dynamic storage settings
```

### **Environment Variables Required**

The following environment variables need to be set in your deployment environment:

#### **For Local Development (.env file):**
```bash
VITE_API_BASE_URL=https://your-api-gateway-url.com/v1
VITE_S3_BUCKET_NAME=ab2-cerozob-rawdata-us-east-1
VITE_AWS_REGION=us-east-1
```

#### **For Amplify Hosting (Environment Variables):**
In the Amplify Console → App Settings → Environment Variables:
- `VITE_API_BASE_URL` = `https://your-api-gateway-url.com/v1`
- `VITE_S3_BUCKET_NAME` = `ab2-cerozob-rawdata-us-east-1`
- `VITE_AWS_REGION` = `us-east-1`

#### **For Other Deployment Platforms:**
Set the same environment variables in your deployment platform's configuration.

### **Configuration Flow**

1. **Build Time**: Vite reads `VITE_*` environment variables
2. **Runtime**: `configService.getConfig()` loads the configuration
3. **App Initialization**: Amplify is configured with dynamic storage settings
4. **File Upload**: StorageService uses the configured bucket

### **Fallback Values**
If environment variables are not set, the system falls back to:
- `apiBaseUrl`: `'http://localhost:3000/v1'`
- `s3BucketName`: `'dev-bucket'`
- `region`: `'us-east-1'`

### **Verification**

#### **Check Configuration in Browser Console:**
When the app loads, you should see:
```
🔧 Configuring Amplify with dynamic settings:
📍 S3 Bucket: ab2-cerozob-rawdata-us-east-1
🌍 Region: us-east-1
🔗 API Base URL: https://your-actual-api-url.com/v1
✅ Amplify configured successfully with dynamic storage settings
```

#### **Test File Upload:**
1. Navigate to Configuration → Files tab
2. Upload a file
3. Should see successful upload with proper S3 path
4. No more "NoBucket" errors

### **Benefits of This Approach**

✅ **No Hardcoded Values**: Bucket name is configured dynamically  
✅ **Environment Flexibility**: Different buckets for dev/staging/prod  
✅ **Consistent Pattern**: Same approach as API endpoint configuration  
✅ **Easy Deployment**: Just set environment variables  
✅ **Proper Logging**: Clear visibility into configuration  

### **Next Steps**

1. **Set Environment Variables**: Configure `VITE_S3_BUCKET_NAME` in your deployment environment
2. **Verify Configuration**: Check browser console for configuration logs
3. **Test File Upload**: Ensure file upload works without bucket errors
4. **Deploy**: The configuration will work across all environments

The S3 bucket is now configured dynamically just like the API endpoint! 🎉

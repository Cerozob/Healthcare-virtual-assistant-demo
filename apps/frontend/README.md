# Healthcare System Frontend

React TypeScript web application built with AWS Amplify and Cloudscape Design System.

## Features

- **Patient Management**: View, create, and manage patient records
- **Document Upload**: Upload medical documents with progress tracking
- **Real-time Processing**: Monitor document processing workflows
- **Responsive Design**: Works on desktop and mobile devices
- **AWS Integration**: Seamless integration with backend services

## Technology Stack

- **React 18**: Modern React with hooks and TypeScript
- **Cloudscape Design**: AWS design system components
- **AWS Amplify**: Authentication and hosting
- **Vite**: Fast development and build tool
- **TypeScript**: Type-safe development

## Configuration

### Current Setup (Hardcoded for Demo)

The application is configured with hardcoded values in `src/services/configService.ts`:

```typescript
getConfig(): RuntimeConfig {
  return {
    apiBaseUrl: 'https://pg5pv01t3j.execute-api.us-east-1.amazonaws.com/v1',
    s3BucketName: 'ab2-cerozob-rawdata-us-east-1',
    region: 'us-east-1'
  };
}
```

### Updating Configuration

To update the configuration for your environment:

1. **Deploy your CDK infrastructure** to get new endpoints
2. **Update the values** in `src/services/configService.ts`:
   - `apiBaseUrl`: Your API Gateway endpoint
   - `s3BucketName`: Your S3 bucket name
   - `region`: Your AWS region
3. **Redeploy the application**

### Production Considerations

For production deployments, consider:
- Using environment variables instead of hardcoded values
- Implementing proper secret management
- Using AWS Parameter Store or Systems Manager
- Setting up different configurations for different environments

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run type-check` - Run TypeScript type checking

## Project Structure

```
src/
├── components/          # Reusable UI components
│   └── ApiExample.tsx   # Patient API demo component
├── config/             # Configuration files
│   ├── api.ts          # API configuration
│   └── storage.ts      # S3 storage configuration
├── hooks/              # Custom React hooks
│   ├── useApi.ts       # Generic API hook
│   └── usePatients.ts  # Patient-specific hooks
├── pages/              # Page components
│   ├── HomePage.tsx    # Landing page
│   └── DocumentTestPage.tsx  # Document upload page
├── services/           # Business logic services
│   ├── apiClient.ts    # HTTP client
│   ├── configService.ts # Configuration service
│   ├── patientService.ts # Patient API service
│   └── storageService.ts # S3 storage service
├── types/              # TypeScript type definitions
└── app.tsx            # Main application component
```

## Key Features

### Patient Management
- View patient list with pagination
- Create new patients
- Real-time API integration
- Error handling and loading states

### Document Upload
- Drag-and-drop file upload
- Progress bars for upload tracking
- Support for multiple file formats (PDF, DOC, images)
- Real-time upload status updates

### Authentication
- AWS Amplify authentication
- Secure user sessions
- Protected routes

## API Integration

The frontend integrates with the backend API for:

- **Patient CRUD operations**: `/patients` endpoints
- **Document upload**: `/documents/upload` endpoint
- **File storage**: Direct S3 upload with progress tracking

## Deployment

### Amplify Hosting

The application is deployed using AWS Amplify:

1. **Amplify Console**: Automatic builds from Git
2. **CDN Distribution**: Global content delivery
3. **SSL Certificate**: Automatic HTTPS
4. **Custom Domain**: Optional custom domain setup

### Manual Deployment

```bash
# Build the application
npm run build

# Deploy to Amplify
amplify publish
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check if the API Gateway endpoint is correct
   - Verify CORS configuration on the backend
   - Check network connectivity

2. **Upload Failures**
   - Verify S3 bucket permissions
   - Check file size limits
   - Ensure proper CORS configuration

3. **Authentication Issues**
   - Check Amplify configuration
   - Verify user pool settings
   - Clear browser cache/localStorage

### Development Tips

- Use browser developer tools to debug API calls
- Check the console for error messages
- Use the Network tab to inspect HTTP requests
- Verify configuration values in the console

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Include error handling
4. Test on different screen sizes
5. Update documentation for new features

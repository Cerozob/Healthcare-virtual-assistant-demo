import { defineBackend } from '@aws-amplify/backend';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';

export const createRestApi = (backend: ReturnType<typeof defineBackend>) => {
  const api = new apigateway.RestApi(backend.stack, 'HealthcareAPI', {
    restApiName: 'Healthcare Management API',
    description: 'REST API for healthcare management system',
    defaultCorsPreflightOptions: {
      allowOrigins: apigateway.Cors.ALL_ORIGINS,
      allowMethods: apigateway.Cors.ALL_METHODS,
      allowHeaders: [
        'Content-Type',
        'X-Amz-Date',
        'Authorization',
        'X-Api-Key',
      ],
    },
    deployOptions: {
      stageName: 'v1',
      loggingLevel: apigateway.MethodLoggingLevel.INFO,
      dataTraceEnabled: true,
      metricsEnabled: true,
    },
  });

  // Create CRUD endpoints for each resource
  const createCrudEndpoints = (
    resourceName: string,
    lambdaFunction: any
  ) => {
    const resource = api.root.addResource(resourceName);
    
    // Collection endpoints
    resource.addMethod('GET', new apigateway.LambdaIntegration(lambdaFunction));
    resource.addMethod('POST', new apigateway.LambdaIntegration(lambdaFunction));
    
    // Item endpoints
    const itemResource = resource.addResource('{id}');
    itemResource.addMethod('GET', new apigateway.LambdaIntegration(lambdaFunction));
    itemResource.addMethod('PUT', new apigateway.LambdaIntegration(lambdaFunction));
    itemResource.addMethod('DELETE', new apigateway.LambdaIntegration(lambdaFunction));
  };

  // Create endpoints for each resource
  createCrudEndpoints('patients', backend.patientsFunction.resources.lambda);
  createCrudEndpoints('medics', backend.medicsFunction.resources.lambda);
  createCrudEndpoints('exams', backend.examsFunction.resources.lambda);
  createCrudEndpoints('reservations', backend.reservationsFunction.resources.lambda);

  // ICD-10 endpoint
  const icd10Resource = api.root.addResource('icd10');
  const icd10CodeResource = icd10Resource.addResource('{code}');
  icd10CodeResource.addMethod(
    'GET',
    new apigateway.LambdaIntegration(backend.icd10Function.resources.lambda)
  );

  // Chat endpoints
  const chatResource = api.root.addResource('chat');
  
  // POST /chat/message
  const messageResource = chatResource.addResource('message');
  messageResource.addMethod(
    'POST',
    new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda)
  );
  
  // Chat session endpoints
  const sessionsResource = chatResource.addResource('sessions');
  sessionsResource.addMethod(
    'GET',
    new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda)
  );
  sessionsResource.addMethod(
    'POST',
    new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda)
  );
  
  const sessionIdResource = sessionsResource.addResource('{id}');
  const messagesResource = sessionIdResource.addResource('messages');
  messagesResource.addMethod(
    'GET',
    new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda)
  );

  // Agent integration endpoints
  const agentResource = api.root.addResource('agent');
  agentResource.addMethod(
    'GET',
    new apigateway.LambdaIntegration(backend.agentIntegrationFunction.resources.lambda)
  );
  agentResource.addMethod(
    'POST',
    new apigateway.LambdaIntegration(backend.agentIntegrationFunction.resources.lambda)
  );

  // Document upload endpoints
  const documentsResource = api.root.addResource('documents');
  
  // POST /documents/upload - Document upload metadata
  const uploadResource = documentsResource.addResource('upload');
  uploadResource.addMethod(
    'POST',
    new apigateway.LambdaIntegration(backend.documentUploadFunction.resources.lambda)
  );
  
  // GET /documents/status/{id} - Get document processing status
  const statusResource = documentsResource.addResource('status');
  const statusIdResource = statusResource.addResource('{id}');
  statusIdResource.addMethod(
    'GET',
    new apigateway.LambdaIntegration(backend.documentUploadFunction.resources.lambda)
  );

  return api;
};

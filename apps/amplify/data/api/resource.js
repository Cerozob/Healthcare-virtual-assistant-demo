"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.createRestApi = void 0;
const apigateway = __importStar(require("aws-cdk-lib/aws-apigateway"));
const createRestApi = (backend) => {
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
    const createCrudEndpoints = (resourceName, lambdaFunction) => {
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
    icd10CodeResource.addMethod('GET', new apigateway.LambdaIntegration(backend.icd10Function.resources.lambda));
    // Chat endpoints
    const chatResource = api.root.addResource('chat');
    // POST /chat/message
    const messageResource = chatResource.addResource('message');
    messageResource.addMethod('POST', new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda));
    // Chat session endpoints
    const sessionsResource = chatResource.addResource('sessions');
    sessionsResource.addMethod('GET', new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda));
    sessionsResource.addMethod('POST', new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda));
    const sessionIdResource = sessionsResource.addResource('{id}');
    const messagesResource = sessionIdResource.addResource('messages');
    messagesResource.addMethod('GET', new apigateway.LambdaIntegration(backend.chatFunction.resources.lambda));
    // Agent integration endpoints
    const agentResource = api.root.addResource('agent');
    agentResource.addMethod('GET', new apigateway.LambdaIntegration(backend.agentIntegrationFunction.resources.lambda));
    agentResource.addMethod('POST', new apigateway.LambdaIntegration(backend.agentIntegrationFunction.resources.lambda));
    // Document upload endpoints
    const documentsResource = api.root.addResource('documents');
    // POST /documents/upload - Document upload metadata
    const uploadResource = documentsResource.addResource('upload');
    uploadResource.addMethod('POST', new apigateway.LambdaIntegration(backend.documentUploadFunction.resources.lambda));
    // GET /documents/status/{id} - Get document processing status
    const statusResource = documentsResource.addResource('status');
    const statusIdResource = statusResource.addResource('{id}');
    statusIdResource.addMethod('GET', new apigateway.LambdaIntegration(backend.documentUploadFunction.resources.lambda));
    return api;
};
exports.createRestApi = createRestApi;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicmVzb3VyY2UuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJyZXNvdXJjZS50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUFDQSx1RUFBeUQ7QUFFbEQsTUFBTSxhQUFhLEdBQUcsQ0FBQyxPQUF5QyxFQUFFLEVBQUU7SUFDekUsTUFBTSxHQUFHLEdBQUcsSUFBSSxVQUFVLENBQUMsT0FBTyxDQUFDLE9BQU8sQ0FBQyxLQUFLLEVBQUUsZUFBZSxFQUFFO1FBQ2pFLFdBQVcsRUFBRSwyQkFBMkI7UUFDeEMsV0FBVyxFQUFFLDJDQUEyQztRQUN4RCwyQkFBMkIsRUFBRTtZQUMzQixZQUFZLEVBQUUsVUFBVSxDQUFDLElBQUksQ0FBQyxXQUFXO1lBQ3pDLFlBQVksRUFBRSxVQUFVLENBQUMsSUFBSSxDQUFDLFdBQVc7WUFDekMsWUFBWSxFQUFFO2dCQUNaLGNBQWM7Z0JBQ2QsWUFBWTtnQkFDWixlQUFlO2dCQUNmLFdBQVc7YUFDWjtTQUNGO1FBQ0QsYUFBYSxFQUFFO1lBQ2IsU0FBUyxFQUFFLElBQUk7WUFDZixZQUFZLEVBQUUsVUFBVSxDQUFDLGtCQUFrQixDQUFDLElBQUk7WUFDaEQsZ0JBQWdCLEVBQUUsSUFBSTtZQUN0QixjQUFjLEVBQUUsSUFBSTtTQUNyQjtLQUNGLENBQUMsQ0FBQztJQUVILDBDQUEwQztJQUMxQyxNQUFNLG1CQUFtQixHQUFHLENBQzFCLFlBQW9CLEVBQ3BCLGNBQW1CLEVBQ25CLEVBQUU7UUFDRixNQUFNLFFBQVEsR0FBRyxHQUFHLENBQUMsSUFBSSxDQUFDLFdBQVcsQ0FBQyxZQUFZLENBQUMsQ0FBQztRQUVwRCx1QkFBdUI7UUFDdkIsUUFBUSxDQUFDLFNBQVMsQ0FBQyxLQUFLLEVBQUUsSUFBSSxVQUFVLENBQUMsaUJBQWlCLENBQUMsY0FBYyxDQUFDLENBQUMsQ0FBQztRQUM1RSxRQUFRLENBQUMsU0FBUyxDQUFDLE1BQU0sRUFBRSxJQUFJLFVBQVUsQ0FBQyxpQkFBaUIsQ0FBQyxjQUFjLENBQUMsQ0FBQyxDQUFDO1FBRTdFLGlCQUFpQjtRQUNqQixNQUFNLFlBQVksR0FBRyxRQUFRLENBQUMsV0FBVyxDQUFDLE1BQU0sQ0FBQyxDQUFDO1FBQ2xELFlBQVksQ0FBQyxTQUFTLENBQUMsS0FBSyxFQUFFLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLGNBQWMsQ0FBQyxDQUFDLENBQUM7UUFDaEYsWUFBWSxDQUFDLFNBQVMsQ0FBQyxLQUFLLEVBQUUsSUFBSSxVQUFVLENBQUMsaUJBQWlCLENBQUMsY0FBYyxDQUFDLENBQUMsQ0FBQztRQUNoRixZQUFZLENBQUMsU0FBUyxDQUFDLFFBQVEsRUFBRSxJQUFJLFVBQVUsQ0FBQyxpQkFBaUIsQ0FBQyxjQUFjLENBQUMsQ0FBQyxDQUFDO0lBQ3JGLENBQUMsQ0FBQztJQUVGLHFDQUFxQztJQUNyQyxtQkFBbUIsQ0FBQyxVQUFVLEVBQUUsT0FBTyxDQUFDLGdCQUFnQixDQUFDLFNBQVMsQ0FBQyxNQUFNLENBQUMsQ0FBQztJQUMzRSxtQkFBbUIsQ0FBQyxRQUFRLEVBQUUsT0FBTyxDQUFDLGNBQWMsQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLENBQUM7SUFDdkUsbUJBQW1CLENBQUMsT0FBTyxFQUFFLE9BQU8sQ0FBQyxhQUFhLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxDQUFDO0lBQ3JFLG1CQUFtQixDQUFDLGNBQWMsRUFBRSxPQUFPLENBQUMsb0JBQW9CLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxDQUFDO0lBRW5GLGtCQUFrQjtJQUNsQixNQUFNLGFBQWEsR0FBRyxHQUFHLENBQUMsSUFBSSxDQUFDLFdBQVcsQ0FBQyxPQUFPLENBQUMsQ0FBQztJQUNwRCxNQUFNLGlCQUFpQixHQUFHLGFBQWEsQ0FBQyxXQUFXLENBQUMsUUFBUSxDQUFDLENBQUM7SUFDOUQsaUJBQWlCLENBQUMsU0FBUyxDQUN6QixLQUFLLEVBQ0wsSUFBSSxVQUFVLENBQUMsaUJBQWlCLENBQUMsT0FBTyxDQUFDLGFBQWEsQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLENBQ3pFLENBQUM7SUFFRixpQkFBaUI7SUFDakIsTUFBTSxZQUFZLEdBQUcsR0FBRyxDQUFDLElBQUksQ0FBQyxXQUFXLENBQUMsTUFBTSxDQUFDLENBQUM7SUFFbEQscUJBQXFCO0lBQ3JCLE1BQU0sZUFBZSxHQUFHLFlBQVksQ0FBQyxXQUFXLENBQUMsU0FBUyxDQUFDLENBQUM7SUFDNUQsZUFBZSxDQUFDLFNBQVMsQ0FDdkIsTUFBTSxFQUNOLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLE9BQU8sQ0FBQyxZQUFZLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxDQUN4RSxDQUFDO0lBRUYseUJBQXlCO0lBQ3pCLE1BQU0sZ0JBQWdCLEdBQUcsWUFBWSxDQUFDLFdBQVcsQ0FBQyxVQUFVLENBQUMsQ0FBQztJQUM5RCxnQkFBZ0IsQ0FBQyxTQUFTLENBQ3hCLEtBQUssRUFDTCxJQUFJLFVBQVUsQ0FBQyxpQkFBaUIsQ0FBQyxPQUFPLENBQUMsWUFBWSxDQUFDLFNBQVMsQ0FBQyxNQUFNLENBQUMsQ0FDeEUsQ0FBQztJQUNGLGdCQUFnQixDQUFDLFNBQVMsQ0FDeEIsTUFBTSxFQUNOLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLE9BQU8sQ0FBQyxZQUFZLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxDQUN4RSxDQUFDO0lBRUYsTUFBTSxpQkFBaUIsR0FBRyxnQkFBZ0IsQ0FBQyxXQUFXLENBQUMsTUFBTSxDQUFDLENBQUM7SUFDL0QsTUFBTSxnQkFBZ0IsR0FBRyxpQkFBaUIsQ0FBQyxXQUFXLENBQUMsVUFBVSxDQUFDLENBQUM7SUFDbkUsZ0JBQWdCLENBQUMsU0FBUyxDQUN4QixLQUFLLEVBQ0wsSUFBSSxVQUFVLENBQUMsaUJBQWlCLENBQUMsT0FBTyxDQUFDLFlBQVksQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLENBQ3hFLENBQUM7SUFFRiw4QkFBOEI7SUFDOUIsTUFBTSxhQUFhLEdBQUcsR0FBRyxDQUFDLElBQUksQ0FBQyxXQUFXLENBQUMsT0FBTyxDQUFDLENBQUM7SUFDcEQsYUFBYSxDQUFDLFNBQVMsQ0FDckIsS0FBSyxFQUNMLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLE9BQU8sQ0FBQyx3QkFBd0IsQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLENBQ3BGLENBQUM7SUFDRixhQUFhLENBQUMsU0FBUyxDQUNyQixNQUFNLEVBQ04sSUFBSSxVQUFVLENBQUMsaUJBQWlCLENBQUMsT0FBTyxDQUFDLHdCQUF3QixDQUFDLFNBQVMsQ0FBQyxNQUFNLENBQUMsQ0FDcEYsQ0FBQztJQUVGLDRCQUE0QjtJQUM1QixNQUFNLGlCQUFpQixHQUFHLEdBQUcsQ0FBQyxJQUFJLENBQUMsV0FBVyxDQUFDLFdBQVcsQ0FBQyxDQUFDO0lBRTVELG9EQUFvRDtJQUNwRCxNQUFNLGNBQWMsR0FBRyxpQkFBaUIsQ0FBQyxXQUFXLENBQUMsUUFBUSxDQUFDLENBQUM7SUFDL0QsY0FBYyxDQUFDLFNBQVMsQ0FDdEIsTUFBTSxFQUNOLElBQUksVUFBVSxDQUFDLGlCQUFpQixDQUFDLE9BQU8sQ0FBQyxzQkFBc0IsQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLENBQ2xGLENBQUM7SUFFRiw4REFBOEQ7SUFDOUQsTUFBTSxjQUFjLEdBQUcsaUJBQWlCLENBQUMsV0FBVyxDQUFDLFFBQVEsQ0FBQyxDQUFDO0lBQy9ELE1BQU0sZ0JBQWdCLEdBQUcsY0FBYyxDQUFDLFdBQVcsQ0FBQyxNQUFNLENBQUMsQ0FBQztJQUM1RCxnQkFBZ0IsQ0FBQyxTQUFTLENBQ3hCLEtBQUssRUFDTCxJQUFJLFVBQVUsQ0FBQyxpQkFBaUIsQ0FBQyxPQUFPLENBQUMsc0JBQXNCLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxDQUNsRixDQUFDO0lBRUYsT0FBTyxHQUFHLENBQUM7QUFDYixDQUFDLENBQUM7QUFoSFcsUUFBQSxhQUFhLGlCQWdIeEIiLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBkZWZpbmVCYWNrZW5kIH0gZnJvbSAnQGF3cy1hbXBsaWZ5L2JhY2tlbmQnO1xuaW1wb3J0ICogYXMgYXBpZ2F0ZXdheSBmcm9tICdhd3MtY2RrLWxpYi9hd3MtYXBpZ2F0ZXdheSc7XG5cbmV4cG9ydCBjb25zdCBjcmVhdGVSZXN0QXBpID0gKGJhY2tlbmQ6IFJldHVyblR5cGU8dHlwZW9mIGRlZmluZUJhY2tlbmQ+KSA9PiB7XG4gIGNvbnN0IGFwaSA9IG5ldyBhcGlnYXRld2F5LlJlc3RBcGkoYmFja2VuZC5zdGFjaywgJ0hlYWx0aGNhcmVBUEknLCB7XG4gICAgcmVzdEFwaU5hbWU6ICdIZWFsdGhjYXJlIE1hbmFnZW1lbnQgQVBJJyxcbiAgICBkZXNjcmlwdGlvbjogJ1JFU1QgQVBJIGZvciBoZWFsdGhjYXJlIG1hbmFnZW1lbnQgc3lzdGVtJyxcbiAgICBkZWZhdWx0Q29yc1ByZWZsaWdodE9wdGlvbnM6IHtcbiAgICAgIGFsbG93T3JpZ2luczogYXBpZ2F0ZXdheS5Db3JzLkFMTF9PUklHSU5TLFxuICAgICAgYWxsb3dNZXRob2RzOiBhcGlnYXRld2F5LkNvcnMuQUxMX01FVEhPRFMsXG4gICAgICBhbGxvd0hlYWRlcnM6IFtcbiAgICAgICAgJ0NvbnRlbnQtVHlwZScsXG4gICAgICAgICdYLUFtei1EYXRlJyxcbiAgICAgICAgJ0F1dGhvcml6YXRpb24nLFxuICAgICAgICAnWC1BcGktS2V5JyxcbiAgICAgIF0sXG4gICAgfSxcbiAgICBkZXBsb3lPcHRpb25zOiB7XG4gICAgICBzdGFnZU5hbWU6ICd2MScsXG4gICAgICBsb2dnaW5nTGV2ZWw6IGFwaWdhdGV3YXkuTWV0aG9kTG9nZ2luZ0xldmVsLklORk8sXG4gICAgICBkYXRhVHJhY2VFbmFibGVkOiB0cnVlLFxuICAgICAgbWV0cmljc0VuYWJsZWQ6IHRydWUsXG4gICAgfSxcbiAgfSk7XG5cbiAgLy8gQ3JlYXRlIENSVUQgZW5kcG9pbnRzIGZvciBlYWNoIHJlc291cmNlXG4gIGNvbnN0IGNyZWF0ZUNydWRFbmRwb2ludHMgPSAoXG4gICAgcmVzb3VyY2VOYW1lOiBzdHJpbmcsXG4gICAgbGFtYmRhRnVuY3Rpb246IGFueVxuICApID0+IHtcbiAgICBjb25zdCByZXNvdXJjZSA9IGFwaS5yb290LmFkZFJlc291cmNlKHJlc291cmNlTmFtZSk7XG4gICAgXG4gICAgLy8gQ29sbGVjdGlvbiBlbmRwb2ludHNcbiAgICByZXNvdXJjZS5hZGRNZXRob2QoJ0dFVCcsIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGxhbWJkYUZ1bmN0aW9uKSk7XG4gICAgcmVzb3VyY2UuYWRkTWV0aG9kKCdQT1NUJywgbmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24obGFtYmRhRnVuY3Rpb24pKTtcbiAgICBcbiAgICAvLyBJdGVtIGVuZHBvaW50c1xuICAgIGNvbnN0IGl0ZW1SZXNvdXJjZSA9IHJlc291cmNlLmFkZFJlc291cmNlKCd7aWR9Jyk7XG4gICAgaXRlbVJlc291cmNlLmFkZE1ldGhvZCgnR0VUJywgbmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24obGFtYmRhRnVuY3Rpb24pKTtcbiAgICBpdGVtUmVzb3VyY2UuYWRkTWV0aG9kKCdQVVQnLCBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbihsYW1iZGFGdW5jdGlvbikpO1xuICAgIGl0ZW1SZXNvdXJjZS5hZGRNZXRob2QoJ0RFTEVURScsIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGxhbWJkYUZ1bmN0aW9uKSk7XG4gIH07XG5cbiAgLy8gQ3JlYXRlIGVuZHBvaW50cyBmb3IgZWFjaCByZXNvdXJjZVxuICBjcmVhdGVDcnVkRW5kcG9pbnRzKCdwYXRpZW50cycsIGJhY2tlbmQucGF0aWVudHNGdW5jdGlvbi5yZXNvdXJjZXMubGFtYmRhKTtcbiAgY3JlYXRlQ3J1ZEVuZHBvaW50cygnbWVkaWNzJywgYmFja2VuZC5tZWRpY3NGdW5jdGlvbi5yZXNvdXJjZXMubGFtYmRhKTtcbiAgY3JlYXRlQ3J1ZEVuZHBvaW50cygnZXhhbXMnLCBiYWNrZW5kLmV4YW1zRnVuY3Rpb24ucmVzb3VyY2VzLmxhbWJkYSk7XG4gIGNyZWF0ZUNydWRFbmRwb2ludHMoJ3Jlc2VydmF0aW9ucycsIGJhY2tlbmQucmVzZXJ2YXRpb25zRnVuY3Rpb24ucmVzb3VyY2VzLmxhbWJkYSk7XG5cbiAgLy8gSUNELTEwIGVuZHBvaW50XG4gIGNvbnN0IGljZDEwUmVzb3VyY2UgPSBhcGkucm9vdC5hZGRSZXNvdXJjZSgnaWNkMTAnKTtcbiAgY29uc3QgaWNkMTBDb2RlUmVzb3VyY2UgPSBpY2QxMFJlc291cmNlLmFkZFJlc291cmNlKCd7Y29kZX0nKTtcbiAgaWNkMTBDb2RlUmVzb3VyY2UuYWRkTWV0aG9kKFxuICAgICdHRVQnLFxuICAgIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGJhY2tlbmQuaWNkMTBGdW5jdGlvbi5yZXNvdXJjZXMubGFtYmRhKVxuICApO1xuXG4gIC8vIENoYXQgZW5kcG9pbnRzXG4gIGNvbnN0IGNoYXRSZXNvdXJjZSA9IGFwaS5yb290LmFkZFJlc291cmNlKCdjaGF0Jyk7XG4gIFxuICAvLyBQT1NUIC9jaGF0L21lc3NhZ2VcbiAgY29uc3QgbWVzc2FnZVJlc291cmNlID0gY2hhdFJlc291cmNlLmFkZFJlc291cmNlKCdtZXNzYWdlJyk7XG4gIG1lc3NhZ2VSZXNvdXJjZS5hZGRNZXRob2QoXG4gICAgJ1BPU1QnLFxuICAgIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGJhY2tlbmQuY2hhdEZ1bmN0aW9uLnJlc291cmNlcy5sYW1iZGEpXG4gICk7XG4gIFxuICAvLyBDaGF0IHNlc3Npb24gZW5kcG9pbnRzXG4gIGNvbnN0IHNlc3Npb25zUmVzb3VyY2UgPSBjaGF0UmVzb3VyY2UuYWRkUmVzb3VyY2UoJ3Nlc3Npb25zJyk7XG4gIHNlc3Npb25zUmVzb3VyY2UuYWRkTWV0aG9kKFxuICAgICdHRVQnLFxuICAgIG5ldyBhcGlnYXRld2F5LkxhbWJkYUludGVncmF0aW9uKGJhY2tlbmQuY2hhdEZ1bmN0aW9uLnJlc291cmNlcy5sYW1iZGEpXG4gICk7XG4gIHNlc3Npb25zUmVzb3VyY2UuYWRkTWV0aG9kKFxuICAgICdQT1NUJyxcbiAgICBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbihiYWNrZW5kLmNoYXRGdW5jdGlvbi5yZXNvdXJjZXMubGFtYmRhKVxuICApO1xuICBcbiAgY29uc3Qgc2Vzc2lvbklkUmVzb3VyY2UgPSBzZXNzaW9uc1Jlc291cmNlLmFkZFJlc291cmNlKCd7aWR9Jyk7XG4gIGNvbnN0IG1lc3NhZ2VzUmVzb3VyY2UgPSBzZXNzaW9uSWRSZXNvdXJjZS5hZGRSZXNvdXJjZSgnbWVzc2FnZXMnKTtcbiAgbWVzc2FnZXNSZXNvdXJjZS5hZGRNZXRob2QoXG4gICAgJ0dFVCcsXG4gICAgbmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24oYmFja2VuZC5jaGF0RnVuY3Rpb24ucmVzb3VyY2VzLmxhbWJkYSlcbiAgKTtcblxuICAvLyBBZ2VudCBpbnRlZ3JhdGlvbiBlbmRwb2ludHNcbiAgY29uc3QgYWdlbnRSZXNvdXJjZSA9IGFwaS5yb290LmFkZFJlc291cmNlKCdhZ2VudCcpO1xuICBhZ2VudFJlc291cmNlLmFkZE1ldGhvZChcbiAgICAnR0VUJyxcbiAgICBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbihiYWNrZW5kLmFnZW50SW50ZWdyYXRpb25GdW5jdGlvbi5yZXNvdXJjZXMubGFtYmRhKVxuICApO1xuICBhZ2VudFJlc291cmNlLmFkZE1ldGhvZChcbiAgICAnUE9TVCcsXG4gICAgbmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24oYmFja2VuZC5hZ2VudEludGVncmF0aW9uRnVuY3Rpb24ucmVzb3VyY2VzLmxhbWJkYSlcbiAgKTtcblxuICAvLyBEb2N1bWVudCB1cGxvYWQgZW5kcG9pbnRzXG4gIGNvbnN0IGRvY3VtZW50c1Jlc291cmNlID0gYXBpLnJvb3QuYWRkUmVzb3VyY2UoJ2RvY3VtZW50cycpO1xuICBcbiAgLy8gUE9TVCAvZG9jdW1lbnRzL3VwbG9hZCAtIERvY3VtZW50IHVwbG9hZCBtZXRhZGF0YVxuICBjb25zdCB1cGxvYWRSZXNvdXJjZSA9IGRvY3VtZW50c1Jlc291cmNlLmFkZFJlc291cmNlKCd1cGxvYWQnKTtcbiAgdXBsb2FkUmVzb3VyY2UuYWRkTWV0aG9kKFxuICAgICdQT1NUJyxcbiAgICBuZXcgYXBpZ2F0ZXdheS5MYW1iZGFJbnRlZ3JhdGlvbihiYWNrZW5kLmRvY3VtZW50VXBsb2FkRnVuY3Rpb24ucmVzb3VyY2VzLmxhbWJkYSlcbiAgKTtcbiAgXG4gIC8vIEdFVCAvZG9jdW1lbnRzL3N0YXR1cy97aWR9IC0gR2V0IGRvY3VtZW50IHByb2Nlc3Npbmcgc3RhdHVzXG4gIGNvbnN0IHN0YXR1c1Jlc291cmNlID0gZG9jdW1lbnRzUmVzb3VyY2UuYWRkUmVzb3VyY2UoJ3N0YXR1cycpO1xuICBjb25zdCBzdGF0dXNJZFJlc291cmNlID0gc3RhdHVzUmVzb3VyY2UuYWRkUmVzb3VyY2UoJ3tpZH0nKTtcbiAgc3RhdHVzSWRSZXNvdXJjZS5hZGRNZXRob2QoXG4gICAgJ0dFVCcsXG4gICAgbmV3IGFwaWdhdGV3YXkuTGFtYmRhSW50ZWdyYXRpb24oYmFja2VuZC5kb2N1bWVudFVwbG9hZEZ1bmN0aW9uLnJlc291cmNlcy5sYW1iZGEpXG4gICk7XG5cbiAgcmV0dXJuIGFwaTtcbn07XG4iXX0=
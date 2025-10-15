import { defineBackend } from '@aws-amplify/backend';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
export declare const createRestApi: (backend: ReturnType<typeof defineBackend>) => apigateway.RestApi;

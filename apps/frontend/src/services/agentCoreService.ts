/**
 * AgentCore Service
 * Direct integration with AWS Bedrock AgentCore for JSON request/response
 * Uses IAM-based authentication through Amplify Auth credentials
 */

import {
  BedrockAgentCoreClient,
  InvokeAgentRuntimeCommand,
  type InvokeAgentRuntimeCommandInput,
  type InvokeAgentRuntimeCommandOutput
} from '@aws-sdk/client-bedrock-agentcore';
import {
  BedrockAgentCoreControlClient,
  GetAgentRuntimeCommand,
  type GetAgentRuntimeCommandInput,
  type GetAgentRuntimeCommandOutput
} from '@aws-sdk/client-bedrock-agentcore-control';
import { fetchAuthSession } from 'aws-amplify/auth';
import { v4 as uuidv4 } from 'uuid';

// Environment variables
const AGENTCORE_RUNTIME_ID = import.meta.env.VITE_AGENTCORE_RUNTIME_ID;
const AWS_REGION = import.meta.env.VITE_AWS_REGION || 'us-east-1';

export interface AgentCoreResponse {
  sessionId: string;
  messageId: string;
  content: string;
  metadata?: Record<string, unknown>;
  patientContext?: {
    patientId?: string;
    patientName?: string;
    contextChanged?: boolean;
    identificationSource?: string;
  };
  fileProcessingResults?: Array<{
    fileId: string;
    fileName: string;
    status: 'processed' | 'failed' | 'skipped';
    classification?: string;
    analysisResults?: any;
    s3Location?: string;
    errorMessage?: string;
  }>;
}



export class AgentCoreService {
  private agentCoreClient: BedrockAgentCoreClient | null = null;
  private controlClient: BedrockAgentCoreControlClient | null = null;
  private agentRuntimeId: string;
  private agentRuntimeArn: string | null = null;

  constructor() {
    this.agentRuntimeId = AGENTCORE_RUNTIME_ID || '';
  }

  /**
   * Get or create the AgentCore client with Amplify Auth credentials
   */
  private async getAgentCoreClient(): Promise<BedrockAgentCoreClient> {
    if (!this.agentCoreClient) {
      const credentials = await this.getCredentials();

      this.agentCoreClient = new BedrockAgentCoreClient({
        region: AWS_REGION,
        credentials
      });

      console.log('🔑 AgentCore client initialized with Amplify Auth credentials');
    }

    return this.agentCoreClient;
  }

  /**
   * Get or create the AgentCore control client
   */
  private async getControlClient(): Promise<BedrockAgentCoreControlClient> {
    if (!this.controlClient) {
      const credentials = await this.getCredentials();

      this.controlClient = new BedrockAgentCoreControlClient({
        region: AWS_REGION,
        credentials
      });

      console.log('🔑 AgentCore control client initialized');
    }

    return this.controlClient;
  }

  /**
   * Get AWS credentials from Amplify Auth
   */
  private async getCredentials() {
    try {
      const session = await fetchAuthSession();
      const credentials = session.credentials;

      if (!credentials) {
        throw new Error('No AWS credentials available from Amplify Auth');
      }

      return {
        accessKeyId: credentials.accessKeyId,
        secretAccessKey: credentials.secretAccessKey,
        sessionToken: credentials.sessionToken,
      };
    } catch (error) {
      console.error('❌ Failed to get credentials:', error);
      throw new Error(`Failed to get AWS credentials: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get the AgentCore runtime ARN from the runtime ID
   */
  private async getAgentRuntimeArn(): Promise<string> {
    if (this.agentRuntimeArn) {
      return this.agentRuntimeArn;
    }

    try {
      const controlClient = await this.getControlClient();

      const input: GetAgentRuntimeCommandInput = {
        agentRuntimeId: this.agentRuntimeId
      };

      const command = new GetAgentRuntimeCommand(input);
      const response: GetAgentRuntimeCommandOutput = await controlClient.send(command);

      if (!response.agentRuntimeArn) {
        throw new Error('Agent runtime ARN not found in response');
      }

      this.agentRuntimeArn = response.agentRuntimeArn;
      console.log('🎯 AgentCore Runtime ARN:', this.agentRuntimeArn);

      return this.agentRuntimeArn;
    } catch (error) {
      console.error('❌ Error getting AgentCore runtime ARN:', error);
      throw new Error(`Failed to get AgentCore runtime ARN: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Check if AgentCore is configured
   */
  private isConfigured(): boolean {
    return !!this.agentRuntimeId;
  }

  /**
   * Generate a valid AgentCore session ID (minimum 33 characters)
   */
  private generateSessionId(): string {
    // Use UUID v4 for session ID - this ensures uniqueness and meets length requirement
    const sessionId = `agentcore_session_${uuidv4()}`;

    console.log(`Generated session ID: ${sessionId} (length: ${sessionId.length})`);
    return sessionId;
  }



  /**
   * Send HTTP request to AgentCore using Strands format
   */
  async sendMessage(
    strandsRequest: import('../types/api').SendMessageRequest,
    signal?: AbortSignal
  ): Promise<AgentCoreResponse> {
    try {
      console.group('📤 AGENTCORE HTTP REQUEST (STRANDS FORMAT)');
      console.log('🎯 Runtime ID:', this.agentRuntimeId);
      console.log('📦 Content blocks:', strandsRequest.content.length);
      console.log('🔑 Session ID:', strandsRequest.sessionId);

      if (!this.isConfigured()) {
        throw new Error('AgentCore runtime ID not configured. Please set VITE_AGENTCORE_RUNTIME_ID environment variable.');
      }

      // Get the AgentCore client
      const client = await this.getAgentCoreClient();

      // Generate valid session ID if not provided
      const validSessionId = strandsRequest.sessionId || this.generateSessionId();

      console.log('🔑 Session ID Analysis:');
      console.log(`   • Input sessionId: ${strandsRequest.sessionId || 'NOT PROVIDED'}`);
      console.log(`   • Generated/Used: ${validSessionId}`);
      console.log(`   • Length: ${validSessionId.length} chars`);

      // Get the AgentCore runtime ARN
      const runtimeArn = await this.getAgentRuntimeArn();

      // Build the payload in Strands format
      const agentCorePayload = {
        content: strandsRequest.content,
        sessionId: validSessionId
      };

      console.log('🔍 HTTP Request Payload (Strands):');
      console.log('📦 Payload Size:', JSON.stringify(agentCorePayload).length, 'characters');
      console.log('📋 Content blocks:', strandsRequest.content.map(block => Object.keys(block)[0]));

      // Prepare the request for HTTP (non-streaming)
      const input: InvokeAgentRuntimeCommandInput = {
        agentRuntimeArn: runtimeArn,
        runtimeSessionId: validSessionId,
        payload: new TextEncoder().encode(JSON.stringify(agentCorePayload))
      };

      console.log('🚀 Sending HTTP request to AgentCore...');
      console.groupEnd();

      const command = new InvokeAgentRuntimeCommand(input);

      // Add abort signal support
      if (signal) {
        command.middlewareStack.add(
          (next) => (args) => {
            if (signal.aborted) {
              throw new Error('Request was aborted');
            }
            return next(args);
          },
          { step: 'initialize' }
        );
      }

      const response: InvokeAgentRuntimeCommandOutput = await client.send(command);

      console.group('📥 AGENTCORE HTTP RESPONSE');
      console.log('✅ Response received:', response);

      // Handle the response (should be complete, not streaming)
      let fullContent = '';
      const messageId = `agent_${Date.now()}`;
      // Use the original session ID from the request to maintain consistency
      const responseSessionId = validSessionId;

      console.log('📥 Processing AgentCore HTTP response...');
      console.log('Response keys:', Object.keys(response));

      // Process the response payload
      if (response.response) {
        const responseText = await response.response.transformToString();

        try {
          const parsedResponse = JSON.parse(responseText);
          console.log('🔍 Parsed response structure:', Object.keys(parsedResponse));
          console.log('🔍 Full parsed response:', JSON.stringify(parsedResponse, null, 2));
          
          if (parsedResponse.message) {
            console.log('🔍 Message structure:', Object.keys(parsedResponse.message));
            if (parsedResponse.message.content) {
              console.log('🔍 Content array length:', parsedResponse.message.content.length);
              console.log('🔍 Content items:', parsedResponse.message.content);
            }
          }

          // Extract content from AgentCore response structure
          if (parsedResponse.response && typeof parsedResponse.response === 'string') {
            // Direct response field (most common for AgentCore)
            fullContent = parsedResponse.response;
          } else if (parsedResponse.message?.content && Array.isArray(parsedResponse.message.content)) {
            // Strands format: message.content[0].text
            const textContent = parsedResponse.message.content
              .filter((item: any) => item.text)
              .map((item: any) => item.text)
              .join('\n');
            fullContent = textContent;
          } else if (parsedResponse.content) {
            // Fallback: direct content field
            fullContent = String(parsedResponse.content);
          } else {
            // Final fallback: raw response text
            fullContent = responseText;
          }

          console.log('🔍 Final content type:', typeof fullContent);
          console.log('🔍 Final content length:', fullContent.length);

          // Return structured response with proper field extraction
          const result: AgentCoreResponse = {
            sessionId: validSessionId, // Always use the frontend session ID, not the agent response
            messageId: messageId,
            content: String(fullContent),
            metadata: {
              timestamp: new Date().toISOString(),
              agentUsed: 'healthcare_agent',
              requestId: messageId,
              // Include specific fields from response, not the entire object
              status: parsedResponse.status,
              memoryEnabled: parsedResponse.memoryEnabled,
              memoryId: parsedResponse.memoryId,
              metrics: parsedResponse.metrics,
              uploadResults: parsedResponse.uploadResults,
              // Store the original agent session ID for debugging
              agentSessionId: parsedResponse.sessionId
            },
            patientContext: parsedResponse.patientContext,
            fileProcessingResults: parsedResponse.uploadResults // Map uploadResults to fileProcessingResults for frontend compatibility
          };

          console.log('✅ Structured response created:', result);
          console.groupEnd();
          return result;

        } catch (parseError) {
          console.warn('⚠️ Failed to parse response as JSON, using raw text');
          fullContent = responseText;
        }
      }

      // Fallback response
      const result: AgentCoreResponse = {
        sessionId: validSessionId, // Always use the frontend session ID
        messageId: messageId,
        content: String(fullContent || 'No response content received'),
        metadata: {
          timestamp: new Date().toISOString(),
          agentUsed: 'healthcare_agent',
          requestId: messageId
        }
      };

      console.log('✅ Fallback response created:', result);
      console.groupEnd();
      return result;

    } catch (error) {
      console.error('❌ AgentCore HTTP request failed:', error);
      console.groupEnd();
      throw error;
    }
  }

  /**
   * Validate AgentCore configuration
   */
  async validateConfiguration(): Promise<{ valid: boolean; error?: string }> {
    try {
      if (!this.agentRuntimeId) {
        return { valid: false, error: 'VITE_AGENTCORE_RUNTIME_ID not configured' };
      }

      // Test client initialization
      try {
        await this.getAgentCoreClient();
        console.log('✅ AgentCore client validation successful');
      } catch (clientError) {
        return {
          valid: false,
          error: `AgentCore client initialization failed: ${clientError instanceof Error ? clientError.message : 'Unknown error'}`
        };
      }

      return { valid: true };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Unknown validation error'
      };
    }
  }
}

// Export singleton instance
export const agentCoreService = new AgentCoreService();

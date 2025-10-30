/**
 * AgentCore Streaming Service
 * Direct integration with AWS Bedrock AgentCore for streaming responses
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

export interface StreamingChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string;
  metadata?: Record<string, unknown>;
}

// Interface for AgentCore response with streaming properties
interface AgentCoreStreamingResponse {
  response?: {
    transformToString(): Promise<string>;
    transformToByteArray(): Promise<Uint8Array>;
  };
  statusCode?: number;
  runtimeSessionId?: string;
  contentType?: string;
}

export class AgentCoreStreamingService {
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
   * Send a streaming message to AgentCore
   */
  async sendStreamingMessage(
    message: string,
    sessionId?: string,
    onChunk?: (chunk: StreamingChatResponse) => void,
    onComplete?: (finalResponse: StreamingChatResponse) => void,
    onError?: (error: Error) => void
  ): Promise<StreamingChatResponse> {
    try {
      console.group('📤 AGENTCORE STREAMING REQUEST');
      console.log('🎯 Runtime ID:', this.agentRuntimeId);
      console.log('📝 Message:', message);
      console.log('🔑 Session ID:', sessionId);

      if (!this.isConfigured()) {
        throw new Error('AgentCore runtime ID not configured. Please set VITE_AGENTCORE_RUNTIME_ID environment variable.');
      }

      // Get the AgentCore client
      const client = await this.getAgentCoreClient();

      // Generate valid session ID if not provided
      const validSessionId = sessionId || this.generateSessionId();
      console.log('🔑 Using session ID:', validSessionId, `(length: ${validSessionId.length})`);

      // Get the AgentCore runtime ARN
      const runtimeArn = await this.getAgentRuntimeArn();

      // Prepare the request based on AgentCore SDK documentation
      const input: InvokeAgentRuntimeCommandInput = {
        agentRuntimeArn: runtimeArn,                    // Required: ARN not ID
        runtimeSessionId: validSessionId,               // Required: runtimeSessionId not sessionId
        payload: new TextEncoder().encode(JSON.stringify({
          prompt: message,
          timestamp: new Date().toISOString()
        }))                                             // Required: payload not inputText
      };

      console.log('📦 AgentCore request:', input);
      console.groupEnd();

      const command = new InvokeAgentRuntimeCommand(input);

      let response: InvokeAgentRuntimeCommandOutput;
      try {
        response = await client.send(command);
        console.log('✅ Command sent successfully');
      } catch (error: any) {
        // Enhanced error logging for debugging
        console.error('❌ AgentCore command failed:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error code:', error.$metadata?.httpStatusCode);

        // Check for common parameter issues
        if (error.message?.includes('ValidationException') || error.message?.includes('InvalidParameter')) {
          console.error('🔍 Possible parameter issue. Input was:', input);
          throw new Error(`AgentCore parameter validation failed: ${error.message}`);
        }

        throw error;
      }

      console.group('📥 AGENTCORE STREAMING RESPONSE');
      console.log('✅ Response received:', response);

      // Handle response
      let fullContent = '';
      const messageId = `agent_${Date.now()}`;
      const responseSessionId = response.runtimeSessionId || input.runtimeSessionId || this.generateSessionId();

      // Type the response properly
      const streamingResponse = response as AgentCoreStreamingResponse;

      // Handle streaming response based on SDK documentation
      if (streamingResponse.response) {
        try {
          // The response is a stream - convert to string
          const responseText = await streamingResponse.response.transformToString();
          fullContent = responseText;

          // Call chunk callback for streaming simulation
          if (onChunk) {
            const chunkResponse: StreamingChatResponse = {
              sessionId: responseSessionId,
              messageId,
              isComplete: false,
              content: fullContent,
              metadata: {
                agentCoreSDK: true,
                statusCode: streamingResponse.statusCode
              }
            };
            onChunk(chunkResponse);
          }
        } catch (streamError) {
          console.error('Stream processing failed:', streamError);
          throw streamError;
        }
      } else {
        // Fallback: log response structure for debugging
        console.log('Response structure for debugging:', Object.keys(response));
        console.log('Full response:', response);

        // Try to extract any text content from the response
        const responseStr = JSON.stringify(response);
        if (responseStr.length > 50) {
          fullContent = `Response received but format unclear. Keys: ${Object.keys(response).join(', ')}`;
        } else {
          throw new Error('No content received from AgentCore');
        }
      }

      // Call chunk callback for immediate response
      if (onChunk) {
        const chunkResponse: StreamingChatResponse = {
          sessionId: responseSessionId,
          messageId,
          isComplete: false,
          content: fullContent,
          metadata: {
            agentCoreSDK: true
          }
        };
        onChunk(chunkResponse);
      }

      // Final response
      const finalResponse: StreamingChatResponse = {
        sessionId: responseSessionId,
        messageId,
        isComplete: true,
        content: fullContent,
        metadata: {
          sessionId: responseSessionId,
          agentCoreResponse: response,
          agentCoreSDK: true
        }
      };

      console.log('✅ Final response:', finalResponse);
      console.groupEnd();

      if (onComplete) {
        onComplete(finalResponse);
      }

      return finalResponse;

    } catch (error) {
      console.error('❌ AgentCore streaming error:', error);
      console.groupEnd();

      const errorMessage = error instanceof Error ? error.message : 'Unknown AgentCore error';

      if (onError) {
        onError(new Error(errorMessage));
      }

      // Return error response with valid session ID
      return {
        sessionId: sessionId || this.generateSessionId(),
        messageId: `error_${Date.now()}`,
        isComplete: true,
        content: `Error: ${errorMessage}`,
        metadata: { error: true }
      };
    }
  }

  /**
   * Send a non-streaming message (fallback)
   */
  async sendMessage(message: string, sessionId?: string): Promise<StreamingChatResponse> {
    return new Promise((resolve, reject) => {
      this.sendStreamingMessage(
        message,
        sessionId,
        undefined, // No chunk callback
        (finalResponse) => resolve(finalResponse),
        (error) => reject(error)
      );
    });
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
export const agentCoreService = new AgentCoreStreamingService();

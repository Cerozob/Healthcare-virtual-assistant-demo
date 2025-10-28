/**
 * AgentCore Streaming Service
 * Direct integration with AWS Bedrock AgentCore for streaming responses
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

// Environment variables
const AGENTCORE_RUNTIME_ID = import.meta.env.VITE_AGENTCORE_RUNTIME_ID;
const AWS_REGION = import.meta.env.VITE_AWS_REGION || 'us-east-1';

export interface StreamingChatMessage {
  id: string;
  content: string;
  type: 'user' | 'agent' | 'system';
  timestamp: string;
  isStreaming?: boolean;
  metadata?: Record<string, unknown>;
}

export interface StreamingChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string;
  metadata?: Record<string, unknown>;
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

      // Get the AgentCore client and runtime ARN
      const client = await this.getAgentCoreClient();
      const runtimeArn = await this.getAgentRuntimeArn();

      // Prepare the request based on SDK documentation
      const input: InvokeAgentRuntimeCommandInput = {
        agentRuntimeArn: runtimeArn,
        mcpSessionId: sessionId || `session_${Date.now()}`,
        payload: new TextEncoder().encode(JSON.stringify({
          inputText: message,
          timestamp: new Date().toISOString()
        }))
      };

      console.log('📦 AgentCore request:', input);
      console.groupEnd();

      const command = new InvokeAgentRuntimeCommand(input);
      const response: InvokeAgentRuntimeCommandOutput = await client.send(command);

      console.group('📥 AGENTCORE STREAMING RESPONSE');
      console.log('✅ Response received:', response);

      // Handle response
      let fullContent = '';
      const messageId = `agent_${Date.now()}`;
      const responseSessionId = response.mcpSessionId || input.mcpSessionId || `session_${Date.now()}`;

      // Handle response - use type assertion for SDK properties that may not be fully typed
      const responseAny = response as any;
      
      // Check for streaming response
      if (responseAny.completion) {
        // Handle streaming completion
        try {
          for await (const chunk of responseAny.completion) {
            if (chunk.chunk?.bytes) {
              const chunkText = new TextDecoder().decode(chunk.chunk.bytes);
              fullContent += chunkText;

              // Call chunk callback
              if (onChunk) {
                const chunkResponse: StreamingChatResponse = {
                  sessionId: responseSessionId,
                  messageId,
                  isComplete: false,
                  content: fullContent,
                  metadata: {
                    chunk: chunkText,
                    agentCoreSDK: true
                  }
                };
                onChunk(chunkResponse);
              }
            }
          }
        } catch (streamError) {
          console.warn('Streaming failed, using fallback:', streamError);
          fullContent = responseAny.outputText || 
                       responseAny.response || 
                       `AgentCore processed: "${message}"`;
        }
      } else {
        // Handle non-streaming response
        fullContent = responseAny.outputText || 
                     responseAny.response || 
                     responseAny.message ||
                     `AgentCore processed: "${message}"`;

        // Simulate chunk callback for immediate response
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
      }

      // Final response
      const finalResponse: StreamingChatResponse = {
        sessionId: responseSessionId,
        messageId,
        isComplete: true,
        content: fullContent || 'No response received',
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

      // Return error response
      return {
        sessionId: sessionId || `error_session_${Date.now()}`,
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

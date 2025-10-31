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
    attachments?: Array<{
      fileName: string;
      fileSize: number;
      fileType: string;
      category: string;
      s3Key: string;
      content?: string;
      mimeType?: string;
    }>,
    onChunk?: (chunk: StreamingChatResponse) => void,
    onComplete?: (finalResponse: StreamingChatResponse) => void,
    onError?: (error: Error) => void
  ): Promise<StreamingChatResponse> {
    try {
      console.group('📤 AGENTCORE STREAMING REQUEST');
      console.log('🎯 Runtime ID:', this.agentRuntimeId);
      console.log('📝 Message:', message);
      console.log('🔑 Session ID:', sessionId);
      console.log('📎 Attachments:', attachments?.length || 0);

      // Log multimodal processing details
      if (attachments && attachments.length > 0) {
        console.log('🖼️ Multimodal processing enabled');
        attachments.forEach((att, idx) => {
          console.log(`   ${idx + 1}. ${att.fileName} (${att.mimeType}) - ${att.content ? 'Has base64 content' : 'No content'}`);
          if (att.content) {
            console.log(`      Content length: ${att.content.length} chars`);
            console.log(`      Content preview: ${att.content.substring(0, 50)}...`);
          }
        });
      }

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

      // Build and log the complete payload
      const agentCorePayload = this.buildAgentCorePayload(message, attachments);
      
      console.log('🔍 === DETAILED PAYLOAD ANALYSIS ===');
      console.log('📦 AgentCore Payload Object:', agentCorePayload);
      console.log('📦 Payload JSON String:', JSON.stringify(agentCorePayload, null, 2));
      console.log('📦 Payload Size:', JSON.stringify(agentCorePayload).length, 'characters');
      
      // Log payload structure
      console.log('📋 Payload Structure:');
      console.log('   - prompt:', typeof agentCorePayload.prompt, `(${agentCorePayload.prompt?.length || 0} chars)`);
      console.log('   - timestamp:', typeof agentCorePayload.timestamp);
      console.log('   - media:', agentCorePayload.media ? 'present' : 'absent');
      console.log('   - mediaMetadata:', agentCorePayload.mediaMetadata ? 'present' : 'absent');
      console.log('   - attachmentContext:', agentCorePayload.attachmentContext ? `${agentCorePayload.attachmentContext.length} items` : 'absent');
      
      if (agentCorePayload.media) {
        console.log('🖼️ Media Details:');
        console.log('   - type:', agentCorePayload.media.type);
        console.log('   - format:', agentCorePayload.media.format);
        console.log('   - data length:', agentCorePayload.media.data?.length || 0, 'chars');
      }
      
      if (agentCorePayload.mediaMetadata) {
        console.log('📄 Media Metadata:');
        console.log('   - fileName:', agentCorePayload.mediaMetadata.fileName);
        console.log('   - fileSize:', agentCorePayload.mediaMetadata.fileSize);
        console.log('   - category:', agentCorePayload.mediaMetadata.category);
        console.log('   - s3Key:', agentCorePayload.mediaMetadata.s3Key);
      }
      
      // Prepare the request based on AgentCore SDK documentation
      const input: InvokeAgentRuntimeCommandInput = {
        agentRuntimeArn: runtimeArn,                    // Required: ARN not ID
        runtimeSessionId: validSessionId,               // Required: runtimeSessionId not sessionId
        payload: new TextEncoder().encode(JSON.stringify(agentCorePayload))  // Required: payload not inputText
      };
      
      console.log('🚀 Final AgentCore Request Input:');
      console.log('   - agentRuntimeArn:', runtimeArn);
      console.log('   - runtimeSessionId:', validSessionId);
      console.log('   - payload size (bytes):', input.payload);
      console.log('🔍 === END PAYLOAD ANALYSIS ===');

      // Validate payload before sending
      console.log('✅ === PAYLOAD VALIDATION ===');
      try {
        const payloadString = JSON.stringify(agentCorePayload);
        const parsedBack = JSON.parse(payloadString);
        console.log('✅ Payload is valid JSON');
        console.log('✅ Payload can be serialized and deserialized');
        
        // Check required fields
        if (!parsedBack.prompt) {
          console.error('❌ Missing required field: prompt');
        } else {
          console.log('✅ Required field present: prompt');
        }
        
        // Check multimodal fields consistency
        if (parsedBack.media && !parsedBack.mediaMetadata) {
          console.warn('⚠️ Media present but mediaMetadata missing');
        } else if (!parsedBack.media && parsedBack.mediaMetadata) {
          console.warn('⚠️ MediaMetadata present but media missing');
        } else if (parsedBack.media && parsedBack.mediaMetadata) {
          console.log('✅ Multimodal fields are consistent');
        }
        
      } catch (validationError) {
        console.error('❌ Payload validation failed:', validationError);
      }
      console.log('✅ === END VALIDATION ===');
      
      console.log('📦 Final AgentCore SDK Input:', input);
      console.groupEnd();

      const command = new InvokeAgentRuntimeCommand(input);

      let response: InvokeAgentRuntimeCommandOutput;
      try {
        response = await client.send(command);
        console.log('✅ Command sent successfully');
      } catch (error: any) {
        // Enhanced error logging for debugging
        console.error('❌ === AGENTCORE COMMAND FAILED ===');
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error code:', error.$metadata?.httpStatusCode);
        console.error('Full error object:', error);
        
        // Log the payload that caused the error
        console.error('💥 Payload that caused error:');
        console.error('   - Payload size:', input.payload, 'bytes');
        console.error('   - Runtime ARN:', input.agentRuntimeArn);
        console.error('   - Session ID:', input.runtimeSessionId);
        console.error('   - Payload content:', input.payload.toString());
        console.error('❌ === END ERROR ANALYSIS ===');

        // Check for common parameter issues
        if (error.message?.includes('ValidationException') || error.message?.includes('InvalidParameter')) {
          console.error('🔍 Possible parameter issue. Input was:', input);
          throw new Error(`AgentCore parameter validation failed: ${error.message}`);
        }

        throw error;
      }

      console.group('📥 AGENTCORE STREAMING RESPONSE');
      console.log('✅ Response received:', response);

      // Handle streaming response according to AgentCore docs
      let fullContent = '';
      const messageId = `agent_${Date.now()}`;
      const responseSessionId = response.runtimeSessionId || input.runtimeSessionId || this.generateSessionId();

      console.log('📥 Processing AgentCore streaming response...');
      console.log('Response keys:', Object.keys(response));
      console.log('Content type:', response.contentType);

      // AgentCore always returns streaming responses for our runtime
      console.log('🌊 Processing AgentCore streaming response (streaming-only mode)');

      try {
        // Handle streaming response according to AgentCore docs
        const streamingResponse = response as AgentCoreStreamingResponse;

        if (streamingResponse.response && typeof streamingResponse.response.transformToByteArray === 'function') {
          const responseBytes = await streamingResponse.response.transformToByteArray();
          const responseText = new TextDecoder().decode(responseBytes);

          console.log('📄 Raw streaming response length:', responseText.length);

          // Process Server-Sent Events format
          const lines = responseText.split('\n');
          let chunkCount = 0;
          let patientContext: any = null;

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              chunkCount++;
              const dataStr = line.substring(6); // Remove 'data: ' prefix

              if (dataStr.trim()) {
                try {
                  const chunkData = JSON.parse(dataStr);
                  console.log(`📦 Chunk ${chunkCount} (${chunkData.type}):`, chunkData);

                  // Handle different chunk types from our streaming runtime
                  if (chunkData.type === 'content_chunk' || chunkData.type === 'multimodal_chunk' || chunkData.type === 'legacy_multimodal_chunk') {
                    fullContent = chunkData.accumulated_content || fullContent + (chunkData.content || '');

                    if (onChunk) {
                      const chunkResponse: StreamingChatResponse = {
                        sessionId: responseSessionId,
                        messageId,
                        isComplete: false,
                        content: fullContent,
                        metadata: {
                          agentCoreStreaming: true,
                          chunkType: chunkData.type,
                          chunkNumber: chunkData.chunk_number,
                          mediaType: chunkData.media_type,
                          mediaFormat: chunkData.media_format,
                          primaryFile: chunkData.primary_file,
                          attachmentsCount: chunkData.attachments_count
                        }
                      };
                      onChunk(chunkResponse);
                    }
                  } else if (chunkData.type === 'patient_context' || chunkData.type === 'multimodal_context' || chunkData.type === 'legacy_multimodal_context') {
                    // Store patient context for final response
                    console.log('👤 Patient context received:', chunkData);
                    patientContext = chunkData;
                  } else if (chunkData.type === 'status') {
                    // Status updates
                    console.log(`📊 Status: ${chunkData.status} - ${chunkData.message || ''}`);
                  } else if (chunkData.type === 'completion') {
                    // Completion event
                    console.log(`✅ Completion: ${chunkData.status} (${chunkData.total_time_ms}ms)`);
                  } else if (chunkData.type === 'error') {
                    console.error('❌ Streaming error:', chunkData.error);
                    throw new Error(chunkData.error);
                  }
                } catch (parseError) {
                  console.warn('⚠️ Failed to parse chunk data:', dataStr, parseError);
                }
              }
            }
          }

          console.log(`✅ Processed ${chunkCount} streaming chunks`);

          // Include patient context in final response metadata
          if (patientContext) {
            console.log('👤 Including patient context in final response');
          }

        } else if (streamingResponse.response && typeof streamingResponse.response.transformToString === 'function') {
          console.warn('⚠️ No transformToByteArray method available, trying transformToString');
          const responseText = await streamingResponse.response.transformToString();
          fullContent = responseText;
        } else {
          console.error('❌ No response transformation methods available');
          throw new Error('Unable to process AgentCore response');
        }

      } catch (streamError) {
        console.error('❌ Stream processing failed:', streamError);
        throw streamError;
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
          agentCoreStreaming: true,
          contentType: response.contentType
        }
      };

      console.log('✅ Final streaming response:', finalResponse);
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
  async sendMessage(message: string, sessionId?: string, attachments?: Array<{
    fileName: string;
    fileSize: number;
    fileType: string;
    category: string;
    s3Key: string;
    content?: string;
    mimeType?: string;
  }>): Promise<StreamingChatResponse> {
    return new Promise((resolve, reject) => {
      this.sendStreamingMessage(
        message,
        sessionId,
        attachments,
        undefined, // No chunk callback
        (finalResponse) => resolve(finalResponse),
        (error) => reject(error)
      );
    });
  }

  /**
   * Build AgentCore payload according to official multimodal format
   */
  private buildAgentCorePayload(
    message: string,
    attachments?: Array<{
      fileName: string;
      fileSize: number;
      fileType: string;
      category: string;
      s3Key: string;
      content?: string;
      mimeType?: string;
    }>
  ): any {
    console.log('🏗️ === BUILDING AGENTCORE PAYLOAD ===');
    console.log('Input message length:', message?.length || 0);
    console.log('Input attachments count:', attachments?.length || 0);
    
    // Base payload structure
    const payload: any = {
      prompt: message,
      timestamp: new Date().toISOString()
    };
    
    console.log('📦 Base payload created:', payload);

    // Add multimodal support according to AgentCore docs
    if (attachments && attachments.length > 0) {
      // Find the first attachment with base64 content for primary media
      const primaryAttachment = attachments.find(att => att.content && att.mimeType);

      if (primaryAttachment) {
        // Extract format from MIME type
        const format = this.extractFormatFromMimeType(primaryAttachment.mimeType!);
        const mediaType = this.getMediaTypeFromMimeType(primaryAttachment.mimeType!);

        console.log(`🖼️ Primary media: ${primaryAttachment.fileName} (${mediaType}/${format})`);

        // Add media according to AgentCore format
        payload.media = {
          type: mediaType,           // "image", "document", etc.
          format: format,            // "jpeg", "png", "pdf", etc.
          data: primaryAttachment.content
        };

        // Add metadata about the file
        payload.mediaMetadata = {
          fileName: primaryAttachment.fileName,
          fileSize: primaryAttachment.fileSize,
          category: primaryAttachment.category,
          s3Key: primaryAttachment.s3Key
        };
      }

      // Add information about all attachments for context
      payload.attachmentContext = attachments.map(att => ({
        fileName: att.fileName,
        fileType: att.fileType,
        category: att.category,
        s3Key: att.s3Key,
        hasContent: !!att.content,
        mimeType: att.mimeType
      }));

      // Enhance prompt with attachment context
      if (attachments.length > 1) {
        payload.prompt += `\n\n[CONTEXT: Processing ${attachments.length} attachments: ${attachments.map(a => a.fileName).join(', ')}]`;
      } else if (primaryAttachment) {
        payload.prompt += `\n\n[CONTEXT: Analyzing attached ${primaryAttachment.category}: ${primaryAttachment.fileName}]`;
      }
    }

    console.log('✅ Final payload built:', payload);
    console.log('📊 Payload statistics:');
    console.log('   - Total size:', JSON.stringify(payload).length, 'characters');
    console.log('   - Has media:', !!payload.media);
    console.log('   - Has mediaMetadata:', !!payload.mediaMetadata);
    console.log('   - Has attachmentContext:', !!payload.attachmentContext);
    console.log('🏗️ === END PAYLOAD BUILD ===');
    
    return payload;
  }

  /**
   * Extract format from MIME type for AgentCore
   */
  private extractFormatFromMimeType(mimeType: string): string {
    const formatMap: Record<string, string> = {
      'image/jpeg': 'jpeg',
      'image/jpg': 'jpeg',
      'image/png': 'png',
      'image/gif': 'gif',
      'image/webp': 'webp',
      'image/tiff': 'tiff',
      'image/tif': 'tiff',
      'application/pdf': 'pdf',
      'text/plain': 'txt',
      'text/markdown': 'md',
      'text/html': 'html',
      'text/csv': 'csv',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
      'application/msword': 'doc',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
      'application/vnd.ms-excel': 'xls'
    };

    return formatMap[mimeType] || mimeType.split('/')[1] || 'unknown';
  }

  /**
   * Get media type from MIME type for AgentCore
   */
  private getMediaTypeFromMimeType(mimeType: string): string {
    if (mimeType.startsWith('image/')) {
      return 'image';
    } else if (mimeType.startsWith('video/')) {
      return 'video';
    } else if (mimeType.startsWith('audio/')) {
      return 'audio';
    } else if (mimeType.includes('pdf') || mimeType.includes('document') || mimeType.includes('text')) {
      return 'document';
    } else {
      return 'document'; // Default to document for unknown types
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
export const agentCoreService = new AgentCoreStreamingService();

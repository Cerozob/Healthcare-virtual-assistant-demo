/**
 * Chat Service
 * Direct AgentCore integration for healthcare chat functionality
 */

import type { SendMessageRequest } from '../types/api';

// Define StreamingChatResponse type for AgentCore integration
export interface StreamingChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string;
  metadata?: {
    agentCore?: boolean;
    responseTimeMs?: number;
    totalProcessingTimeMs?: number;
    patientContext?: unknown;
    originalResponse?: unknown;
    [key: string]: unknown;
  };
}

export class ChatService {

  /**
   * Send streaming message directly to AgentCore
   */
  async sendStreamingMessage(
    data: SendMessageRequest,
    onChunk?: (chunk: StreamingChatResponse) => void,
    onComplete?: (finalResponse: StreamingChatResponse) => void,
    onError?: (error: Error) => void
  ): Promise<StreamingChatResponse> {
    console.group('📤 CHAT SERVICE STREAMING REQUEST');
    console.log('📝 Request data:', data);
    console.log('   • message length:', data.message?.length || 0);
    console.log('   • sessionId:', data.sessionId);
    console.log('   • attachments:', data.attachments?.length || 0);
    console.groupEnd();

    // Use AgentCore directly
    const { agentCoreService } = await import('./agentCoreService');

    console.log('🎯 Connecting to AgentCore...');

    const agentCoreResponse = await agentCoreService.sendStreamingMessage(
      data.message,
      data.sessionId,
      onChunk,
      onComplete,
      onError
    );

    // Convert AgentCore response to our format
    const streamingResponse: StreamingChatResponse = {
      sessionId: agentCoreResponse.sessionId,
      messageId: agentCoreResponse.messageId,
      isComplete: agentCoreResponse.isComplete,
      content: agentCoreResponse.content,
      metadata: {
        agentCore: true,
        ...agentCoreResponse.metadata
      }
    };

    console.log('✅ AgentCore response received');
    return streamingResponse;
  }


}

// Export singleton instance
export const chatService = new ChatService();

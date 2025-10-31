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
    console.log('📝 Complete Request Data:', data);
    console.log('📋 Request Analysis:');
    console.log('   • message length:', data.message?.length || 0);
    console.log('   • sessionId:', data.sessionId);
    console.log('   • attachments count:', data.attachments?.length || 0);
    
    // Log detailed attachment information
    if (data.attachments && data.attachments.length > 0) {
      console.log('📎 Detailed Attachments:');
      data.attachments.forEach((att, idx) => {
        console.log(`   ${idx + 1}. ${att.fileName}:`);
        console.log(`      - fileSize: ${att.fileSize} bytes`);
        console.log(`      - fileType: ${att.fileType}`);
        console.log(`      - category: ${att.category}`);
        console.log(`      - s3Key: ${att.s3Key}`);
        console.log(`      - mimeType: ${att.mimeType}`);
        console.log(`      - has content: ${!!att.content}`);
        if (att.content) {
          console.log(`      - content length: ${att.content.length} chars`);
          console.log(`      - content preview: ${att.content.substring(0, 30)}...`);
        }
      });
    }
    
    console.log('🎯 About to call AgentCore service...');
    console.groupEnd();

    // Use AgentCore directly
    const { agentCoreService } = await import('./agentCoreService');

    console.log('🎯 Connecting to AgentCore...');

    console.log('🔄 Calling AgentCore with parameters:');
    console.log('   - message:', data.message?.substring(0, 100) + '...');
    console.log('   - sessionId:', data.sessionId);
    console.log('   - attachments:', data.attachments);
    console.log('   - callbacks:', { 
      hasOnChunk: !!onChunk, 
      hasOnComplete: !!onComplete, 
      hasOnError: !!onError 
    });

    const agentCoreResponse = await agentCoreService.sendStreamingMessage(
      data.message,
      data.sessionId,
      data.attachments, // Pass attachments to AgentCore
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

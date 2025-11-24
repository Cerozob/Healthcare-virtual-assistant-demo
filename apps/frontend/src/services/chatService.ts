/**
 * Chat Service
 * HTTP request-based implementation for healthcare chat functionality
 * JSON request/response implementation for healthcare chat functionality
 */

import type { SendMessageRequest } from '../types/api';
import { debugLog } from '../utils/debugUtils';

// Define structured response interfaces for normal messaging
export interface ChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string; // Fixed: should be string, not object
  metadata?: {
    processingTimeMs?: number;
    agentUsed?: string;
    toolsExecuted?: string[];
    requestId?: string;
    timestamp?: string;
    patientContext?: unknown;
    // Additional fields from agent response
    status?: string;
    memoryEnabled?: boolean;
    memoryId?: string;
    metrics?: Record<string, unknown>;
    uploadResults?: unknown[];
    agentSessionId?: string;
    [key: string]: unknown;
  };
  patientContext?: {
    patientId?: string;
    patientName?: string;
    contextChanged?: boolean;
    identificationSource?: 'tool_extraction' | 'agent_extraction' | 'content_extraction' | 'image_analysis' | 'document_analysis' | 'multimodal_analysis' | 'default';
    fileOrganizationId?: string;
    confidenceLevel?: string;
    additionalIdentifiers?: Record<string, unknown>;
  };
  guardrailInterventions?: Array<{
    source: 'INPUT' | 'OUTPUT';
    action: 'GUARDRAIL_INTERVENED' | 'NONE';
    content_preview?: string;
    timestamp?: string;
    violations: Array<{
      type: 'topic_policy' | 'content_policy' | 'pii_entity' | 'pii_regex' | 'grounding_policy';
      topic?: string;
      content_type?: string;
      pii_type?: string;
      pattern?: string;
      grounding_type?: string;
      confidence?: string;
      score?: number;
      threshold?: number;
      action?: string;
      policy_type?: string;
    }>;
  }>;
  fileProcessingResults?: Array<{
    fileId: string;
    fileName: string;
    status: 'processed' | 'failed' | 'skipped';
    classification?: string;
    analysisResults?: Record<string, unknown>;
    s3Location?: string;
    errorMessage?: string;
  }>;
  errors?: Array<{
    code: string;
    message: string;
    details?: Record<string, unknown>;
  }>;
  success: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  stage: 'uploading' | 'processing' | 'analyzing' | 'completing';
  progress?: number;
}

export class ChatService {
  private abortController: AbortController | null = null;

  /**
   * Send message using HTTP request-response pattern
   */
  async sendMessage(
    message: string,
    sessionId: string,
    attachments?: Array<{
      fileName: string;
      fileType: string;
      mimeType: string;
      content?: string;
      s3Key?: string;
      fileSize: number;
    }>,
    onLoadingStateChange?: (state: LoadingState) => void
  ): Promise<ChatResponse> {
    console.group('📤 CHAT SERVICE HTTP REQUEST');
    console.log('📝 Request Data:');
    console.log('   • message length:', message?.length || 0);
    console.log('   • sessionId:', sessionId);
    console.log('   • attachments count:', attachments?.length || 0);
    
    // Log detailed attachment information
    if (attachments && attachments.length > 0) {
      console.log('📎 Detailed Attachments:');
      attachments.forEach((att, idx) => {
        console.log(`   ${idx + 1}. ${att.fileName}:`);
        console.log(`      - fileSize: ${att.fileSize} bytes`);
        console.log(`      - fileType: ${att.fileType}`);
        console.log(`      - s3Key: ${att.s3Key}`);
        console.log(`      - mimeType: ${att.mimeType}`);
        console.log(`      - has content: ${!!att.content}`);
        if (att.content) {
          console.log(`      - content length: ${att.content.length} chars`);
          console.log(`      - content preview: ${att.content.substring(0, 30)}...`);
        }
      });
    }
    
    console.groupEnd();

    // Convert to Strands format
    const strandsRequest = this.convertToStrandsFormat(message, attachments);
    console.log('🔄 Converted to Strands format:', strandsRequest);

    // Create new AbortController for this request
    this.abortController = new AbortController();

    try {
      // Update loading state - processing stage
      if (onLoadingStateChange) {
        onLoadingStateChange({
          isLoading: true,
          stage: 'processing',
        });
      }

      // Use AgentCore Service for HTTP request
      const { agentCoreService } = await import('./agentCoreService');

      console.log('🎯 Sending HTTP request to AgentCore...');
      console.log('🔄 Request parameters:');
      console.log('   - content blocks:', strandsRequest.content.length);
      console.log('   - sessionId:', sessionId);

      const startTime = Date.now();

      // Send HTTP request with Strands format
      const agentCoreResponse = await agentCoreService.sendMessage(
        strandsRequest,
        this.abortController.signal
      );

      const processingTime = Date.now() - startTime;

      // Update loading state - completing
      if (onLoadingStateChange) {
        onLoadingStateChange({
          isLoading: true,
          stage: 'completing',
          progress: 90
        });
      }

      // Convert AgentCore response to our structured format
      const chatResponse: ChatResponse = {
        sessionId: agentCoreResponse.sessionId || sessionId,
        messageId: agentCoreResponse.messageId || `msg_${Date.now()}`,
        isComplete: true,
        content: agentCoreResponse.content || '', // Now correctly typed as string
        metadata: {
          processingTimeMs: processingTime,
          agentUsed: 'healthcare_agent',
          requestId: `req_${Date.now()}`,
          timestamp: new Date().toISOString(),
          // Safely spread metadata, avoiding circular references
          ...(agentCoreResponse.metadata && typeof agentCoreResponse.metadata === 'object' 
            ? Object.fromEntries(
                Object.entries(agentCoreResponse.metadata).filter(([key, value]) => 
                  typeof value !== 'function' && key !== 'constructor'
                )
              )
            : {}
          )
        },
        success: true
      };

      // Log response structure for debugging
      debugLog('AgentCore Response Structure', {
        sessionId: agentCoreResponse.sessionId,
        contentLength: agentCoreResponse.content?.length || 0,
        hasPatientContext: !!agentCoreResponse.patientContext,
        hasFileProcessingResults: !!agentCoreResponse.fileProcessingResults,
        metadataKeys: agentCoreResponse.metadata ? Object.keys(agentCoreResponse.metadata) : 'none',
        responsePreview: agentCoreResponse.content?.substring(0, 100) + '...'
      });

      // Extract structured fields from AgentCore response if available
      if (agentCoreResponse.patientContext) {
        chatResponse.patientContext = agentCoreResponse.patientContext;
      } else if (agentCoreResponse.metadata?.patientContext) {
        chatResponse.patientContext = agentCoreResponse.metadata.patientContext as any;
      }

      if (agentCoreResponse.guardrailInterventions) {
        chatResponse.guardrailInterventions = agentCoreResponse.guardrailInterventions;
      } else if (agentCoreResponse.metadata?.guardrailInterventions) {
        chatResponse.guardrailInterventions = agentCoreResponse.metadata.guardrailInterventions as any;
      }

      if (agentCoreResponse.fileProcessingResults) {
        chatResponse.fileProcessingResults = agentCoreResponse.fileProcessingResults;
      } else if (agentCoreResponse.metadata?.fileProcessingResults) {
        chatResponse.fileProcessingResults = agentCoreResponse.metadata.fileProcessingResults as any;
      }

      // Complete loading state
      if (onLoadingStateChange) {
        onLoadingStateChange({
          isLoading: false,
          stage: 'completing',
          progress: 100
        });
      }

      console.log('✅ HTTP response received and processed');
      console.log('📊 Processing time:', processingTime, 'ms');
      console.log('📝 Response content length:', chatResponse.content?.length || 0);

      return chatResponse;

    } catch (error) {
      console.error('❌ HTTP request failed:', error);

      // Complete loading state with error
      if (onLoadingStateChange) {
        onLoadingStateChange({
          isLoading: false,
          stage: 'completing',
          progress: 100
        });
      }

      // Handle AbortError specifically
      if (error instanceof Error && error.name === 'AbortError') {
        return {
          sessionId: sessionId,
          messageId: `error_${Date.now()}`,
          isComplete: true,
          content: '⚠️ Request was cancelled by user.',
          metadata: {
            requestId: `req_${Date.now()}`,
            timestamp: new Date().toISOString(),
            cancelled: true
          },
          success: false,
          errors: [{
            code: 'REQUEST_CANCELLED',
            message: 'Request was cancelled by user'
          }]
        };
      }

      // Return structured error response
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return {
        sessionId: sessionId,
        messageId: `error_${Date.now()}`,
        isComplete: true,
        content: `❌ **Error processing request**\n\n${errorMessage}`,
        metadata: {
          requestId: `req_${Date.now()}`,
          timestamp: new Date().toISOString(),
          error: true,
          errorType: error instanceof Error ? error.name : typeof error
        },
        success: false,
        errors: [{
          code: error instanceof Error ? error.name : 'UNKNOWN_ERROR',
          message: errorMessage,
          details: { originalError: error }
        }]
      };
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Cancel the current request
   */
  cancelRequest(): void {
    if (this.abortController) {
      console.log('🚫 Cancelling current request...');
      this.abortController.abort();
    }
  }

  /**
   * Convert message and attachments to Strands format
   */
  private convertToStrandsFormat(
    message: string,
    attachments?: Array<{
      fileName: string;
      fileType: string;
      mimeType: string;
      content?: string;
      s3Key?: string;
      fileSize: number;
    }>
  ): SendMessageRequest {
    const content: any[] = [];

    // Add text message
    if (message) {
      content.push({ text: message });
    }

    // Add attachments as multimodal content
    if (attachments) {
      for (const attachment of attachments) {
        if (!attachment.content) continue; // Skip S3-only attachments for now

        const mimeType = attachment.mimeType || attachment.fileType;

        if (mimeType.startsWith('image/')) {
          // Handle image content
          const formatMap: Record<string, string> = {
            'image/jpeg': 'jpeg',
            'image/jpg': 'jpeg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp'
          };

          const format = formatMap[mimeType] || 'jpeg';

          content.push({
            image: {
              format,
              source: {
                bytes: attachment.content
              }
            }
          });

        } else if (mimeType === 'application/pdf' || mimeType === 'text/plain' || 
                   mimeType.includes('document') || mimeType.includes('text')) {
          // Handle document content
          const formatMap: Record<string, string> = {
            'application/pdf': 'pdf',
            'text/plain': 'txt',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/markdown': 'md',
            'text/csv': 'csv',
            'application/vnd.ms-excel': 'xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'text/html': 'html'
          };

          const format = formatMap[mimeType] || 'txt';

          content.push({
            document: {
              format,
              name: attachment.fileName,
              source: {
                bytes: attachment.content
              }
            }
          });
        }
      }
    }

    return {
      content,
      sessionId: undefined // Will be set by caller
    };
  }


}

// Export singleton instance
export const chatService = new ChatService();

/**
 * useChat Hook
 * React hooks for chat-related API operations
 */

import { chatService, type StreamingChatResponse } from '../services';
import type {
  SendMessageRequest
} from '../types/api';
import { useApi } from './useApi';

export function useSendMessage() {
  return useApi<StreamingChatResponse>((data: SendMessageRequest) => 
    chatService.sendStreamingMessage(data)
  );
}

// Session management is handled by the lambda/AgentCore
// Lambda generates session IDs and frontend reuses them

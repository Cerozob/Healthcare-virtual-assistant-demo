/**
 * useChat Hook
 * React hooks for chat-related API operations
 */

import { chatService } from '../services';
import type {
  SendMessageRequest,
  SendMessageResponse
} from '../types/api';
import { useApi } from './useApi';

export function useSendMessage() {
  return useApi<SendMessageResponse>((data: SendMessageRequest) => 
    chatService.sendMessage(data)
  );
}

// Session management is handled by the lambda/AgentCore
// Lambda generates session IDs and frontend reuses them

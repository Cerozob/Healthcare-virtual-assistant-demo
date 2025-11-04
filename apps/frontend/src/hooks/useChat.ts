/**
 * useChat Hook
 * React hooks for chat-related API operations
 */

import { chatService } from '../services';
import type { ChatResponse } from '../services/chatService';
import { useApi } from './useApi';

export function useSendMessage() {
  return useApi<ChatResponse>((message: string, sessionId: string, attachments?: any[]) => 
    chatService.sendMessage(message, sessionId, attachments)
  );
}

// Session management is handled by the lambda/AgentCore
// Lambda generates session IDs and frontend reuses them

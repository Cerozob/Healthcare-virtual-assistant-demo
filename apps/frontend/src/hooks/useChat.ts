/**
 * useChat Hook
 * React hooks for chat-related API operations
 */

import { chatService } from '../services';
import { useApi } from './useApi';
import type {
  SendMessageRequest,
  SendMessageResponse,
  CreateSessionRequest,
  ChatSessionsResponse,
  ChatMessagesResponse,
  PaginationParams
} from '../types/api';

export function useSendMessage() {
  return useApi<SendMessageResponse>((data: SendMessageRequest) => 
    chatService.sendMessage(data)
  );
}

export function useChatSessions() {
  return useApi<ChatSessionsResponse>((params?: PaginationParams) => 
    chatService.getSessions(params)
  );
}

export function useCreateChatSession() {
  return useApi<{ message: string; session: any }>((data?: CreateSessionRequest) => 
    chatService.createSession(data)
  );
}

export function useChatMessages() {
  return useApi<ChatMessagesResponse>((sessionId: string, params?: PaginationParams) => 
    chatService.getSessionMessages(sessionId, params)
  );
}

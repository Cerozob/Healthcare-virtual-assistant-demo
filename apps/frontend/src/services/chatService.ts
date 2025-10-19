/**
 * Chat Service
 * Service class for chat-related API operations
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import {
  SendMessageRequest,
  SendMessageResponse,
  CreateSessionRequest,
  ChatSessionsResponse,
  ChatMessagesResponse,
  PaginationParams
} from '../types/api';

export class ChatService {
  /**
   * Send message to chat agent
   */
  async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse> {
    return apiClient.post<SendMessageResponse>(API_ENDPOINTS.chatMessage, data);
  }

  /**
   * Get list of chat sessions
   */
  async getSessions(params?: PaginationParams): Promise<ChatSessionsResponse> {
    return apiClient.get<ChatSessionsResponse>(API_ENDPOINTS.chatSessions, params);
  }

  /**
   * Create new chat session
   */
  async createSession(data?: CreateSessionRequest): Promise<{ message: string; session: any }> {
    return apiClient.post<{ message: string; session: any }>(API_ENDPOINTS.chatSessions, data || {});
  }

  /**
   * Get messages for a specific session
   */
  async getSessionMessages(sessionId: string, params?: PaginationParams): Promise<ChatMessagesResponse> {
    return apiClient.get<ChatMessagesResponse>(API_ENDPOINTS.chatSessionMessages(sessionId), params);
  }
}

// Export singleton instance
export const chatService = new ChatService();

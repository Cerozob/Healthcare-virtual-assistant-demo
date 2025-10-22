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
  PaginationParams,
  ChatMessage
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

  /**
   * Echo message functionality (placeholder for AI integration)
   * Simulates AI response by echoing the user's message
   */
  async sendEchoMessage(content: string, _sessionId?: string): Promise<{ userMessage: ChatMessage; agentMessage: ChatMessage }> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const timestamp = new Date().toISOString();
    const messageId = `msg_${Date.now()}`;

    const userMessage: ChatMessage = {
      id: messageId,
      content,
      type: 'user',
      timestamp
    };

    // Generate markdown response to demonstrate markdown rendering
    const markdownResponse = `# Respuesta del Asistente IA

Recibí tu mensaje: "${content}"

## Análisis del mensaje

- **Longitud**: ${content.length} caracteres
- **Palabras**: ${content.split(' ').length} palabras
- **Tipo**: ${content.includes('?') ? 'Pregunta' : 'Declaración'}

### Capacidades de Markdown

Este asistente puede mostrar contenido con formato **markdown** que incluye:

1. **Texto en negrita** y *texto en cursiva*
2. \`Código inline\` y bloques de código:

\`\`\`javascript
function ejemplo() {
  console.log("¡Hola mundo!");
  return "Markdown funciona correctamente";
}
\`\`\`

3. Listas ordenadas y no ordenadas
4. Enlaces como [este enlace a AWS](https://aws.amazon.com)
5. Tablas:

| Característica | Estado |
|----------------|--------|
| Markdown | ✅ Implementado |
| Código | ✅ Soportado |
| Tablas | ✅ Funcionando |

> **Nota**: Este es un ejemplo de blockquote para mostrar citas o información importante.

---

¿Hay algo específico en lo que pueda ayudarte?`;

    const agentMessage: ChatMessage = {
      id: `${messageId}_response`,
      content: markdownResponse,
      type: 'agent',
      agentType: 'echo',
      timestamp: new Date(Date.now() + 500).toISOString()
    };

    return { userMessage, agentMessage };
  }
}

// Export singleton instance
export const chatService = new ChatService();

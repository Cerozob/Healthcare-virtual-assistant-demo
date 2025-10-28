/**
 * Chat Service
 * Service class for chat-related API operations via API Gateway
 */

import { apiClient } from './apiClient';
import { API_ENDPOINTS } from '../config/api';
import type {
  SendMessageRequest,
  SendMessageResponse,
  ChatMessage
} from '../types/api';

// Define StreamingChatResponse type locally since we're no longer using agentCoreService
export interface StreamingChatResponse {
  sessionId: string;
  messageId: string;
  isComplete: boolean;
  content: string;
  metadata?: {
    apiGateway?: boolean;
    fallback?: boolean;
    echoMode?: boolean;
    responseTimeMs?: number;
    totalProcessingTimeMs?: number;
    patientContext?: any;
    originalResponse?: any;
  };
}

export class ChatService {
  /**
   * Send streaming message via API Gateway (primary method)
   */
  async sendStreamingMessage(
    data: SendMessageRequest,
    onChunk?: (chunk: StreamingChatResponse) => void,
    onComplete?: (finalResponse: StreamingChatResponse) => void,
    onError?: (error: Error) => void
  ): Promise<StreamingChatResponse> {
    try {
      console.group('📤 CHAT SERVICE STREAMING REQUEST');
      console.log('📝 Request data:', data);
      console.log('   • message length:', data.message?.length || 0);
      console.log('   • sessionId:', data.sessionId);
      console.log('   • attachments:', data.attachments?.length || 0);
      console.groupEnd();

      // Use API Gateway endpoint for AgentCore communication
      const response = await this.sendMessage(data);
      
      // Convert to streaming response format for compatibility
      const streamingResponse: StreamingChatResponse = {
        sessionId: response.sessionId || `api_session_${Date.now()}`,
        messageId: `api_${Date.now()}`,
        isComplete: true,
        content: response.response || response.message || 'No response received',
        metadata: { 
          apiGateway: true,
          responseTimeMs: response.responseTimeMs,
          totalProcessingTimeMs: response.totalProcessingTimeMs,
          patientContext: response.patient_context
        }
      };

      // Simulate streaming by calling onChunk and onComplete
      if (onChunk) {
        onChunk(streamingResponse);
      }
      
      if (onComplete) {
        onComplete(streamingResponse);
      }

      return streamingResponse;
    } catch (error: unknown) {
      console.error('API Gateway request failed, falling back to echo mode:', error);
      
      if (onError) {
        onError(error as Error);
      }

      // Fallback to echo mode
      const echoResponse = await this.sendEchoMessage(data.message, data.sessionId);
      
      const streamingResponse: StreamingChatResponse = {
        sessionId: data.sessionId || `echo_session_${Date.now()}`,
        messageId: `echo_${Date.now()}`,
        isComplete: true,
        content: `⚠️ **Modo de desarrollo activo** - El servicio no está disponible.\n\n${echoResponse.agentMessage.content}`,
        metadata: { 
          fallback: true,
          echoMode: true
        }
      };

      if (onComplete) {
        onComplete(streamingResponse);
      }

      return streamingResponse;
    }
  }

  /**
   * Send message to API Gateway AgentCore endpoint
   */
  async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse> {
    try {
      // 🔍 DEBUG: Log outgoing request
      console.group('📤 CHAT SERVICE REQUEST');
      console.log('🎯 Endpoint:', API_ENDPOINTS.agentCoreChat);
      console.log('📝 Request data:', data);
      console.log('   • message length:', data.message?.length || 0);
      console.log('   • sessionId:', data.sessionId);
      console.log('   • attachments:', data.attachments?.length || 0);
      console.groupEnd();

      const response = await apiClient.post<SendMessageResponse>(API_ENDPOINTS.agentCoreChat, data);

      // 🔍 DEBUG: Log incoming response
      console.group('📥 CHAT SERVICE RESPONSE');
      console.log('✅ Raw response from API:', response);
      console.log('📝 Response message:', response.response || response.message);
      console.log('🔑 Session ID:', response.sessionId);
      console.log('👤 Patient context exists:', !!response.patient_context);
      
      if (response.patient_context) {
        console.log('👤 Patient context details:');
        console.log('   • patient_found:', response.patient_context.patient_found);
        console.log('   • patient_id:', response.patient_context.patient_id);
        console.log('   • patient_name:', response.patient_context.patient_name);
        console.log('   • patient_data:', response.patient_context.patient_data);
        
        if (response.patient_context.patient_data) {
          console.log('📋 Patient data structure:');
          console.log('   • Keys:', Object.keys(response.patient_context.patient_data));
          console.log('   • Values:', response.patient_context.patient_data);
        }
      }
      console.groupEnd();

      // Ensure we have a proper response format
      const formattedResponse = {
        response: response.response || response.message || 'No response received',
        sessionId: response.sessionId || data.sessionId || `session_${Date.now()}`,
        timestamp: response.timestamp || new Date().toISOString(),
        patient_context: response.patient_context // Pass through patient context from agent
      };

      // 🔍 DEBUG: Log formatted response
      console.group('🔄 FORMATTED RESPONSE');
      console.log('📦 Final response object:', formattedResponse);
      console.groupEnd();

      return formattedResponse;
    } catch (error: unknown) {
      console.error('AgentCore request failed, falling back to echo mode:', error);

      // Check if it's a network error or server error
      const errorWithResponse = error as { response?: { status?: number } };
      const isNetworkError = !errorWithResponse?.response;
      const statusCode = errorWithResponse?.response?.status;

      if (isNetworkError || (statusCode && statusCode >= 500)) {
        console.warn('Using echo mode due to service unavailability');
        // Fallback to echo mode if AgentCore is not available
        const echoResponse = await this.sendEchoMessage(data.message, data.sessionId);
        return {
          response: `⚠️ **Modo de desarrollo activo** - El servicio AgentCore no está disponible.\n\n${echoResponse.agentMessage.content}`,
          sessionId: data.sessionId || `session_${Date.now()}`,
          timestamp: new Date().toISOString()
        };
      } else {
        // Re-throw client errors (4xx)
        throw error;
      }
    }
  }

  // Session management methods removed - AgentCore handles sessions internally

  /**
   * Echo message functionality (placeholder for AI integration)
   * Simulates AI response by echoing the user's message with patient context awareness
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

    // Parse patient context and document information from the content
    const hasPatientContext = content.includes('[Contexto del paciente:');
    const hasDocuments = content.includes('[Documentos adjuntos');
    const noPatientContext = content.includes('[Sin contexto de paciente seleccionado]');

    let patientInfo = '';
    let documentInfo = '';
    let actualMessage = content;

    // Extract patient information
    if (hasPatientContext) {
      const patientMatch = content.match(/\[Contexto del paciente: ([^\]]+)\]/);
      if (patientMatch) {
        patientInfo = patientMatch[1];
        actualMessage = content.replace(patientMatch[0], '').trim();
      }
    }

    // Extract document information
    if (hasDocuments) {
      const docMatch = content.match(/\[Documentos adjuntos[^\]]*:\n([^\]]+)\]/);
      if (docMatch) {
        documentInfo = docMatch[1];
        actualMessage = actualMessage.replace(/\[Documentos adjuntos[^\]]*:\n[^\]]+\]/, '').trim();
      }
    }

    // Generate contextual response
    let markdownResponse = `# Asistente Virtual de Salud (Modo Echo)

`;

    if (noPatientContext) {
      markdownResponse += `⚠️ **Sin contexto de paciente**: Para obtener respuestas más precisas y personalizadas, por favor seleccione un paciente en el panel lateral.

`;
    } else if (hasPatientContext) {
      markdownResponse += `👤 **Paciente**: ${patientInfo}

`;
    }

    if (hasDocuments) {
      markdownResponse += `📄 **Documentos procesados**:
${documentInfo.split('\n').map(line => `- ${line.trim()}`).join('\n')}

> Los documentos han sido subidos al flujo de trabajo de documentos y serán procesados automáticamente según las pautas establecidas.

`;
    }

    markdownResponse += `## Tu consulta
"${actualMessage}"

## Respuesta del Asistente

`;

    // Generate contextual response based on content
    if (actualMessage.toLowerCase().includes('historia') || actualMessage.toLowerCase().includes('historial')) {
      markdownResponse += `Entiendo que necesitas información sobre el historial médico${hasPatientContext ? ' del paciente' : ''}. `;
      if (hasPatientContext) {
        markdownResponse += `Con el contexto del paciente ${patientInfo}, puedo ayudarte a revisar su historial médico y identificar patrones relevantes.`;
      } else {
        markdownResponse += `Para proporcionarte información específica del historial, necesitaría que selecciones un paciente.`;
      }
    } else if (actualMessage.toLowerCase().includes('cita') || actualMessage.toLowerCase().includes('agendar')) {
      markdownResponse += `Para agendar una cita${hasPatientContext ? ` para ${patientInfo}` : ''}, necesitaré la siguiente información:

- Tipo de examen o consulta
- Fecha y hora preferida
- Médico especialista (si aplica)
- Motivo de la consulta

${hasPatientContext ? `Con el paciente ya seleccionado, podemos proceder con el agendamiento.` : `Por favor selecciona un paciente para continuar con el agendamiento.`}`;
    } else if (actualMessage.toLowerCase().includes('síntomas') || actualMessage.toLowerCase().includes('sintomas')) {
      markdownResponse += `Para analizar síntomas${hasPatientContext ? ` del paciente ${patientInfo}` : ''}, puedo ayudarte a:

1. **Revisar síntomas actuales** y su duración
2. **Comparar con historial previo** de síntomas similares
3. **Identificar patrones** o síntomas recurrentes
4. **Sugerir seguimiento** médico apropiado

${hasPatientContext ? `Con el contexto del paciente, puedo proporcionar un análisis más detallado.` : `Selecciona un paciente para un análisis personalizado.`}`;
    } else {
      markdownResponse += `He recibido tu mensaje y estoy listo para ayudarte. ${hasPatientContext ? `Con el contexto del paciente ${patientInfo}, ` : ''}Puedo asistirte con:

- 📋 **Revisión de historiales médicos**
- 📅 **Agendamiento de citas**
- 🔍 **Análisis de síntomas**
- 📊 **Consulta de resultados de exámenes**
- 💊 **Información sobre medicamentos**`;
    }

    markdownResponse += `

---

### Capacidades del Sistema

| Función | Estado | Descripción |
|---------|--------|-------------|
| Contexto de Paciente | ${hasPatientContext ? '✅ Activo' : '⚠️ No seleccionado'} | Información específica del paciente |
| Procesamiento de Documentos | ${hasDocuments ? '✅ Procesando' : '⏸️ Sin documentos'} | Clasificación automática de documentos |
| Flujo de Trabajo | ✅ Implementado | Seguimiento de pautas de documentos |
| Modo Echo | ✅ Activo | Simulación de respuestas (desarrollo) |

> **Nota**: Este es el modo de desarrollo (echo). En producción, las consultas serán procesadas por agentes de IA especializados en salud.

¿En qué más puedo ayudarte?`;

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

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Alert,
} from "@cloudscape-design/components";
import ChatMessageList from "./chat-message-list";
import ChatInput from "./chat-input";
import type { ChatMessage } from "../../types/chat";
import { getCurrentISO8601, generateTimestampId } from "../../common/helpers/datetime-helper";

interface ChatInterfaceProps {
  sessionId?: string;
}

export default function ChatInterface({
  sessionId: _sessionId,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = async (content: string, files?: File[]) => {
    if (!content.trim() && (!files || files.length === 0)) return;

    // Add user message to UI
    const userMessage: ChatMessage = {
      id: generateTimestampId('temp'),
      content,
      type: "user",
      timestamp: getCurrentISO8601(),
      attachments: files?.map((f) => ({
        name: f.name,
        size: f.size,
        type: f.type,
        status: "uploading",
      })),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // TODO: Implement WebSocket or SSE connection for real-time messaging
      // TODO: Upload files to S3 if attachments exist
      // TODO: Call chat Lambda function via API Gateway
      // TODO: Handle streaming responses from orchestrator agent
      // TODO: Update message status (uploading -> processing -> complete)
      // TODO: Handle document processing status updates
      
      // For now, simulate a response
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const agentMessage: ChatMessage = {
        id: generateTimestampId('agent'),
        content: "Esta es una respuesta de prueba. Integración de API de chat pendiente.",
        type: "agent",
        timestamp: getCurrentISO8601(),
        agentType: "orchestrator",
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al enviar el mensaje"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Asistente de salud con inteligencia artificial"
        >
          Asistente Médico de Chat
        </Header>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Alert
            type="error"
            dismissible
            onDismiss={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        <Box padding={{ vertical: "l" }}>
          <ChatMessageList messages={messages} isLoading={isLoading} />
          <div ref={messagesEndRef} />
        </Box>

        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
        />
      </SpaceBetween>
    </Container>
  );
}

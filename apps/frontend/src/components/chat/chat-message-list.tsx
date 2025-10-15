import { Box, SpaceBetween, Spinner } from "@cloudscape-design/components";
import ChatMessageItem from "./chat-message-item";
import { ChatMessage } from "../../types/chat";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export default function ChatMessageList({
  messages,
  isLoading,
}: ChatMessageListProps) {
  return (
    <SpaceBetween size="m">
      {messages.length === 0 ? (
        <Box textAlign="center" color="text-body-secondary" padding="xxl">
          Inicia una conversación escribiendo un mensaje abajo
        </Box>
      ) : (
        messages.map((message) => (
          <ChatMessageItem key={message.id} message={message} />
        ))
      )}
      
      {/* TODO: Implement typing indicator component */}
      {isLoading && (
        <Box padding="s">
          <SpaceBetween size="xs" direction="horizontal">
            <Spinner size="normal" />
            <Box color="text-body-secondary">El asistente está pensando...</Box>
          </SpaceBetween>
        </Box>
      )}
    </SpaceBetween>
  );
}

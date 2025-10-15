import { Box, SpaceBetween, Badge, Icon } from "@cloudscape-design/components";
import { ChatMessage } from "../../types/chat";
import { formatTimeFromISO8601 } from "../../common/helpers/datetime-helper";

interface ChatMessageItemProps {
  message: ChatMessage;
}

export default function ChatMessageItem({ message }: ChatMessageItemProps) {
  const isUser = message.type === "user";

  return (
    <Box
      padding="m"
      margin={{ bottom: "s" }}
      float={isUser ? "right" : "left"}
    >
      <SpaceBetween size="xs">
        <Box>
          <SpaceBetween size="xxs" direction="horizontal">
            {!isUser && message.agentType && (
              <Badge color="blue">{message.agentType}</Badge>
            )}
            <Box fontSize="body-s" color="text-body-secondary">
              {formatTimeFromISO8601(message.timestamp)}
            </Box>
          </SpaceBetween>
        </Box>

        <Box
          padding="s"
        >
          {message.content}
        </Box>

        {/* TODO: Implement document attachment display */}
        {message.attachments && message.attachments.length > 0 && (
          <SpaceBetween size="xxs">
            {message.attachments.map((attachment, idx) => (
              <Box key={idx} fontSize="body-s">
                <SpaceBetween size="xxs" direction="horizontal">
                  <Icon name="file" />
                  <span>{attachment.name}</span>
                  {/* TODO: Show upload/processing status with proper icons */}
                  {attachment.status === "uploading" && <Badge color="grey">Subiendo...</Badge>}
                  {attachment.status === "processing" && <Badge color="blue">Procesando...</Badge>}
                  {attachment.status === "complete" && <Badge color="green">Listo</Badge>}
                  {attachment.status === "error" && <Badge color="red">Error</Badge>}
                </SpaceBetween>
              </Box>
            ))}
          </SpaceBetween>
        )}
      </SpaceBetween>
    </Box>
  );
}

/**
 * ChatBubble Component
 * Displays individual chat messages with avatars and markdown support
 */

import { Box, Icon } from '@cloudscape-design/components';
import ReactMarkdown from 'react-markdown';
import { ChatMessage } from '../../types/api';
import { AttachmentDisplay } from './AttachmentDisplay';
import { SourceReferences } from './SourceReferences';

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.type === 'user';
  const isAgent = message.type === 'agent';

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('es-MX', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Get avatar icon based on message type
  const getAvatarIcon = (): 'user-profile' | 'contact' | 'status-info' => {
    if (isUser) return 'user-profile';
    if (isAgent) return 'contact';
    return 'status-info';
  };

  // Get avatar background color
  const getAvatarColor = () => {
    if (isUser) return '#0972d3';
    if (isAgent) return '#037f0c';
    return '#5f6b7a';
  };

  return (
    <Box
      padding="s"
      variant="div"
    >
      <div
        style={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          gap: '12px',
          alignItems: 'flex-start'
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            backgroundColor: getAvatarColor(),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          <Icon name={getAvatarIcon()} variant="inverted" size="medium" />
        </div>

        {/* Message Content */}
        <div
          style={{
            maxWidth: '70%',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}
        >
          {/* Message Bubble */}
          <div
            style={{
              backgroundColor: isUser ? '#f2f8fd' : '#ffffff',
              border: '1px solid #e9ebed',
              borderRadius: '8px',
              wordBreak: 'break-word',
              padding: '12px'
            }}
          >
            <div style={{ fontSize: '14px', lineHeight: '20px' }}>
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <AttachmentDisplay attachments={message.attachments} />
          )}

          {/* Source References */}
          {message.sources && message.sources.length > 0 && (
            <SourceReferences sources={message.sources} />
          )}

          {/* Timestamp */}
          <Box
            fontSize="body-s"
            color="text-body-secondary"
            textAlign={isUser ? 'right' : 'left'}
          >
            {formatTime(message.timestamp)}
          </Box>
        </div>
      </div>
    </Box>
  );
}

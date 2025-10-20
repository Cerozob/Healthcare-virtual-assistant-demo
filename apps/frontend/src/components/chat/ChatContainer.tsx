/**
 * ChatContainer Component
 * Main chat interface container with message history and input area
 */

import { useEffect, useRef } from 'react';
import { Box, SpaceBetween } from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import { ChatMessage } from '../../types/api';

interface ChatContainerProps {
  sessionId?: string;
  messages: ChatMessage[];
  onSendMessage?: (content: string, files?: File[]) => void;
  isLoading?: boolean;
  children?: React.ReactNode;
}

export function ChatContainer({
  messages,
  children
}: ChatContainerProps) {
  const { t } = useLanguage();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <Box padding={{ vertical: 'l', horizontal: 'l' }}>
      <SpaceBetween size="l">
        {/* Message History Area */}
        <Box
          padding="l"
          variant="div"
        >
          <div
            style={{
              minHeight: '400px',
              maxHeight: '600px',
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}
          >
            {messages.length === 0 ? (
              <Box textAlign="center" color="text-body-secondary" padding="xxl">
                {t.chat.placeholder}
              </Box>
            ) : (
              <>
                {children}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </Box>

        {/* Input Area - Will be populated by PromptInput component */}
        <Box>
          {/* Input component will be passed as children or rendered separately */}
        </Box>
      </SpaceBetween>
    </Box>
  );
}

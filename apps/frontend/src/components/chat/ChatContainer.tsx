/**
 * ChatContainer Component
 * Main chat interface container with message history and input area
 */

import { useEffect, useRef, useState } from 'react';
import { Box, SpaceBetween, Button } from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import { ChatMessage } from '../../types/api';
import { ErrorState } from './ErrorState';

interface ChatContainerProps {
  sessionId?: string;
  messages: ChatMessage[];
  onSendMessage?: (content: string, files?: File[]) => void;
  isLoading?: boolean;
  error?: string;
  onRetry?: () => void;
  onErrorDismiss?: () => void;
  children?: React.ReactNode;
  hasPatientContext?: boolean;
}

export function ChatContainer({
  messages,
  onSendMessage,
  isLoading,
  error,
  onRetry,
  onErrorDismiss,
  children,
  hasPatientContext = false
}: ChatContainerProps) {
  const { t } = useLanguage();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showSupportPrompts, setShowSupportPrompts] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Show support prompts based on context
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    const shouldShowPrompts = !isLoading && 
      (!lastMessage || (lastMessage.type === 'agent' && !error));
    setShowSupportPrompts(shouldShowPrompts);
  }, [messages, isLoading, error]);

  // Default prompts for different contexts
  const DEFAULT_PROMPTS = {
    initial: [
      "¿Puedes ayudarme a revisar el historial médico de este paciente?",
      "¿Qué información necesitas para hacer un diagnóstico?",
      "Explícame los resultados de los análisis más recientes",
      "¿Hay alguna interacción medicamentosa que deba considerar?"
    ],
    afterResponse: [
      "¿Puedes explicar esto con más detalle?",
      "¿Hay alguna recomendación adicional?",
      "¿Qué debo hacer a continuación?",
      "¿Necesitas más información?"
    ],
    patientContext: [
      "Analiza los síntomas actuales del paciente",
      "Revisa el plan de tratamiento actual",
      "¿Hay algún riesgo que deba considerar?",
      "Sugiere próximos pasos en el tratamiento"
    ]
  };

  // Get appropriate prompts based on context
  const getSupportPrompts = () => {
    if (messages.length === 0) {
      return hasPatientContext ? DEFAULT_PROMPTS.patientContext : DEFAULT_PROMPTS.initial;
    }
    return DEFAULT_PROMPTS.afterResponse;
  };

  const handlePromptSelect = (prompt: string) => {
    onSendMessage?.(prompt);
  };

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
                {error && (
                  <ErrorState
                    error={error}
                    type="processing"
                    onRetry={onRetry}
                    onDismiss={onErrorDismiss}
                  />
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </Box>

        {/* Support Prompts */}
        {showSupportPrompts && (
          <Box padding={{ vertical: 'm', horizontal: 'l' }}>
            <Box
              fontSize="body-s"
              fontWeight="bold"
              color="text-label"
              padding={{ bottom: 's' }}
            >
              Suggested prompts
            </Box>
            <SpaceBetween size="xs">
              {getSupportPrompts().map((prompt, index) => (
                <Button
                  key={index}
                  variant="link"
                  onClick={() => handlePromptSelect(prompt)}
                  disabled={isLoading}
                  formAction="none"
                >
                  {prompt}
                </Button>
              ))}
            </SpaceBetween>
          </Box>
        )}

        {/* Input Area - Will be populated by PromptInput component */}
        <Box>
          {/* Input component will be passed as children or rendered separately */}
        </Box>
      </SpaceBetween>
    </Box>
  );
}

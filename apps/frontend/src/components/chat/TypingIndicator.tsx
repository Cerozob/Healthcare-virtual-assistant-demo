/**
 * TypingIndicator Component
 * Shows when the AI is processing a response
 */

import { Box, Icon } from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';

export function TypingIndicator() {
  const { t } = useLanguage();

  return (
    <Box padding="s" variant="div">
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
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
            backgroundColor: '#037f0c',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}
        >
          <Icon name="contact" variant="inverted" size="medium" />
        </div>

        {/* Typing Animation */}
        <div
          style={{
            padding: '12px',
            backgroundColor: '#ffffff',
            border: '1px solid #e9ebed',
            borderRadius: '8px',
            minWidth: '80px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Box fontSize="body-s" color="text-body-secondary">
              {t.chat.typing}
            </Box>
            <div style={{ display: 'flex', gap: '4px' }}>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: '#5f6b7a',
                    animation: `typing 1.4s infinite ${i * 0.2}s`
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes typing {
          0%, 60%, 100% {
            opacity: 0.3;
            transform: translateY(0);
          }
          30% {
            opacity: 1;
            transform: translateY(-4px);
          }
        }
      `}</style>
    </Box>
  );
}

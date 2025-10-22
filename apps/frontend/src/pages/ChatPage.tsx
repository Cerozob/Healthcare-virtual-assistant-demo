import { useState } from 'react';
import { Container, Header, SpaceBetween, Alert, Box, Grid, Modal, Button, Icon } from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import { ChatContainer, ChatBubble, PromptInput, PatientChatSidebar } from '../components/chat';
import { PatientSelector } from '../components/patient';
import { useLanguage } from '../contexts/LanguageContext';
import { usePatientContext } from '../contexts/PatientContext';
import { chatService } from '../services/chatService';
import { examService } from '../services/examService';
import type { ChatMessage, Patient } from '../types/api';

interface ChatPageProps {
  signOut?: () => void;
  user?: {
    signInDetails?: {
      loginId?: string;
    };
  };
}

// Wrapper component to integrate PatientSelector with PatientContext
function PatientSelectorWrapper({ onComplete }: { onComplete: () => void }) {
  const { setSelectedPatient, setPatientExams } = usePatientContext();

  const handlePatientSelect = async (patient: Patient | null) => {
    setSelectedPatient(patient);
    
    // Load patient exams if patient is selected
    if (patient) {
      try {
        // TODO: Implement patient-specific exam filtering in the API
        const examsResponse = await examService.getExams();
        // Filter exams by patient ID on the client side for now
        const patientExams = examsResponse.exams.filter(exam => 
          exam.patient_id === patient.patient_id
        );
        setPatientExams(patientExams);
      } catch (error) {
        console.error('Error loading patient exams:', error);
        setPatientExams([]);
      }
    } else {
      setPatientExams([]);
    }
  };

  return (
    <PatientSelector 
      onPatientSelect={handlePatientSelect}
      onPatientSelected={onComplete}
    />
  );
}

export default function ChatPage({ signOut, user }: ChatPageProps) {
  const { t } = useLanguage();
  const { selectedPatient, isPatientSelected, clearPatient } = usePatientContext();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<'processing' | 'generating'>('processing');
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState<string>(`session_${Date.now()}`);
  const [showPatientSelector, setShowPatientSelector] = useState(false);

  const handleSendMessage = async (content: string, _files?: File[]) => {
    setIsLoading(true);
    setLoadingStage('processing');
    setError(null);

    try {
      // Include patient context in the message if available
      const contextualContent = selectedPatient 
        ? `[Contexto del paciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})]\n\n${content}`
        : content;

      // Use echo functionality as placeholder
      const { userMessage, agentMessage } = await chatService.sendEchoMessage(contextualContent, sessionId);

      // Add user message immediately (show original content without context prefix)
      setMessages(prev => [...prev, { ...userMessage, content }]);

      // Simulate processing stage
      setTimeout(() => {
        setLoadingStage('generating');
      }, 500);

      // Simulate generation stage with response
      setTimeout(() => {
        setMessages(prev => [...prev, agentMessage]);
        setIsLoading(false);
      }, 1500);

      // TODO: Replace with actual AI integration
      // const response = await chatService.sendMessage({
      //   content: contextualContent,
      //   sessionId,
      //   attachments: _files?.map(f => ({ name: f.name, type: f.type, url: '' }))
      // });
      // setMessages(prev => [...prev, response.userMessage, response.agentMessage]);
      // setIsLoading(false);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setError(error instanceof Error ? error.message : t.errors.generic);
    }
  };

  const handleFeedback = async (messageId: string, feedback: 'positive' | 'negative', details?: string) => {
    try {
      // TODO: Implement actual feedback API call
      console.log('Feedback submitted:', { messageId, feedback, details });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // You could update the message with feedback status if needed
      // setMessages(prev => prev.map(msg => 
      //   msg.id === messageId 
      //     ? { ...msg, feedback: { type: feedback, details } }
      //     : msg
      // ));
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  };

  const handleRetry = () => {
    setError(null);
    // Optionally retry the last message
  };

  const handleErrorDismiss = () => {
    setError(null);
  };

  const handleChangePatient = () => {
    setShowPatientSelector(true);
  };

  const handleClearPatient = () => {
    clearPatient();
    // Add system message about patient context being cleared
    const systemMessage: ChatMessage = {
      id: `system_${Date.now()}`,
      content: 'Contexto del paciente eliminado. Las siguientes consultas no incluirán información del paciente.',
      type: 'system',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const handlePatientSelected = () => {
    setShowPatientSelector(false);
    // Add system message about new patient context
    if (selectedPatient) {
      const systemMessage: ChatMessage = {
        id: `system_${Date.now()}`,
        content: `Contexto del paciente actualizado: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})`,
        type: 'system',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, systemMessage]);
    }
  };

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header variant="h1">{t.chat.title}</Header>
        
        {/* Patient Context Alert - Compact version */}
        {!isPatientSelected && (
          <Alert type="info" header="Sugerencia">
            Puede seleccionar un paciente para incluir su contexto en las consultas del chat.
          </Alert>
        )}
        
        <Grid gridDefinition={[{ colspan: { default: 12, s: 8 } }, { colspan: { default: 12, s: 4 } }]}>
          {/* Chat Area */}
          <Container>
            <ChatContainer
              sessionId={sessionId}
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              error={error || undefined}
              onRetry={handleRetry}
              onErrorDismiss={handleErrorDismiss}
              hasPatientContext={isPatientSelected}
            >
              {messages.map((message) => (
                <ChatBubble 
                  key={message.id} 
                  message={message} 
                  onFeedback={handleFeedback}
                />
              ))}
              {isLoading && (
                <Box padding="s" variant="div">
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'row',
                      gap: '12px',
                      alignItems: 'flex-start'
                    }}
                  >
                    {/* Avatar with loading state */}
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
                      role="img"
                      aria-label="Generative AI assistant"
                    >
                      <Icon name="gen-ai" variant="inverted" size="medium" />
                    </div>

                    {/* Loading message bubble */}
                    <div
                      style={{
                        padding: '12px',
                        backgroundColor: '#ffffff',
                        border: '1px solid #e9ebed',
                        borderRadius: '8px',
                        minWidth: '120px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Box fontSize="body-s" color="text-body-secondary">
                          {loadingStage === 'processing' ? 'Processing your request' : 'Generating a response'}
                        </Box>
                        {loadingStage === 'generating' && (
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
                        )}
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
              )}
            </ChatContainer>
            
            <PromptInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </Container>

          {/* Patient Sidebar */}
          <PatientChatSidebar
            patient={selectedPatient}
            onChangePatient={handleChangePatient}
            onClearPatient={isPatientSelected ? handleClearPatient : undefined}
          />
        </Grid>
      </SpaceBetween>

      {/* Patient Selection Modal */}
      <Modal
        visible={showPatientSelector}
        onDismiss={() => setShowPatientSelector(false)}
        header="Seleccionar paciente"
        footer={
          <Box float="right">
            <Button variant="link" onClick={() => setShowPatientSelector(false)}>
              Cancelar
            </Button>
          </Box>
        }
      >
        <PatientSelectorWrapper onComplete={handlePatientSelected} />
      </Modal>
    </MainLayout>
  );
}

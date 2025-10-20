import { useState } from 'react';
import { Container, Header, SpaceBetween, Alert, Box, Grid, Modal, Button } from '@cloudscape-design/components';
import { MainLayout } from '../components/layout';
import { ChatContainer, ChatBubble, PromptInput, TypingIndicator, PatientChatSidebar } from '../components/chat';
import { PatientSelector } from '../components/patient';
import { useLanguage } from '../contexts/LanguageContext';
import { usePatientContext } from '../contexts/PatientContext';
import { chatService } from '../services/chatService';
import { examService } from '../services/examService';
import { ChatMessage, Patient } from '../types/api';

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
        const examsResponse = await examService.getExams({ patient_id: patient.patient_id } as any);
        setPatientExams(examsResponse.exams);
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
  const [sessionId] = useState<string>(`session_${Date.now()}`);
  const [showPatientSelector, setShowPatientSelector] = useState(false);

  const handleSendMessage = async (content: string, _files?: File[]) => {
    setIsLoading(true);

    try {
      // Include patient context in the message if available
      const contextualContent = selectedPatient 
        ? `[Contexto del paciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})]\n\n${content}`
        : content;

      // Use echo functionality as placeholder
      const { userMessage, agentMessage } = await chatService.sendEchoMessage(contextualContent, sessionId);

      // Add user message immediately (show original content without context prefix)
      setMessages(prev => [...prev, { ...userMessage, content }]);

      // Simulate typing delay before showing agent response
      setTimeout(() => {
        setMessages(prev => [...prev, agentMessage]);
        setIsLoading(false);
      }, 1000);

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
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        content: t.errors.generic,
        type: 'system',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
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
            >
              {messages.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}
              {isLoading && <TypingIndicator />}
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

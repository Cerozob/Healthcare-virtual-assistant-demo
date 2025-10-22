import { useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Grid,
  Modal,
  Button,

  PromptInput,
  FileInput,
  FileTokenGroup,

} from '@cloudscape-design/components';

import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import SupportPromptGroup from '@cloudscape-design/chat-components/support-prompt-group';
import { MainLayout } from '../components/layout';
import { PatientChatSidebar, MarkdownRenderer } from '../components/chat';
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
    username?: string;
    attributes?: {
      name?: string;
      given_name?: string;
      family_name?: string;
      email?: string;
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
  const [sessionId] = useState<string>(`session_${Date.now()}`);
  const [showPatientSelector, setShowPatientSelector] = useState(false);

  // Prompt input state
  const [promptValue, setPromptValue] = useState('');
  const [files, setFiles] = useState<File[]>([]);

  // Get user's full name for UI customization
  const getUserDisplayName = () => {
    if (user?.attributes?.name) return user.attributes.name;
    if (user?.attributes?.given_name && user?.attributes?.family_name) {
      return `${user.attributes.given_name} ${user.attributes.family_name}`;
    }
    if (user?.attributes?.given_name) return user.attributes.given_name;
    if (user?.username) return user.username;
    if (user?.signInDetails?.loginId) return user.signInDetails.loginId;
    return 'Usuario';
  };

  const getUserInitials = () => {
    const name = getUserDisplayName();
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const handleSendMessage = async () => {
    if (!promptValue.trim() && files.length === 0) return;

    // Create user message immediately
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: promptValue,
      type: 'user',
      timestamp: new Date().toISOString()
    };

    // Add user message immediately to UI
    setMessages(prev => [...prev, userMessage]);

    // Clear input immediately
    const messageContent = promptValue;
    setPromptValue('');
    setFiles([]);

    // Start loading process
    setIsLoading(true);
    setLoadingStage('processing');

    try {
      // Include patient context in the message if available
      const contextualContent = selectedPatient
        ? `[Contexto del paciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})]\n\n${messageContent}`
        : messageContent;

      // Use echo functionality as placeholder
      const { agentMessage } = await chatService.sendEchoMessage(contextualContent, sessionId);

      // Simulate processing stage
      setTimeout(() => {
        setLoadingStage('generating');
      }, 500);

      // Simulate generation stage with response
      setTimeout(() => {
        setMessages(prev => [...prev, agentMessage]);
        setIsLoading(false);
      }, 1500);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
    }
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
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
        <Header
          variant="h1"
          description={`Bienvenido, ${getUserDisplayName()}`}
        >
          {t.chat.title}
        </Header>



        <Grid gridDefinition={[{ colspan: { default: 12, s: 8 } }, { colspan: { default: 12, s: 4 } }]}>
          {/* Chat Area */}
          <Container>
            <SpaceBetween size="l">
              {/* Chat Messages */}
              <Box padding="l">
                <div className="chat-messages-container">
                  {messages.length === 0 ? (
                    <Box textAlign="center" color="text-body-secondary" padding="xxl">
                      {t.chat.placeholder}
                    </Box>
                  ) : (
                    messages.map((message) => {
                      const isUser = message.type === 'user';
                      const isAgent = message.type === 'agent';

                      const formatTime = (timestamp: string) => {
                        const date = new Date(timestamp);
                        return date.toLocaleString('es-MX', {
                          hour: '2-digit',
                          minute: '2-digit',
                          day: 'numeric',
                          month: 'short'
                        });
                      };

                      const avatar = isUser ? (
                        <Avatar
                          ariaLabel={getUserDisplayName()}
                          tooltipText={getUserDisplayName()}
                          initials={getUserInitials()}
                        />
                      ) : (
                        <Avatar
                          ariaLabel="Generative AI assistant"
                          color="gen-ai"
                          iconName="gen-ai"
                          tooltipText="Generative AI assistant"
                        />
                      );

                      const actions = isAgent ? (
                        <Button
                          variant="icon"
                          iconName="copy"
                          onClick={() => handleCopy(message.content)}
                          ariaLabel="Copy message"
                        />
                      ) : undefined;

                      return (
                        <div
                          key={message.id}
                          className={`chat-bubble-wrapper ${isUser ? 'outgoing' : 'incoming'}`}
                        >
                          <ChatBubble
                            ariaLabel={`${isUser ? getUserDisplayName() : 'Generative AI assistant'} at ${formatTime(message.timestamp)}`}
                            type={isUser ? "outgoing" : "incoming"}
                            avatar={avatar}
                            actions={actions}
                          >
                            <MarkdownRenderer content={message.content} />
                          </ChatBubble>
                        </div>
                      );
                    })
                  )}

                  {/* Loading State */}
                  {isLoading && (
                    <div className="chat-bubble-wrapper incoming">
                      <ChatBubble
                        ariaLabel="Generative AI assistant generating response"
                        showLoadingBar
                        type="incoming"
                        avatar={
                          <Avatar
                            loading={loadingStage === 'generating'}
                            color="gen-ai"
                            iconName="gen-ai"
                            ariaLabel="Generative AI assistant"
                            tooltipText="Generative AI assistant"
                          />
                        }
                      >
                        <Box color="text-status-inactive">
                          {loadingStage === 'processing' ? 'Analizando solicitud' : 'Generando respuesta'}
                        </Box>
                      </ChatBubble>
                    </div>
                  )}
                </div>
              </Box>

              {/* Support Prompts */}
              {!isLoading && messages.length === 0 && (
                <Box padding="l">
                  <SupportPromptGroup
                    onItemClick={({ detail }) => {
                      const selectedPrompt = [
                        "¿Puedes ayudarme a revisar el historial médico de este paciente?",
                        "¿Qué información necesitas para agendar una cita?",
                        "Agenda una cita para este paciente",
                        "¿Este paciente presenta síntomas recurrentes?"
                      ].find((_, index) => `prompt-${index}` === detail.id);

                      if (selectedPrompt) {
                        setPromptValue(selectedPrompt);
                        setTimeout(handleSendMessage, 0);
                      }
                    }}
                    ariaLabel="Suggested prompts"
                    items={[
                      {
                        text: "¿Puedes ayudarme a revisar el historial médico de este paciente?",
                        id: "prompt-0"
                      },
                      {
                        text: "¿Qué información necesitas para agendar una cita?",
                        id: "prompt-1"
                      },
                      {
                        text: "Agenda una cita para este paciente",
                        id: "prompt-2"
                      },
                      {
                        text: "¿Este paciente presenta síntomas recurrentes?",
                        id: "prompt-3"
                      }
                    ]}
                  />
                </Box>
              )}

              {/* Prompt Input */}
              <Box padding="l">
                <PromptInput
                  onChange={({ detail }) => setPromptValue(detail.value)}
                  value={promptValue}
                  actionButtonAriaLabel="Send message"
                  actionButtonIconName="send"
                  placeholder="Haz una pregunta, incluye archivos con el botón o arrastrandolos a la ventana"
                  disabled={isLoading}
                  onAction={handleSendMessage}
                  secondaryActions={
                    <Box padding={{ left: "xxs", top: "xs" }}>
                      <FileInput
                        variant="icon"
                        multiple={true}
                        value={files}

                        onChange={({ detail }) => setFiles(detail.value)}
                        accept=".pdf,.tiff,.tif,.jpeg,.jpg,.png,.docx,.txt,.md,.html,.csv,.xlsx,.mp4,.mov,.avi,.mkv,.webm,.amr,.flac,.m4a,.mp3,.ogg,.wav"
                      />
                    </Box>
                  }
                  secondaryContent={
                    files.length > 0 && (
                      <FileTokenGroup
                        items={files.map(file => ({ file }))}
                        onDismiss={({ detail }) =>
                          setFiles(files =>
                            files.filter((_, index) =>
                              index !== detail.fileIndex
                            )
                          )
                        }
                        alignment="horizontal"
                        showFileSize={true}
                        showFileLastModified={true}
                        showFileThumbnail={true}
                        i18nStrings={{
                          removeFileAriaLabel: () => "Remover archivo",
                          limitShowFewer: "Mostrar menos archivos",
                          limitShowMore: "Mostrar más archivos",
                          errorIconAriaLabel: "Error",
                          warningIconAriaLabel: "Warning"
                        }}
                      />
                    )
                  }
                />
              </Box>
            </SpaceBetween>
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

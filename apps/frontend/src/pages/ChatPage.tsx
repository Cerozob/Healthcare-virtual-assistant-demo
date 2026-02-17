import { Avatar, ChatBubble, SupportPromptGroup } from '@cloudscape-design/chat-components';
import {
  Alert,
  Box,
  Button,
  Container,
  FileDropzone,
  FileInput,
  FileTokenGroup,
  Grid,
  Header,
  Icon,
  Modal,
  PromptInput,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useFilesDragging } from '@cloudscape-design/components/file-dropzone';
import { useCallback, useEffect, useRef, useState } from 'react';
import { MarkdownRenderer, PatientChatSidebar } from '../components/chat';
import { DebugPanel } from '../components/debug/DebugPanel';
import { MainLayout } from '../components/layout';
import { PatientSelector } from '../components/patient';
import { useLanguage } from '../contexts/LanguageContext';
import { usePatientContext } from '../contexts/PatientContext';
import { useTheme } from '../contexts/ThemeContext';
import { usePatientSync } from '../hooks/usePatientSync';
import { chatService } from '../services/chatService';
import { reservationService } from '../services/reservationService';

import type { ChatMessage, Patient } from '../types/api';

// File attachment metadata type
interface FileAttachmentMetadata {
  fileName: string;
  fileSize: number;
  fileType: string;
}

// Guardrail intervention types
interface GuardrailViolation {
  type: 'topic_policy' | 'content_policy' | 'pii_entity' | 'pii_regex' | 'grounding_policy';
  topic?: string;
  content_type?: string;
  pii_type?: string;
  pattern?: string;
  grounding_type?: string;
  confidence?: string;
  score?: number;
  threshold?: number;
  action?: string;
  policy_type?: string;
}

interface GuardrailIntervention {
  source: 'INPUT' | 'OUTPUT';
  action: 'GUARDRAIL_INTERVENED' | 'NONE';
  content_preview?: string;
  timestamp?: string;
  violations: GuardrailViolation[];
}

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

    // Load patient reservations if patient is selected
    if (patient) {
      try {
        // TODO: Implement patient-specific reservation filtering in the API
        const reservationsResponse = await reservationService.getReservations();
        // Filter reservations by patient ID on the client side for now
        const patientExams = reservationsResponse.reservations.filter(reservation =>
          reservation.patient_id === patient.patient_id
        );
        setPatientExams(patientExams);
      } catch (error) {
        console.error('Error loading patient reservations:', error);
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
  const { mode } = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<'processing' | 'generating'>('processing');
  const [sessionId, setSessionId] = useState<string>(() => {
    // Always start with a session ID for conversation continuity
    const initialSessionId = `healthcare_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log(`🔒 Initial session started: ${initialSessionId}`);
    return initialSessionId;
  });

  // 🔒 SECURITY: Generate new session ID for patient safety
  const generateNewSession = (reason: string) => {
    const newSessionId = `healthcare_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    // Reset AgentCore session IDs (MCP and Runtime)
    import('../services/agentCoreService').then(({ agentCoreService }) => {
      agentCoreService.resetSessions();
    });
    
    console.log(`🔒 New session started: ${newSessionId} (Reason: ${reason})`);
    return newSessionId;
  };

  // Enhanced patient sync hook
  const { handlePatientContextSync } = usePatientSync({
    onPatientDetected: (patient) => {
      console.log('🎯 Patient detected via sync hook:', patient);
    },
    onPatientChanged: (oldPatient, newPatient) => {
      console.log('🔄 Patient changed via sync hook:', { oldPatient, newPatient });
    },
    onSyncError: (error) => {
      console.error('❌ Patient sync error:', error);
      setError(`Error al sincronizar paciente: ${error.message}`);
    },
    generateNewSession
  });
  const [showPatientSelector, setShowPatientSelector] = useState(false);

  // Chat auto-scroll refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Smooth scroll function for chat container only
  const scrollChatToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      // Scroll only the chat container, not the entire page
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, []);

  // Auto-scroll chat container when messages change
  useEffect(() => {
    const timer = setTimeout(scrollChatToBottom, 100);
    return () => clearTimeout(timer);
  }, [scrollChatToBottom]); // Trigger when messages change

  // Debug state for troubleshooting
  const [debugInfo, setDebugInfo] = useState<{
    lastResponse: unknown;
    lastRequest: unknown;
    patientContext: unknown;
    guardrailInterventions: GuardrailIntervention[];
  }>({
    lastResponse: null,
    lastRequest: null,
    patientContext: null,
    guardrailInterventions: []
  });



  // Prompt input state
  const [promptValue, setPromptValue] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>('');

  // File dragging state
  const { areFilesDragging } = useFilesDragging();

  const defaultPrompts = [
    {
      text: "Hola, Cómo puedes ayudarme?",
      id: "prompt-4"
    }
    ,
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
  ]

  const getUserInitials = () => {
    const name = user?.signInDetails?.loginId
    return name?.charAt(0).toUpperCase();
  };


  const handleSendMessage = async () => {
    if (!promptValue.trim() && files.length === 0) return;



    // Allow files without patient selection - agent will help identify patient
    // This enables the agent to analyze files and ask for patient information if needed

    // Create user message immediately
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      content: promptValue,
      type: 'user',
      timestamp: new Date().toISOString(),
      ...(files.length > 0 && {
        metadata: {
          attachments: files.map(f => ({
            fileName: f.name,
            fileSize: f.size,
            fileType: f.type
          }))
        }
      })
    };

    // Add user message immediately to UI
    setMessages(prev => [...prev, userMessage]);

    // Clear input immediately
    const messageContent = promptValue;
    const attachedFiles = [...files];

    setPromptValue('');
    setFiles([]);

    // Start loading process
    setIsLoading(true);
    setLoadingStage('processing');

    try {
      // Process file uploads - handle both with and without patient context
      if (attachedFiles.length > 0) {
        console.log(`Processing ${attachedFiles.length} files ${selectedPatient ? `for patient ${selectedPatient.full_name}` : 'without patient context'}`);

        // Upload files to S3 using the storage service
        const { storageService } = await import('../services/storageService');
        const { configService } = await import('../services/configService');
        const config = configService.getConfig();

        for (const file of attachedFiles) {
          try {
            // S3 path structure: 
            // With patient: {patient_id}/{filename}
            // Without patient: unassigned/{timestamp}/{filename} (for agent to process and assign)
            const s3Key = selectedPatient
              ? `${selectedPatient.patient_id}/${file.name}`
              : `unassigned/${Date.now()}/${file.name}`;

            // Prepare metadata following document workflow guidelines
            const fileMetadata: { [key: string]: string } = selectedPatient ? {
              'patient-id': selectedPatient.patient_id,
              'workflow-stage': 'uploaded',
              'auto-classification-enabled': 'true',
              'uploaded-from': 'chat-interface'
            } : {
              'workflow-stage': 'pending-patient-assignment',
              'auto-classification-enabled': 'true',
              'uploaded-from': 'chat-interface',
              'requires-patient-identification': 'true'
            };

            console.log(`📋 Document Workflow Metadata:`, fileMetadata);
            console.log(`📍 S3 Path: ${s3Key}`);

            // Upload file to S3 with metadata
            const uploadResult = await storageService.uploadFile(file, s3Key, {
              contentType: file.type,
              bucket: config.s3BucketName,
              metadata: fileMetadata
            });

            console.log(`Successfully uploaded ${file.name}${selectedPatient ? ` for patient ${selectedPatient.full_name}` : ' for patient identification'}:`, uploadResult);
          } catch (uploadError) {
            console.error(`Error uploading ${file.name}:`, uploadError);
            setError(`Error al subir ${file.name}: ${uploadError instanceof Error ? uploadError.message : 'Error desconocido'}`);
          }
        }
      }

      // Build contextual content with patient and document information
      let contextualContent = messageContent;

      // Add patient context if available
      if (selectedPatient) {
        contextualContent = `[Contexto del paciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})]\n\n${contextualContent}`;
      } else {
        // No patient selected - let agent know it needs to help identify patient if files are attached
        if (attachedFiles.length > 0) {
          contextualContent = `[Sin paciente seleccionado - ARCHIVOS ADJUNTOS REQUIEREN IDENTIFICACIÓN DE PACIENTE]\n\n${contextualContent}`;
        } else {
          contextualContent = `[Sin contexto de paciente seleccionado]\n\n${contextualContent}`;
        }
      }

      // Add document context if files are attached
      if (attachedFiles.length > 0) {
        const documentContext = attachedFiles.map(file => {
          const statusText = selectedPatient
            ? 'Subido al flujo de documentos'
            : 'Subido - REQUIERE IDENTIFICACIÓN DE PACIENTE';
          return `- ${file.name} - ${statusText}`;
        }).join('\n');

        const contextHeader = selectedPatient
          ? '[Documentos adjuntos y procesados:'
          : '[Documentos adjuntos - REQUIEREN ASIGNACIÓN DE PACIENTE:';

        contextualContent = `${contextHeader}\n${documentContext}]\n\n${contextualContent}`;
      }

      // Send message using normal messaging
      setLoadingStage('generating');

      // 🔒 Validate session ID before sending
      if (!sessionId || sessionId.length < 10) {
        console.error('❌ Invalid session ID detected:', sessionId);
        setError('Error de sesión: ID de sesión inválido. Recargando página...');
        window.location.reload();
        return;
      }

      console.log(`🔑 Using session ID for request: ${sessionId} (length: ${sessionId.length})`);
      console.log(`🔍 Session ID validation: pattern=${/^healthcare_\d+_[a-z0-9]+$/.test(sessionId)}, length_ok=${sessionId.length >= 33}`);

      const requestData = {
        message: contextualContent,
        sessionId, // Always include consistent session ID
        // Include file information if available
        ...(attachedFiles.length > 0 && {
          attachments: await Promise.all(attachedFiles.map(async (file) => {
            // For images and documents, include base64 content for AgentCore multi-modal support
            let content: string | undefined;
            let mimeType: string | undefined;

            // Supported file types for multi-modal processing
            const supportedTypes = [
              // Images
              'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
              // Documents
              'application/pdf',
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
              'application/msword', // .doc
              'text/plain', // .txt
              'text/markdown', // .md
              'text/csv', // .csv
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
              'application/vnd.ms-excel', // .xls
              'text/html' // .html
            ];

            if (supportedTypes.includes(file.type)) {
              try {
                content = await fileToBase64(file);
                mimeType = file.type;
                console.log(`Converted ${file.name} (${file.type}) to base64 for multi-modal processing`);
              } catch (error) {
                console.warn(`Failed to convert ${file.name} to base64:`, error);
              }
            }

            return {
              fileName: file.name,
              fileSize: file.size,
              fileType: file.type,
              s3Key: selectedPatient
                ? `${selectedPatient.patient_id}/${file.name}`
                : `unassigned/${Date.now()}/${file.name}`,
              content,
              mimeType,
              requiresPatientAssignment: !selectedPatient
            };
          }))
        })
      };

      // Create agent message placeholder for loading state
      const agentMessageId = `agent_${Date.now()}`;
      const agentMessage: ChatMessage = {
        id: agentMessageId,
        content: '',
        type: 'agent',
        agentType: 'processing',
        timestamp: new Date().toISOString()
      };

      // Add agent message to UI immediately (this will show loading state)
      setMessages(prev => [...prev, agentMessage]);

      // Use normal messaging service with loading state handling
      const response = await chatService.sendMessage(
        requestData.message,
        requestData.sessionId,
        requestData.attachments?.map(att => ({
          fileName: att.fileName,
          fileType: att.fileType,
          mimeType: att.mimeType || att.fileType,
          content: att.content,
          s3Key: att.s3Key,
          fileSize: att.fileSize
        })),
        // Loading state callback
        (loadingState) => {
          console.log('📊 Loading state:', loadingState);

          // Update agent message with loading information
          setMessages(prev => prev.map(msg =>
            msg.id === agentMessageId
              ? {
                ...msg,
                content: loadingState.isLoading
                  ? `**Procesando...**`
                  : msg.content,
                agentType: loadingState.isLoading ? 'processing' : 'agentcore'
              }
              : msg
          ));
        }
      );

      console.log('✅ Normal messaging complete:', response);

      // 🔒 CRITICAL: Always maintain frontend session ID consistency
      // The agent may modify session IDs (e.g., adding "_nonrestrictive" for guardrails)
      // but the frontend must maintain its own session ID for conversation continuity
      if (response.sessionId !== sessionId) {
        console.warn(`  Frontend sessionId: "${sessionId}"`);
        console.warn(`  Agent response sessionId: "${response.sessionId}"`);
        console.warn(`  ✅ Maintaining frontend session ID for consistency`);
        
        // Log detailed session ID analysis for debugging
        console.log('🔍 Session ID Analysis:');
        console.log(`   Frontend: "${sessionId}" (${sessionId.length} chars)`);
        console.log(`   Agent: "${response.sessionId}" (${response.sessionId?.length || 0} chars)`);
        console.log(`   Likely cause: AgentCore guardrails or memory system modification`);
        console.log(`   Action: Frontend maintains original session ID`);
      } else {
        console.log(`✅ Session ID consistent: ${sessionId}`);
      }
      
      // IMPORTANT: Always use frontend session ID, never the response session ID
      // This ensures conversation continuity regardless of agent-side modifications

      // Check if response is successful and has content
      const hasContent = response.success && response.content && response.content.trim().length > 0;

      // Update the agent message with final response
      setMessages(prev => prev.map(msg =>
        msg.id === agentMessageId
          ? {
            ...msg,
            content: hasContent
              ? response.content
              : response.errors && response.errors.length > 0
                ? `❌ **Error en la consulta**\n\n${response.errors[0].message}\n\n💡 **¿Qué puedes hacer?**\n• Verifica tu conexión a internet\n• Intenta reformular tu consulta\n• Si el problema persiste, espera unos momentos\n\n*Puedes escribir tu consulta nuevamente para intentar otra vez.*`
                : '⚠️ **Respuesta vacía del agente**\n\nEl agente completó el procesamiento pero no generó una respuesta. Esto puede ocurrir cuando:\n\n• La consulta no pudo ser procesada correctamente\n• Hubo un problema técnico durante la generación\n• El agente se quedó bloqueado en una operación\n\n💡 **Sugerencias:**\n• Intenta reformular tu consulta de manera más específica\n• Verifica que tu consulta esté relacionada con temas médicos\n• Si persiste el problema, espera unos momentos e intenta nuevamente',
            agentType: hasContent ? 'agentcore' : 'error',
            metadata: response.metadata
          }
          : msg
      ));

      // 🔍 DEBUG: Update debug info
      setDebugInfo({
        lastResponse: response,
        lastRequest: requestData,
        patientContext: response.patientContext,
        guardrailInterventions: response.guardrailInterventions || []
      });

      // 👤 ENHANCED: Sync patient context using the enhanced sync hook
      if (response.patientContext) {
        console.log('🔍 Patient context from response:', response.patientContext);

        await handlePatientContextSync(
          response.patientContext,
          (message) => setMessages(prev => [...prev, message]),
          () => setMessages([])
        );
      }

      setIsLoading(false);

      // Patient context handling is now done in the streaming callbacks above

    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Error al enviar mensaje');
      setIsLoading(false);
    }
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  // Helper function to convert file to base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to read file as base64'));
        }
      };
      reader.onerror = (error) => reject(error);
    });
  };



  const handleFileChange = (newFiles: File[]) => {
    setFiles(newFiles);
  };



  const handleChangePatient = () => {
    setShowPatientSelector(true);
  };

  const handleClearPatient = () => {
    const previousPatient = selectedPatient;
    clearPatient();

    // 🔒 SECURITY: Start new session when clearing patient
    generateNewSession('Patient context cleared');
    setMessages([]);

    // Add system message about patient context being cleared
    const systemMessage: ChatMessage = {
      id: `system_${Date.now()}`,
      content: `🔒 **Contexto del paciente eliminado**\n\nPaciente anterior: ${previousPatient?.full_name || 'Desconocido'}\n\n*Se ha iniciado una nueva sesión por seguridad.*`,
      type: 'system',
      timestamp: new Date().toISOString(),
      agentType: 'security'
    };
    setMessages([systemMessage]);
  };

  const handlePatientSelected = () => {
    setShowPatientSelector(false);

    // 🔒 SECURITY: Check if this is a different patient
    if (selectedPatient) {
      const previousPatientId = messages.length > 0 ?
        messages.find(msg => msg.agentType === 'system' && msg.content.includes('ID:'))?.content.match(/ID:\s*([^)]+)/)?.[1] :
        null;

      const isDifferentPatient = previousPatientId && previousPatientId !== selectedPatient.patient_id;

      if (isDifferentPatient) {
        // Start new session for different patient
        generateNewSession('Different patient manually selected');
        setMessages([]);

        const securityMessage: ChatMessage = {
          id: `system_${Date.now()}`,
          content: `🔒 **Nuevo paciente seleccionado**\n\nPaciente: ${selectedPatient.full_name} (ID: ${selectedPatient.patient_id})\n\n*Se ha iniciado una nueva sesión por seguridad.*`,
          type: 'system',
          timestamp: new Date().toISOString(),
          agentType: 'security'
        };
        setMessages([securityMessage]);
      } else {
        // Same patient or first selection
        const systemMessage: ChatMessage = {
          id: `system_${Date.now()}`,
          content: `🎯 Contexto del paciente actualizado: **${selectedPatient.full_name}** (ID: ${selectedPatient.patient_id})`,
          type: 'system',
          timestamp: new Date().toISOString(),
          agentType: 'system'
        };
        setMessages(prev => [...prev, systemMessage]);
      }
    }
  };

  return (
    <MainLayout signOut={signOut} user={user}>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          description={selectedPatient ? `Sesión segura activa - Paciente: ${selectedPatient.full_name}` : "Bienvenido"}
          actions={
            selectedPatient && sessionId && (
              <Box fontSize="body-s" color="text-status-success">
                <Icon name="security" /> Sesión ID: {sessionId.split('_')[1] || sessionId}
              </Box>
            )
          }
        >
          {t.chat.title}
        </Header>



        <Grid gridDefinition={[{ colspan: { default: 12, s: 8 } }, { colspan: { default: 12, s: 4 } }]}>
          {/* Chat Area */}
          <Container>
            <SpaceBetween size="l">
              {error && (
                <Alert type="error" dismissible onDismiss={() => setError('')}>
                  {error}
                </Alert>
              )}
              {/* Chat Messages */}

              <div
                ref={chatContainerRef}
                className={`chat-messages-container theme-transition`}
                data-theme={mode}
              >
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
                        ariaLabel={"User avatar"}
                        initials={getUserInitials()}
                      />
                    ) : (
                      <Avatar
                        ariaLabel="Generative AI assistant"
                        color="gen-ai"
                        iconName="gen-ai"
                        tooltipText="Generative AI assistant"
                        loading={message.agentType === 'processing'}
                      />
                    );

                    const actions = isAgent ? (
                      <Button
                        variant="icon"
                        iconName="copy"
                        onClick={() => handleCopy(message.content)}
                        ariaLabel="Copy message"
                        disabled={message.agentType === 'agentcore-streaming' || message.agentType === 'agentcore-processing'}
                      />
                    ) : undefined;

                    return (
                      <div
                        key={message.id}
                        className={`chat-bubble-wrapper ${isUser ? 'outgoing' : 'incoming'}`}
                      >
                        <ChatBubble
                          ariaLabel={`${isUser ? "User" : 'Generative AI assistant'} at ${formatTime(message.timestamp)}`}
                          type={isUser ? "outgoing" : "incoming"}
                          avatar={avatar}
                          actions={actions}
                          showLoadingBar={message.agentType === 'processing'}
                        >
                          {message.agentType === 'processing' && !message.content ? (
                            <Box color="text-status-inactive">
                              Procesando consulta...
                            </Box>
                          ) : (
                            <>
                              <MarkdownRenderer content={message.content} />
                              {isUser && message.metadata?.attachments && Array.isArray(message.metadata.attachments) && message.metadata.attachments.length > 0 && (
                                <Box margin={{ top: 'xs' }} fontSize="body-s" color="text-body-secondary">
                                  <SpaceBetween size="xxs" direction="horizontal">
                                    <Icon name="file" />
                                    <span>
                                      {message.metadata.attachments.length} {message.metadata.attachments.length === 1 ? 'archivo adjunto' : 'archivos adjuntos'}
                                      {message.metadata.attachments.length <= 3 && (
                                        <>: {(message.metadata.attachments as FileAttachmentMetadata[]).map(att => att.fileName).join(', ')}</>
                                      )}
                                    </span>
                                  </SpaceBetween>
                                </Box>
                              )}
                            </>
                          )}
                        </ChatBubble>
                      </div>
                    );
                  })
                )}

                {/* Loading State - Only show when no processing message exists */}
                {isLoading && !messages.some(msg => msg.agentType === 'processing') && (
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
                        {loadingStage === 'processing' ? 'Analizando solicitud' : 'Procesando consulta...'}
                      </Box>
                    </ChatBubble>
                  </div>
                )}

                {/* Auto-scroll target */}
                <div ref={messagesEndRef} />
              </div>


              {/* Support Prompts */}
              {!isLoading && messages.length === 0 && (

                <SupportPromptGroup
                  onItemClick={({ detail }) => {
                    const selectedPrompt = defaultPrompts.find(prompt => prompt.id === detail.id);

                    if (selectedPrompt) {
                      setPromptValue(selectedPrompt.text);
                      setTimeout(handleSendMessage, 0);
                    }
                  }}
                  ariaLabel="Suggested prompts"
                  items={defaultPrompts}
                />

              )}

              {/* Prompt Input with File Upload */}

              <PromptInput
                onChange={({ detail }) => setPromptValue(detail.value)}
                value={promptValue}
                actionButtonAriaLabel="Send message"
                actionButtonIconName="send"
                disableSecondaryActionsPaddings
                placeholder={selectedPatient
                  ? `Haz una pregunta sobre ${selectedPatient.full_name}`
                  : "Haz una pregunta o adjunta archivos para identificar al paciente"
                }
                disabled={isLoading}
                onAction={handleSendMessage}
                secondaryActions={
                  <Box padding={{ left: "xxs", top: "xs" }}>
                    <FileInput
                      variant="icon"
                      multiple={true}
                      value={files}
                      onChange={({ detail }) => handleFileChange(detail.value)}
                      accept=".pdf,.tiff,.tif,.jpeg,.jpg,.png,.docx,.txt,.md,.html,.csv,.xlsx,.mp4,.mov,.avi,.mkv,.webm,.amr,.flac,.m4a,.mp3,.ogg,.wav"
                    />
                  </Box>
                }
                secondaryContent={
                  areFilesDragging ? (
                    <FileDropzone
                      onChange={({ detail }) => {
                        handleFileChange([...files, ...detail.value]);
                      }}
                    >
                      <SpaceBetween size="xs" alignItems="center">
                        <Icon name="upload" />
                        <Box>
                          {selectedPatient
                            ? `Suelta los archivos aquí para ${selectedPatient.full_name}`
                            : "Suelta los archivos aquí - el asistente te ayudará a identificar al paciente"
                          }
                        </Box>
                      </SpaceBetween>
                    </FileDropzone>
                  ) : (
                    files.length > 0 && (
                      <SpaceBetween size="s">
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
                            removeFileAriaLabel: () => "Eliminar archivo",
                            limitShowFewer: "Mostrar menos archivos",
                            limitShowMore: "Mostrar más archivos",
                            errorIconAriaLabel: "Error",
                            warningIconAriaLabel: "Advertencia"
                          }}
                        />


                      </SpaceBetween>
                    )
                  )
                }
              />


            </SpaceBetween>
          </Container>

          {/* Patient Sidebar */}
          <PatientChatSidebar
            patient={selectedPatient}
            onChangePatient={handleChangePatient}
            onClearPatient={isPatientSelected ? handleClearPatient : undefined}
          />
        </Grid>

        {/* Debug Panel */}
        <DebugPanel
          lastResponse={debugInfo.lastResponse}
          lastRequest={debugInfo.lastRequest}
          patientContext={debugInfo.patientContext}
          selectedPatient={selectedPatient || undefined}
          sessionId={sessionId}
          messages={messages}
          guardrailInterventions={debugInfo.guardrailInterventions}
        />
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

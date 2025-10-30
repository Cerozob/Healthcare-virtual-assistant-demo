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
import { useEffect, useRef, useState } from 'react';
import { MarkdownRenderer, PatientChatSidebar } from '../components/chat';
import { DebugPanel } from '../components/debug/DebugPanel';
import { MainLayout } from '../components/layout';
import { PatientSelector } from '../components/patient';
import { useLanguage } from '../contexts/LanguageContext';
import { usePatientContext } from '../contexts/PatientContext';
import { useTheme } from '../contexts/ThemeContext';
import { chatService } from '../services/chatService';
import { reservationService } from '../services/reservationService';
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
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [showPatientSelector, setShowPatientSelector] = useState(false);

  // Chat auto-scroll ref with callback
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when messages change
  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };

    const timer = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timer);
  });

  // Debug state for troubleshooting
  const [debugInfo, setDebugInfo] = useState<{
    lastResponse: unknown;
    lastRequest: unknown;
    patientContext: unknown;
  }>({
    lastResponse: null,
    lastRequest: null,
    patientContext: null
  });

  // Prompt input state
  const [promptValue, setPromptValue] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [fileClassifications, setFileClassifications] = useState<Map<string, {
    category: string;
    confidence?: number;
    autoClassified?: boolean;
    processing?: boolean;
  }>>(new Map());
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

    // Check if patient is selected when files are attached
    if (files.length > 0 && !selectedPatient) {
      setError('Por favor seleccione un paciente antes de adjuntar archivos. Los documentos necesitan estar asociados a un paciente específico.');
      return;
    }

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
    const attachedFiles = [...files];
    const attachedClassifications = new Map(fileClassifications);

    setPromptValue('');
    setFiles([]);
    setFileClassifications(new Map());

    // Start loading process
    setIsLoading(true);
    setLoadingStage('processing');

    try {
      // Process file uploads if patient is selected
      if (attachedFiles.length > 0 && selectedPatient) {
        console.log(`Processing ${attachedFiles.length} files for patient ${selectedPatient.full_name} following document workflow guidelines`);

        // Upload files to S3 using the storage service
        const { storageService } = await import('../services/storageService');
        const { configService } = await import('../services/configService');
        const config = configService.getConfig();

        for (const file of attachedFiles) {
          const fileKey = getFileKey(file);
          const classification = attachedClassifications.get(fileKey);

          try {
            const category = classification?.category || 'auto';

            // S3 path structure: {patient_id}/{filename} (simple structure for BDA processing)
            const s3Key = `${selectedPatient.patient_id}/${file.name}`;

            // Prepare metadata following document workflow guidelines
            const fileMetadata = {
              'patient-id': selectedPatient.patient_id,
              'document-category': category,
              'workflow-stage': 'uploaded',
              'auto-classification-enabled': 'true',
              'uploaded-from': 'chat-interface'
            };

            console.log(`📋 Document Workflow Metadata:`, fileMetadata);
            console.log(`📍 S3 Path: ${s3Key}`);

            // Upload file to S3 with metadata
            const uploadResult = await storageService.uploadFile(file, s3Key, {
              contentType: file.type,
              bucket: config.s3BucketName,
              metadata: fileMetadata
            });

            const response = {
              patient_id: selectedPatient.patient_id,
              s3_key: uploadResult.key,
              message: `File uploaded successfully for patient ${selectedPatient.full_name} following document workflow guidelines`,
              category: category,
              workflow_info: {
                next_stage: 'BDA processing and classification',
                expected_processing_time: '2-5 minutes'
              }
            };

            console.log(`Successfully uploaded ${file.name} for patient ${selectedPatient.full_name}:`, response);
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
      } else if (attachedFiles.length === 0) {
        // No patient selected and no files - this is a noop as requested
        contextualContent = `[Sin contexto de paciente seleccionado]\n\n${contextualContent}`;
      }

      // Add document classification context if files are attached
      if (attachedFiles.length > 0) {
        const documentContext = attachedFiles.map(file => {
          const fileKey = getFileKey(file);
          const classification = attachedClassifications.get(fileKey);

          if (classification && !classification.processing) {
            return `- ${file.name}: ${getCategoryLabel(classification.category)}${classification.autoClassified && classification.confidence
              ? ` (${classification.confidence.toFixed(0)}% confianza)`
              : ''
              } - Subido al flujo de documentos`;
          }
          return `- ${file.name}: Procesando clasificación...`;
        }).join('\n');

        contextualContent = `[Documentos adjuntos y procesados:\n${documentContext}]\n\n${contextualContent}`;
      }

      // Send message to AgentCore
      setLoadingStage('generating');

      const requestData = {
        message: contextualContent,
        ...(sessionId && { sessionId }),
        // Include file information if available
        ...(attachedFiles.length > 0 && {
          attachments: await Promise.all(attachedFiles.map(async (file) => {
            const fileKey = getFileKey(file);
            const classification = attachedClassifications.get(fileKey);

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
              category: classification?.category || 'other',
              s3Key: `${selectedPatient?.patient_id}/${classification?.category || 'other'}/${new Date().toISOString().replace(/[:.]/g, '-')}/${file.name}`,
              content,
              mimeType
            };
          }))
        })
      };

      // Create streaming agent message placeholder
      const streamingMessageId = `agent_${Date.now()}`;
      const streamingMessage: ChatMessage = {
        id: streamingMessageId,
        content: '',
        type: 'agent',
        agentType: 'agentcore-streaming',
        timestamp: new Date().toISOString()
      };

      // Add streaming message to UI
      setMessages(prev => [...prev, streamingMessage]);

      // Use streaming service
      await chatService.sendStreamingMessage(
        requestData,
        // onChunk callback - update the streaming message
        (chunk) => {
          console.log('📥 Streaming chunk:', chunk);
          setMessages(prev => prev.map(msg =>
            msg.id === streamingMessageId
              ? { ...msg, content: chunk.content }
              : msg
          ));
        },
        // onComplete callback - finalize the message
        (finalResponse) => {
          console.log('✅ Streaming complete:', finalResponse);

          // Update session ID
          if (finalResponse.sessionId && finalResponse.sessionId !== sessionId) {
            setSessionId(finalResponse.sessionId);
            console.log(`Using session ID from AgentCore: ${finalResponse.sessionId}`);
          }

          // Finalize the streaming message
          setMessages(prev => prev.map(msg =>
            msg.id === streamingMessageId
              ? {
                ...msg,
                content: finalResponse.content,
                agentType: 'agentcore',
                metadata: finalResponse.metadata
              }
              : msg
          ));

          // 🔍 DEBUG: Update debug info
          setDebugInfo({
            lastResponse: finalResponse,
            lastRequest: requestData,
            patientContext: finalResponse.metadata?.patientContext
          });

          setIsLoading(false);
        },
        // onError callback
        (error) => {
          console.error('❌ Streaming error:', error);

          // Update the streaming message with error
          setMessages(prev => prev.map(msg =>
            msg.id === streamingMessageId
              ? {
                ...msg,
                content: `Error: ${error.message}`,
                agentType: 'error'
              }
              : msg
          ));

          setError(error.message);
          setIsLoading(false);
        }
      );

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

  // Simulate auto-classification for uploaded files following document workflow guidelines
  const simulateAutoClassification = async (file: File): Promise<{
    category: string;
    confidence: number;
    autoClassified: boolean;
  }> => {
    // Simulate processing delay to mimic BDA processing
    await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 2500));

    // Enhanced classification logic based on document workflow guidelines
    const fileName = file.name.toLowerCase();
    const fileType = file.type.toLowerCase();
    const fileExtension = fileName.split('.').pop() || '';

    let category = 'other';
    let confidence = 60 + Math.random() * 35; // Random confidence between 60-95%

    // Medical history documents
    if (fileName.includes('historia') || fileName.includes('historial') || fileName.includes('medical') ||
      fileName.includes('clinica') || fileName.includes('expediente')) {
      category = 'medical-history';
      confidence = 82 + Math.random() * 15;
    }
    // Exam results and lab reports
    else if (fileName.includes('examen') || fileName.includes('resultado') || fileName.includes('lab') ||
      fileName.includes('test') || fileName.includes('analisis') || fileName.includes('reporte')) {
      category = 'exam-results';
      confidence = 87 + Math.random() * 10;
    }
    // Medical images
    else if (fileType.includes('image') || fileName.includes('radiografia') || fileName.includes('ecografia') ||
      fileName.includes('tomografia') || fileName.includes('resonancia') || fileName.includes('rx') ||
      ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'dcm'].includes(fileExtension)) {
      category = 'medical-images';
      confidence = 91 + Math.random() * 8;
    }
    // Identification documents
    else if (fileName.includes('cedula') || fileName.includes('dni') || fileName.includes('id') ||
      fileName.includes('identidad') || fileName.includes('pasaporte') || fileName.includes('licencia')) {
      category = 'identification';
      confidence = 94 + Math.random() * 5;
    }
    // PDF documents might be various types
    else if (fileType.includes('pdf')) {
      // PDFs could be any category, lower confidence
      const categories = ['medical-history', 'exam-results', 'other'];
      category = categories[Math.floor(Math.random() * categories.length)];
      confidence = 65 + Math.random() * 20;
    }

    // Apply confidence threshold (80%) as per document workflow guidelines
    if (confidence < 80) {
      category = 'not-identified';
      console.log(`Document ${fileName} classified as 'not-identified' due to low confidence (${confidence.toFixed(1)}%)`);
    } else {
      console.log(`Document ${fileName} auto-classified as '${category}' with ${confidence.toFixed(1)}% confidence`);
    }

    return {
      category,
      confidence: Math.min(confidence, 100),
      autoClassified: true
    };
  };

  const handleFileChange = async (newFiles: File[]) => {
    setFiles(newFiles);

    // Process classification for new files
    const newClassifications = new Map(fileClassifications);

    for (const file of newFiles) {
      const fileKey = `${file.name}_${file.size}_${file.lastModified}`;

      if (!newClassifications.has(fileKey)) {
        // Mark as processing
        newClassifications.set(fileKey, {
          category: 'other',
          processing: true
        });
        setFileClassifications(new Map(newClassifications));

        try {
          const classification = await simulateAutoClassification(file);
          newClassifications.set(fileKey, classification);
          setFileClassifications(new Map(newClassifications));
        } catch (error) {
          console.error('Classification failed:', error);
          newClassifications.set(fileKey, {
            category: 'not-identified',
            confidence: 0,
            autoClassified: false
          });
          setFileClassifications(new Map(newClassifications));
        }
      }
    }
  };

  const getFileKey = (file: File) => `${file.name}_${file.size}_${file.lastModified}`;

  const getCategoryLabel = (category: string): string => {
    const labels: Record<string, string> = {
      'auto': 'Clasificación automática',
      'medical-history': 'Historia clínica',
      'exam-results': 'Resultados de exámenes',
      'medical-images': 'Imágenes médicas',
      'identification': 'Documentos de identidad',
      'other': 'Otros',
      'not-identified': 'No identificado'
    };
    return labels[category] || 'Sin categoría';
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
        content: `Contexto del paciente actualizado: ${String(selectedPatient.full_name)} (ID: ${String(selectedPatient.patient_id)})`,
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
          description={"Bienvenido"}
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
                          loading={message.agentType === 'agentcore-streaming' && !message.content}
                        />
                      );

                      const actions = isAgent ? (
                        <Button
                          variant="icon"
                          iconName="copy"
                          onClick={() => handleCopy(message.content)}
                          ariaLabel="Copy message"
                          disabled={message.agentType === 'agentcore-streaming' && !message.content}
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
                            showLoadingBar={message.agentType === 'agentcore-streaming' && !message.content}
                          >
                            {message.agentType === 'agentcore-streaming' && !message.content ? (
                              <Box color="text-status-inactive">
                                Conectando con AgentCore...
                              </Box>
                            ) : (
                              <MarkdownRenderer content={message.content} />
                            )}
                          </ChatBubble>
                        </div>
                      );
                    })
                  )}

                  {/* Loading State - Only show when no streaming message exists */}
                  {isLoading && !messages.some(msg => msg.agentType === 'agentcore-streaming') && (
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
                          {loadingStage === 'processing' ? 'Analizando solicitud' : 'Conectando con AgentCore...'}
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
                    : "Selecciona un paciente y haz una pregunta"
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
                          if (!selectedPatient) {
                            setError('Por favor seleccione un paciente antes de adjuntar archivos. Los documentos necesitan estar asociados a un paciente específico.');
                            return;
                          }
                          handleFileChange([...files, ...detail.value]);
                        }}
                      >
                        <SpaceBetween size="xs" alignItems="center">
                          <Icon name="upload" />
                          <Box>
                            {selectedPatient 
                              ? `Suelta los archivos aquí para ${selectedPatient.full_name}`
                              : "Selecciona un paciente primero para adjuntar archivos"
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

                          {/* Classification Information */}
                          <Box>
                            <SpaceBetween size="xs">
                              {files.map((file) => {
                                const fileKey = getFileKey(file);
                                const classification = fileClassifications.get(fileKey);

                                if (!classification) return null;

                                return (
                                  <Box key={fileKey} fontSize="body-s" color="text-body-secondary">
                                    <strong>{file.name}:</strong>{' '}
                                    {classification.processing ? (
                                      <span>Clasificando...</span>
                                    ) : (
                                      <span>
                                        {getCategoryLabel(classification.category)}
                                        {classification.autoClassified && classification.confidence && (
                                          <span> ({classification.confidence.toFixed(0)}% confianza)</span>
                                        )}
                                        {classification.category === 'not-identified' && (
                                          <span style={{ color: '#d91515' }}> - Requiere clasificación manual</span>
                                        )}
                                      </span>
                                    )}
                                  </Box>
                                );
                              })}
                            </SpaceBetween>
                          </Box>
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
          selectedPatient={selectedPatient}
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

/**
 * Panel de Depuración
 * Muestra información de depuración para respuestas del chat, contexto del paciente y eventos de streaming
 */

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Container,
  ExpandableSection,
  Header,
  SpaceBetween,
  Tabs,
  StatusIndicator
} from '@cloudscape-design/components';
import { CodeView } from '@cloudscape-design/code-view';
import { safeStringify, createDebugObject } from '../../utils/debugUtils';

interface DebugPanelProps {
  lastResponse?: unknown;
  lastRequest?: unknown;
  patientContext?: unknown;
  selectedPatient?: any;
  sessionId?: string;
  messages?: Array<{ content: string; type: string; timestamp: string; agentType?: string }>;
}

export function DebugPanel({
  lastResponse,
  lastRequest,
  patientContext,
  selectedPatient,
  sessionId,
  messages = []
}: DebugPanelProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('chat-history');

  if (!isVisible) {
    return (
      <Box margin={{ top: 's' }}>
        <Button
          variant="link"
          iconName="bug"
          onClick={() => setIsVisible(true)}
        >
          Mostrar Panel de Depuración
        </Button>
      </Box>
    );
  }

  // Session validation
  const sessionStatus = sessionId ? 'success' : 'error';

  // Get raw chat history
  const rawChatHistory = messages.map(msg => ({
    timestamp: msg.timestamp,
    type: msg.type,
    agentType: msg.agentType || 'none',
    content: msg.content.substring(0, 200) + (msg.content.length > 200 ? '...' : ''),
    contentLength: msg.content.length
  }));

  const tabs = [
    {
      id: 'chat-history',
      label: 'Historial del Chat',
      content: (
        <Container>
          <SpaceBetween size="m">
            <Alert type="info">
              Historial completo del chat con respuestas sin procesar.
            </Alert>

            <ExpandableSection headerText="Historial de Mensajes" defaultExpanded>
              <CodeView
                content={JSON.stringify(rawChatHistory, null, 2)}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Última Respuesta Completa">
              <CodeView
                content={safeStringify(createDebugObject(lastResponse))}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Última Solicitud">
              <CodeView
                content={safeStringify(createDebugObject(lastRequest))}
                lineNumbers
              />
            </ExpandableSection>
          </SpaceBetween>
        </Container>
      )
    },
    {
      id: 'patient-state',
      label: 'Estado del Paciente',
      content: (
        <Container>
          <SpaceBetween size="m">
            <Alert type="info">
              Información del estado actual del paciente seleccionado y contexto extraído.
            </Alert>

            <ExpandableSection headerText="Paciente Seleccionado" defaultExpanded>
              <CodeView
                content={JSON.stringify(selectedPatient || {}, null, 2)}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Contexto del Paciente desde Respuesta">
              <CodeView
                content={JSON.stringify(patientContext, null, 2)}
                lineNumbers
              />
            </ExpandableSection>

            {selectedPatient && (
              <ExpandableSection headerText="Resumen de Datos del Paciente">
                <CodeView
                  content={JSON.stringify({
                    patient_id: selectedPatient?.patient_id,
                    full_name: selectedPatient?.full_name,
                    cedula: selectedPatient?.cedula,
                    phone: selectedPatient?.phone,
                    email: selectedPatient?.email
                  }, null, 2)}
                  lineNumbers
                />
              </ExpandableSection>
            )}
          </SpaceBetween>
        </Container>
      )
    },
    {
      id: 'session',
      label: 'Detalles de Sesión',
      content: (
        <Container>
          <SpaceBetween size="m">
            <Alert type="info">
              Información de la sesión actual para depuración.
            </Alert>

            <ExpandableSection headerText="Información de Sesión" defaultExpanded>
              <div style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                <div><strong>ID de Sesión:</strong> {sessionId || 'No disponible'}</div>
                <div><strong>Longitud:</strong> {sessionId?.length || 0} caracteres</div>
                <div><strong>Estado:</strong> {sessionId ? 'Válido' : 'No válido'}</div>
                <div><strong>Última Actualización:</strong> {new Date().toLocaleTimeString()}</div>
              </div>
            </ExpandableSection>
          </SpaceBetween>
        </Container>
      )
    },
    {
      id: 'guardrails',
      label: 'GuardRails',
      content: (
        <Container>
          <SpaceBetween size="m">
            <Alert type="warning">
              Panel de GuardRails - TODO: Implementar cuando se conozca el formato de respuesta de AgentCore.
            </Alert>

            <Box>
              <Box variant="h4">Información de GuardRails</Box>
              <Box color="text-body-secondary">
                Este panel mostrará información sobre las detecciones de guardrails cuando esté implementado:
              </Box>
              <ul>
                <li>Detecciones de contenido sensible</li>
                <li>Filtros de seguridad aplicados</li>
                <li>Alertas de cumplimiento</li>
                <li>Logs de moderación de contenido</li>
              </ul>
            </Box>

            <ExpandableSection headerText="Estructura Esperada (Placeholder)">
              <CodeView
                content={JSON.stringify({
                  guardrails: {
                    detected: false,
                    filters_applied: [],
                    content_warnings: [],
                    compliance_status: "compliant"
                  }
                }, null, 2)}
                lineNumbers
              />
            </ExpandableSection>
          </SpaceBetween>
        </Container>
      )
    }
  ];

  return (
    <Container
      header={
        <Header
          variant="h3"
          actions={
            <Button
              variant="icon"
              iconName="close"
              onClick={() => setIsVisible(false)}
            />
          }
        >
          Panel de Depuración
        </Header>
      }
    >
      <SpaceBetween size="m">
        <StatusIndicator type={sessionStatus}>
          ID de Sesión: {sessionId}
        </StatusIndicator>
        <Tabs
          activeTabId={activeTab}
          onChange={({ detail }) => setActiveTab(detail.activeTabId)}
          tabs={tabs}
        />
      </SpaceBetween>
    </Container>
  );
}



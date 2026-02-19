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
  StatusIndicator,
  Table,
  Badge
} from '@cloudscape-design/components';
import { CodeView } from '@cloudscape-design/code-view';
import { safeStringify, createDebugObject } from '../../utils/debugUtils';

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

interface DebugPanelProps {
  lastResponse?: unknown;
  lastRequest?: unknown;
  patientContext?: unknown;
  selectedPatient?: {
    patient_id?: string;
    full_name?: string;
    cedula?: string;
    phone?: string;
    email?: string;
  };
  sessionId?: string;
  messages?: Array<{ content: string; type: string; timestamp: string; agentType?: string }>;
  guardrailInterventions?: GuardrailIntervention[];
}

export function DebugPanel({
  lastResponse,
  lastRequest,
  patientContext,
  selectedPatient,
  sessionId,
  messages = [],
  guardrailInterventions = []
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
                content={JSON.stringify(rawChatHistory, null, 2) || '[]'}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Última Respuesta Completa">
              <CodeView
                content={safeStringify(createDebugObject(lastResponse)) || '{}'}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Última Solicitud">
              <CodeView
                content={safeStringify(createDebugObject(lastRequest)) || '{}'}
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
                content={JSON.stringify(selectedPatient || {}, null, 2) || '{}'}
                lineNumbers
              />
            </ExpandableSection>

            <ExpandableSection headerText="Contexto del Paciente desde Respuesta">
              <CodeView
                content={JSON.stringify(patientContext || {}, null, 2) || '{}'}
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
            {guardrailInterventions.length === 0 ? (
              <Alert type="success">
                ✅ No se detectaron violaciones de guardrails en esta conversación.
              </Alert>
            ) : (
              
                  <SpaceBetween size="xxs" direction="horizontal">
                    <Box>
                      <Badge color="red">
                        {guardrailInterventions.reduce((sum, i) => sum + (i.action === 'GUARDRAIL_INTERVENED' ? i.violations.length : 0), 0)} Violaciones Bloqueadas
                      </Badge>
                    </Box>
                    <Box>
                      <Badge color="blue">
                        {guardrailInterventions.reduce((sum, i) => sum + (i.action === 'NONE' ? i.violations.length : 0), 0)} Violaciones Detectadas
                      </Badge>
                    </Box>
                    <Box>
                      <Badge color="grey">
                        {guardrailInterventions.reduce((sum, i) => sum + i.violations.length, 0)} Total
                      </Badge>
                    </Box>
                  </SpaceBetween>
                
            )}

            {guardrailInterventions.length > 0 && (() => {
              // Flatten violations into separate table rows
              const flattenedViolations = guardrailInterventions.flatMap((intervention) =>
                intervention.violations.map((violation) => ({
                  timestamp: intervention.timestamp,
                  source: intervention.source,
                  interventionAction: intervention.action,
                  content_preview: intervention.content_preview,
                  violation
                }))
              );

              return (
                <Table
                  columnDefinitions={[
                    {
                      id: 'source',
                      header: 'Fuente',
                      cell: (item) => (
                        <Badge color={item.source === 'INPUT' ? 'blue' : 'grey'}>
                          {item.source === 'INPUT' ? 'Usuario' : 'Agente'}
                        </Badge>
                      ),
                      width: 100,
                      minWidth: 100
                    },
                    {
                      id: 'interventionAction',
                      header: 'Intervención',
                      cell: (item) => (
                        <Badge color={item.interventionAction === 'GUARDRAIL_INTERVENED' ? 'red' : 'blue'}>
                          {item.interventionAction === 'GUARDRAIL_INTERVENED' ? 'Bloqueada' : 'Detectada'}
                        </Badge>
                      ),
                      width: 120,
                      minWidth: 120
                    },
                    {
                      id: 'violationType',
                      header: 'Tipo',
                      cell: (item) => {
                        const v = item.violation;
                        
                    
                        return (
                          <Box>
                            {v.type}
                          </Box>
                        );
                      },
                      width: 150,
                      minWidth: 150
                    },
                    {
                      id: 'violationDetails',
                      header: 'Detalle',
                      cell: (item) => {
                        const v = item.violation;
                        let detail = '';
                        
                        if (v.topic) detail = v.topic;
                        else if (v.content_type) detail = v.content_type;
                        else if (v.pii_type) detail = v.pii_type;
                        else if (v.pattern) detail = v.pattern;
                        else if (v.grounding_type) detail = v.grounding_type;
                        
                        return detail || '-';
                      }
                    },
                    {
                      id: 'violationAction',
                      header: 'Acción',
                      cell: (item) => {
                        const action = item.violation.action;
                        if (!action) return '-';
                        
                        return (
                          <Badge color={action === 'ANONYMIZED' ? 'green' : action === 'BLOCK' ? 'red' : 'grey'}>
                            {action}
                          </Badge>
                        );
                      },
                      width: 120,
                      minWidth: 120
                    },
                    {
                      id: 'metrics',
                      header: 'Métricas',
                      cell: (item) => {
                        const v = item.violation;
                        const metrics = [];
                        
                        if (v.confidence) metrics.push(`Conf: ${v.confidence}`);
                        if (v.score !== undefined) metrics.push(`Score: ${v.score.toFixed(2)}`);
                        if (v.threshold !== undefined) metrics.push(`Umbral: ${v.threshold.toFixed(2)}`);
                        
                        return metrics.length > 0 ? (
                          <Box fontSize="body-s" color="text-body-secondary">
                            {metrics.join(' | ')}
                          </Box>
                        ) : '-';
                      }
                    }
                  ]}
                  items={flattenedViolations}
                  loadingText="Cargando detecciones..."
                  empty={
                    <Box textAlign="center" color="inherit">
                      <b>No hay detecciones</b>
                      <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                        No se encontraron violaciones de guardrails.
                      </Box>
                    </Box>
                  }
                  variant="embedded"
                />
              );
            })()}

            {guardrailInterventions.length > 0 && (
              <ExpandableSection headerText="Datos Completos de Detecciones (JSON)">
                <CodeView
                  content={JSON.stringify(guardrailInterventions, null, 2) || '[]'}
                  lineNumbers
                />
              </ExpandableSection>
            )}
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



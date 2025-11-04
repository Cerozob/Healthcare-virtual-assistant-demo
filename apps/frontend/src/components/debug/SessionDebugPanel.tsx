/**
 * Session Debug Panel
 * Real-time monitoring of session ID consistency and memory state
 * Note: This component is now integrated into the main DebugPanel
 */

import { Box, ExpandableSection, SpaceBetween, StatusIndicator } from '@cloudscape-design/components';
import { useEffect, useState } from 'react';

interface SessionDebugInfo {
  currentSessionId: string;
  sessionLength: number;
  messageCount: number;
  lastMessageTime: string;
  sessionConsistent: boolean;
  lastResponse?: string;
  sessionHistory: string[];
}

interface SessionDebugPanelProps {
  sessionId: string;
  messageCount: number;
  lastResponse?: string;
}

export function SessionDebugPanel({
  sessionId,
  messageCount,
  lastResponse
}: SessionDebugPanelProps) {
  const [debugInfo, setDebugInfo] = useState<SessionDebugInfo>({
    currentSessionId: sessionId,
    sessionLength: sessionId.length,
    messageCount: 0,
    lastMessageTime: new Date().toISOString(),
    sessionConsistent: true,
    sessionHistory: []
  });

  // Update debug info when props change
  useEffect(() => {
    const now = new Date().toISOString();

    // Check if session ID changed (consistency issue)
    const sessionChanged = debugInfo.currentSessionId !== sessionId;
    if (sessionChanged) {
      console.warn('🚨 Session ID changed!', {
        old: debugInfo.currentSessionId,
        new: sessionId
      });
    }

    setDebugInfo(prev => ({
      ...prev,
      currentSessionId: sessionId,
      sessionLength: sessionId.length,
      messageCount,
      lastMessageTime: now,
      sessionConsistent: prev.sessionConsistent && !sessionChanged,
      lastResponse: lastResponse?.substring(0, 100),
      sessionHistory: sessionChanged ? [...prev.sessionHistory, prev.currentSessionId].slice(-5) : prev.sessionHistory
    }));
  }, [sessionId, messageCount, lastResponse]);

  // Check if session ID meets AgentCore requirements
  const meetsAgentCoreReqs = debugInfo.sessionLength >= 33;
  const sessionStatus = debugInfo.sessionConsistent ? 'success' : 'error';

  return (
    <ExpandableSection headerText="🔍 Panel de Depuración de Sesión" variant="footer">
      <SpaceBetween size="m">

        {/* Session Status */}
        <Box>
          <h4>Estado de la Sesión</h4>
          <SpaceBetween size="s">
            <div>
              <StatusIndicator type={sessionStatus}>
                Consistencia de Sesión: {debugInfo.sessionConsistent ? 'OK' : 'ROTA'}
              </StatusIndicator>
            </div>
            <div>
              <StatusIndicator type={meetsAgentCoreReqs ? 'success' : 'error'}>
                Requisitos AgentCore: {meetsAgentCoreReqs ? 'Cumplidos' : 'No cumplidos'} ({debugInfo.sessionLength} caracteres)
              </StatusIndicator>
            </div>
          </SpaceBetween>
        </Box>

        {/* Session Details */}
        <Box>
          <h4>Detalles de la Sesión</h4>
          <div style={{ fontFamily: 'monospace', fontSize: '12px' }}>
            <div><strong>ID Actual:</strong> {debugInfo.currentSessionId}</div>
            <div><strong>Longitud:</strong> {debugInfo.sessionLength} caracteres</div>
            <div><strong>Mensajes:</strong> {debugInfo.messageCount}</div>
            <div><strong>Última Actualización:</strong> {new Date(debugInfo.lastMessageTime).toLocaleTimeString()}</div>
          </div>
        </Box>

        {/* Session History */}
        {debugInfo.sessionHistory.length > 0 && (
          <Box>
            <h4>⚠️ Cambios de ID de Sesión Detectados</h4>
            <div style={{ fontFamily: 'monospace', fontSize: '11px', color: '#d13212' }}>
              {debugInfo.sessionHistory.map((oldId, index) => (
                <div key={`session-history-${oldId.substring(0, 10)}-${Date.now()}-${index}`}>#{index + 1}: {oldId}</div>
              ))}
            </div>
          </Box>
        )}

        {/* Last Response Preview */}
        {debugInfo.lastResponse && (
          <Box>
            <h4>Vista Previa de Última Respuesta</h4>
            <div style={{
              fontSize: '12px',
              backgroundColor: '#f2f3f3',
              padding: '8px',
              borderRadius: '4px',
              maxHeight: '60px',
              overflow: 'hidden'
            }}>
              {debugInfo.lastResponse}...
            </div>
          </Box>
        )}

      </SpaceBetween>
    </ExpandableSection>
  );
}

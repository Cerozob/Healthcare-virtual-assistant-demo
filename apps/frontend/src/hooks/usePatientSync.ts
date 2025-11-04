/**
 * Patient Sync Hook
 * Handles patient context synchronization with enhanced notifications and state management
 */

import { useCallback } from 'react';
import { usePatientContext } from '../contexts/PatientContext';
import { useNotifications } from '../components/common/NotificationSystem';
import type { ChatMessage } from '../types/api';

interface PatientSyncOptions {
  onPatientDetected?: (patient: unknown) => void;
  onPatientChanged?: (oldPatient: unknown, newPatient: unknown) => void;
  onSyncError?: (error: Error) => void;
  generateNewSession?: (reason: string) => string;
}

export function usePatientSync(options: PatientSyncOptions = {}) {
  const { syncPatientFromResponse, selectedPatient } = usePatientContext();
  const { showSuccess, showWarning, showError } = useNotifications();
  const { onPatientDetected, onPatientChanged, onSyncError, generateNewSession } = options;

  const handlePatientContextSync = useCallback(async (
    patientContext: {
      patientId?: string;
      patientName?: string;
      contextChanged?: boolean;
      identificationSource?: string;
    },
    addMessage: (message: ChatMessage) => void,
    clearMessages?: () => void
  ) => {
    if (!patientContext || (!patientContext.patientId && !patientContext.patientName)) {
      return { syncCompleted: false, requiresNewSession: false };
    }

    try {
      console.log('🔄 Starting patient context sync...', patientContext);
      
      const syncResult = await syncPatientFromResponse(patientContext);
      
      if (syncResult.requiresNewSession) {
        console.warn('⚠️ SECURITY: Different patient detected - requires new session');
        
        // Generate new session if callback provided
        if (generateNewSession) {
          generateNewSession('Different patient detected');
        }
        
        // Clear messages if callback provided
        if (clearMessages) {
          clearMessages();
        }
        
        // Add security warning message
        const securityWarning: ChatMessage = {
          id: `security_warning_${Date.now()}`,
          content: `🚨 **CAMBIO DE PACIENTE DETECTADO**\n\nPor seguridad, se ha iniciado una nueva sesión.\n\n**Paciente anterior:** ${selectedPatient?.full_name} (${selectedPatient?.patient_id})\n**Nuevo paciente:** ${patientContext.patientName} (${patientContext.patientId})\n\n*El historial de chat anterior ha sido limpiado para proteger la privacidad.*`,
          type: 'system',
          timestamp: new Date().toISOString(),
          agentType: 'security'
        };
        
        addMessage(securityWarning);
        
        // Show security warning notification
        showWarning(
          'Cambio de paciente detectado',
          'Por seguridad, se ha iniciado una nueva sesión para proteger la privacidad del paciente.',
          {
            label: 'Entendido',
            handler: () => {} // No action needed
          }
        );

        // Notify about patient change
        if (onPatientChanged && selectedPatient) {
          onPatientChanged(selectedPatient, null);
        }
        
        return { syncCompleted: true, requiresNewSession: true };
      }
      
      if (syncResult.patientUpdated && syncResult.patient) {
        console.log('✅ Patient context updated successfully');
        
        const patient = syncResult.patient;
        
        // Create patient info string
        const cedula = patient.cedula || patient.document_number;
        let patientInfo = `**${patient.full_name}**`;
        
        if (cedula && cedula !== patient.patient_id) {
          patientInfo += ` (ID: ${patient.patient_id}, Cédula: ${cedula})`;
        } else {
          patientInfo += ` (ID: ${patient.patient_id})`;
        }
        
        // Determine detection message based on source
        const identificationSource = patientContext.identificationSource;
        let detectionMessage = '🎯 Paciente detectado automáticamente';
        
        switch (identificationSource) {
          case 'file_analysis':
            detectionMessage = '📄 Paciente identificado desde archivo';
            break;
          case 'conversation':
            detectionMessage = '💬 Paciente identificado en conversación';
            break;
          case 'document_metadata':
            detectionMessage = '📋 Paciente identificado desde metadatos';
            break;
          case 'cedula_extraction':
            detectionMessage = '🆔 Paciente identificado por cédula';
            break;
          case 'name_matching':
            detectionMessage = '👤 Paciente identificado por nombre';
            break;
          default:
            detectionMessage = '🎯 Paciente detectado automáticamente';
        }
        
        // Add system message about patient detection
        const systemMessage: ChatMessage = {
          id: `system_patient_${Date.now()}`,
          content: `${detectionMessage}: ${patientInfo}`,
          type: 'system',
          timestamp: new Date().toISOString(),
          agentType: 'system'
        };
        
        addMessage(systemMessage);
        
        // Show success notification
        showSuccess(
          'Paciente detectado',
          `Se ha identificado automáticamente al paciente: ${patient.full_name}`,
          true,
          4000
        );

        // Notify about patient detection
        if (onPatientDetected) {
          onPatientDetected(patient);
        }
        
        return { syncCompleted: true, requiresNewSession: false, patient };
      }
      
      // No update needed
      console.log('ℹ️ Patient context sync completed - no changes needed');
      return { syncCompleted: true, requiresNewSession: false };
      
    } catch (error) {
      console.error('❌ Patient context sync failed:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: `system_error_${Date.now()}`,
        content: `⚠️ **Error al sincronizar contexto del paciente**\n\nSe detectó información del paciente pero no se pudo sincronizar correctamente.\n\n**Paciente detectado:** ${patientContext.patientName || 'Desconocido'} (${patientContext.patientId || 'ID no disponible'})\n\n*Puedes seleccionar manualmente el paciente si es necesario.*`,
        type: 'system',
        timestamp: new Date().toISOString(),
        agentType: 'error'
      };
      
      addMessage(errorMessage);
      
      // Show error notification
      showError(
        'Error de sincronización',
        'No se pudo sincronizar el contexto del paciente. Puede seleccionar manualmente el paciente si es necesario.',
        {
          label: 'Seleccionar paciente',
          handler: () => {
            // This could trigger opening the patient selector
            console.log('User requested to select patient manually');
          }
        }
      );

      // Notify about sync error
      if (onSyncError && error instanceof Error) {
        onSyncError(error);
      }
      
      return { syncCompleted: false, requiresNewSession: false, error };
    }
  }, [syncPatientFromResponse, selectedPatient, onPatientDetected, onPatientChanged, onSyncError, generateNewSession]);

  return {
    handlePatientContextSync,
    selectedPatient
  };
}

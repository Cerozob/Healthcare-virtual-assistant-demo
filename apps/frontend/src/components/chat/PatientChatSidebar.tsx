/**
 * PatientChatSidebar Component
 * Displays current patient information in the chat interface with switching capability
 */

import { Box, Button, SpaceBetween, Container, Header, Icon } from '@cloudscape-design/components';
import { Patient } from '../../types/api';

interface PatientChatSidebarProps {
  patient: Patient | null;
  onChangePatient?: () => void;
  onClearPatient?: () => void;
}

export function PatientChatSidebar({ 
  patient, 
  onChangePatient,
  onClearPatient 
}: PatientChatSidebarProps) {
  if (!patient) {
    return (
      <Container>
        <Box textAlign="center" padding="l" color="text-body-secondary">
          <SpaceBetween size="m">
            <Icon name="user-profile" size="big" />
            <Box fontSize="body-m">
              No hay paciente seleccionado
            </Box>
            {onChangePatient && (
              <Button onClick={onChangePatient}>
                Seleccionar paciente
              </Button>
            )}
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  // Format date of birth
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              {onChangePatient && (
                <Button
                  variant="icon"
                  iconName="edit"
                  ariaLabel="Cambiar paciente"
                  onClick={onChangePatient}
                />
              )}
              {onClearPatient && (
                <Button
                  variant="icon"
                  iconName="close"
                  ariaLabel="Limpiar paciente"
                  onClick={onClearPatient}
                />
              )}
            </SpaceBetween>
          }
        >
          Paciente actual
        </Header>
      }
    >
      <SpaceBetween size="m">
        {/* Patient Avatar */}
        <Box textAlign="center">
          <div
            style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              backgroundColor: '#0972d3',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto'
            }}
          >
            <Icon name="user-profile" variant="inverted" size="big" />
          </div>
        </Box>

        {/* Patient Name */}
        <Box textAlign="center">
          <Box fontSize="heading-m" fontWeight="bold">
            {patient.full_name}
          </Box>
          <Box fontSize="body-s" color="text-body-secondary">
            ID: {patient.patient_id}
          </Box>
        </Box>

        {/* Patient Details */}
        <div>
          <Box padding={{ bottom: 'xs' }}>
            <Box fontSize="body-s" fontWeight="bold" color="text-label">
              Fecha de nacimiento
            </Box>
            <Box fontSize="body-m">
              {formatDate(patient.date_of_birth)}
            </Box>
          </Box>

          <Box padding={{ bottom: 'xs' }}>
            <Box fontSize="body-s" fontWeight="bold" color="text-label">
              Registrado
            </Box>
            <Box fontSize="body-m">
              {formatDate(patient.created_at)}
            </Box>
          </Box>

          {patient.updated_at && (
            <Box>
              <Box fontSize="body-s" fontWeight="bold" color="text-label">
                Última actualización
              </Box>
              <Box fontSize="body-m">
                {formatDate(patient.updated_at)}
              </Box>
            </Box>
          )}
        </div>

        {/* Context Info */}
        <div
          style={{
            padding: '12px',
            backgroundColor: '#f2f8fd',
            borderRadius: '8px',
            border: '1px solid #0972d3'
          }}
        >
          <SpaceBetween size="xs">
            <Box fontSize="body-s" fontWeight="bold" color="text-status-info">
              <Icon name="status-info" /> Contexto activo
            </Box>
            <Box fontSize="body-s">
              Las consultas del chat incluirán información de este paciente.
            </Box>
          </SpaceBetween>
        </div>
      </SpaceBetween>
    </Container>
  );
}

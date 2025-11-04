/**
 * PatientChatSidebar Component
 * Displays current patient information in the chat interface with switching capability
 */

import { Box, Button, SpaceBetween, Container, Header, Icon, Cards, ExpandableSection } from '@cloudscape-design/components';
import type { Patient } from '../../types/api';

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
            <Box fontSize="body-s" color="text-body-secondary">
              El paciente se seleccionará automáticamente durante la conversación
            </Box>
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

        {/* Basic Patient Info */}
        <div>
          {patient.date_of_birth && patient.date_of_birth !== '1900-01-01' && (
            <Box padding={{ bottom: 'xs' }}>
              <Box fontSize="body-s" fontWeight="bold" color="text-label">
                Fecha de nacimiento
              </Box>
              <Box fontSize="body-m">
                {formatDate(patient.date_of_birth)}
              </Box>
            </Box>
          )}

          {patient.cedula && (
            <Box padding={{ bottom: 'xs' }}>
              <Box fontSize="body-s" fontWeight="bold" color="text-label">
                Cédula
              </Box>
              <Box fontSize="body-m">
                {patient.cedula}
              </Box>
            </Box>
          )}

          {patient.phone && (
            <Box padding={{ bottom: 'xs' }}>
              <Box fontSize="body-s" fontWeight="bold" color="text-label">
                Teléfono
              </Box>
              <Box fontSize="body-m">
                {patient.phone}
              </Box>
            </Box>
          )}
        </div>

        {/* Expandable Patient Details */}
        <ExpandableSection headerText="Detalles completos del paciente">
          <SpaceBetween size="s">
            {/* Personal Information */}
            <div>
              <Box fontSize="body-s" fontWeight="bold" color="text-label" padding={{ bottom: 'xs' }}>
                Información Personal
              </Box>
              
              {patient.email && (
                <Box padding={{ bottom: 'xs' }}>
                  <Box fontSize="body-s" color="text-label">Email:</Box>
                  <Box fontSize="body-m">{patient.email}</Box>
                </Box>
              )}
              
              {patient.gender && (
                <Box padding={{ bottom: 'xs' }}>
                  <Box fontSize="body-s" color="text-label">Género:</Box>
                  <Box fontSize="body-m">{patient.gender === 'M' ? 'Masculino' : patient.gender === 'F' ? 'Femenino' : patient.gender}</Box>
                </Box>
              )}
              
              {patient.document_type && patient.document_number && (
                <Box padding={{ bottom: 'xs' }}>
                  <Box fontSize="body-s" color="text-label">Documento:</Box>
                  <Box fontSize="body-m">{patient.document_type}: {patient.document_number}</Box>
                </Box>
              )}
            </div>

            {/* Address Information */}
            {patient.address && (patient.address.street || patient.address.city) && (
              <div>
                <Box fontSize="body-s" fontWeight="bold" color="text-label" padding={{ bottom: 'xs' }}>
                  Dirección
                </Box>
                <Box fontSize="body-m">
                  {[
                    patient.address.street,
                    patient.address.city,
                    patient.address.province,
                    patient.address.country
                  ].filter(Boolean).join(', ')}
                  {patient.address.postal_code && ` (${patient.address.postal_code})`}
                </Box>
              </div>
            )}

            {/* Medical History */}
            {patient.medical_history?.conditions && patient.medical_history.conditions.length > 0 && (
              <div>
                <Box fontSize="body-s" fontWeight="bold" color="text-label" padding={{ bottom: 'xs' }}>
                  Condiciones Médicas ({patient.medical_history.conditions.length})
                </Box>
                {patient.medical_history.conditions.slice(0, 3).map((condition, index) => (
                  <Box key={`condition-${condition.descripcion}-${index}`} padding={{ bottom: 'xs' }}>
                    <Box fontSize="body-s">{condition.descripcion}</Box>
                    <Box fontSize="body-s" color="text-body-secondary">
                      {condition.fecha_diagnostico} - {condition.estado}
                    </Box>
                  </Box>
                ))}
                {patient.medical_history.conditions.length > 3 && (
                  <Box fontSize="body-s" color="text-body-secondary">
                    ... y {patient.medical_history.conditions.length - 3} más
                  </Box>
                )}
              </div>
            )}

            {/* Current Medications */}
            {patient.medical_history?.medications && patient.medical_history.medications.length > 0 && (
              <div>
                <Box fontSize="body-s" fontWeight="bold" color="text-label" padding={{ bottom: 'xs' }}>
                  Medicamentos Actuales ({patient.medical_history.medications.filter(med => med.activo).length})
                </Box>
                {patient.medical_history.medications.filter(med => med.activo).slice(0, 3).map((medication, index) => (
                  <Box key={`medication-${medication.nombre}-${index}`} padding={{ bottom: 'xs' }}>
                    <Box fontSize="body-s">{medication.nombre} - {medication.dosis}</Box>
                    <Box fontSize="body-s" color="text-body-secondary">
                      {medication.frecuencia}
                    </Box>
                  </Box>
                ))}
                {patient.medical_history.medications.filter(med => med.activo).length > 3 && (
                  <Box fontSize="body-s" color="text-body-secondary">
                    ... y {patient.medical_history.medications.filter(med => med.activo).length - 3} más
                  </Box>
                )}
              </div>
            )}

            {/* System Information */}
            <div>
              <Box fontSize="body-s" fontWeight="bold" color="text-label" padding={{ bottom: 'xs' }}>
                Información del Sistema
              </Box>
              
              <Box padding={{ bottom: 'xs' }}>
                <Box fontSize="body-s" color="text-label">Registrado:</Box>
                <Box fontSize="body-m">{formatDate(patient.created_at)}</Box>
              </Box>
              
              {patient.updated_at && (
                <Box>
                  <Box fontSize="body-s" color="text-label">Última actualización:</Box>
                  <Box fontSize="body-m">{formatDate(patient.updated_at)}</Box>
                </Box>
              )}
            </div>
          </SpaceBetween>
        </ExpandableSection>

        {/* Context Info Card */}
        <Cards
          ariaLabels={{
            itemSelectionLabel: () => 'Contexto del paciente',
            selectionGroupLabel: "Información de contexto"
          }}
          cardDefinition={{
            header: () => (
              <Box fontSize="body-s" fontWeight="bold" color="text-status-info">
                <Icon name="status-info" /> Contexto activo
              </Box>
            ),
            sections: [
              {
                id: "description",
                content: () => (
                  <SpaceBetween size="xs">
                    <Box fontSize="body-s">
                      Las consultas del chat incluirán información de este paciente.
                    </Box>
                    <Box fontSize="body-s" color="text-status-success">
                      <Icon name="security" /> Sesión segura activa
                    </Box>
                  </SpaceBetween>
                )
              }
            ]
          }}
          cardsPerRow={[{ cards: 1 }]}
          items={[{ id: 'context' }]}
          variant="container"
        />
      </SpaceBetween>
    </Container>
  );
}

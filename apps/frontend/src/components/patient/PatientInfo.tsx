/**
 * PatientInfo Component
 * Displays comprehensive patient information using Cloudscape Cards
 */

import {
  Badge,
  Box,
  ColumnLayout,
  Container,
  ExpandableSection,
  Header,
  Icon,
  SpaceBetween,
  Table
} from '@cloudscape-design/components';
import { es } from '../../i18n/es';
import type { LabResult, MedicalCondition, Medication, Patient } from '../../types/api';

interface PatientInfoProps {
  patient: Patient;
}

export const PatientInfo: React.FC<PatientInfoProps> = ({ patient }) => {
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    return age;
  };

  const formatAddress = (address: any) => {
    if (!address) return 'N/A';

    try {
      const addr = typeof address === 'string' ? JSON.parse(address) : address;
      const parts = [];

      if (addr.street || addr.calle) parts.push(addr.street || addr.calle);
      if (addr.numero) parts.push(addr.numero);
      if (addr.city || addr.ciudad) parts.push(addr.city || addr.ciudad);
      if (addr.province) parts.push(addr.province);
      if (addr.country || addr.pais) parts.push(addr.country || addr.pais);
      if (addr.postal_code || addr.codigo_postal) parts.push(addr.postal_code || addr.codigo_postal);

      return parts.length > 0 ? parts.join(', ') : 'N/A';
    } catch {
      return 'N/A';
    }
  };

  const getGenderBadge = (gender?: string) => {
    if (!gender) return <Badge color="grey">N/A</Badge>;
    return (
      <Badge color={gender === 'M' ? 'blue' : gender === 'F' ? 'red' : 'grey'}>
        {gender === 'M' ? 'Masculino' : gender === 'F' ? 'Femenino' : gender}
      </Badge>
    );
  };

  const renderMedicalHistory = () => {
    if (!patient.medical_history) return null;

    try {
      const history = typeof patient.medical_history === 'string'
        ? JSON.parse(patient.medical_history)
        : patient.medical_history;

      return (
        <Container header={<Header variant="h3">Historial médico</Header>}>
          <SpaceBetween size="m">
            {history.conditions && history.conditions.length > 0 && (
              <ExpandableSection headerText={`Condiciones médicas (${history.conditions.length})`}>
                <SpaceBetween size="s">
                  {history.conditions.map((condition: MedicalCondition, index: number) => (
                    <Box key={index}>
                      <SpaceBetween size="xs">
                        <Box variant="strong">{condition.descripcion}</Box>
                        <Box variant="small">
                          Estado: <Badge color={condition.estado === 'activo' ? 'green' : 'grey'}>
                            {condition.estado}
                          </Badge>
                        </Box>
                        {condition.fecha_diagnostico && (
                          <Box variant="small">Diagnóstico: {condition.fecha_diagnostico}</Box>
                        )}
                        {condition.codigo && (
                          <Box variant="small">Código: {condition.codigo}</Box>
                        )}
                      </SpaceBetween>
                    </Box>
                  ))}
                </SpaceBetween>
              </ExpandableSection>
            )}

            {history.medications && history.medications.length > 0 && (
              <ExpandableSection headerText={`Medicamentos (${history.medications.length})`}>
                <SpaceBetween size="s">
                  {history.medications.map((medication: Medication, index: number) => (
                    <Box key={index}>
                      <SpaceBetween size="xs">
                        <Box variant="strong">{medication.nombre}</Box>
                        <Box variant="small">Dosis: {medication.dosis}</Box>
                        <Box variant="small">Frecuencia: {medication.frecuencia}</Box>
                        <Box variant="small">Inicio: {medication.fecha_inicio}</Box>
                        <Box variant="small">
                          Estado: <Badge color={medication.activo ? 'green' : 'red'}>
                            {medication.activo ? 'Activo' : 'Inactivo'}
                          </Badge>
                        </Box>
                      </SpaceBetween>
                    </Box>
                  ))}
                </SpaceBetween>
              </ExpandableSection>
            )}
          </SpaceBetween>
        </Container>
      );
    } catch {
      return null;
    }
  };

  const renderLabResults = () => {
    if (!patient.lab_results) return null;

    try {
      const results = typeof patient.lab_results === 'string'
        ? JSON.parse(patient.lab_results)
        : patient.lab_results;

      if (!Array.isArray(results) || results.length === 0) return null;

      return (
        <Container header={<Header variant="h3">Resultados de laboratorio</Header>}>
          <Table
            columnDefinitions={[
              {
                id: 'fecha',
                header: 'Fecha',
                cell: (item: LabResult) => formatDate(item.fecha)
              },
              {
                id: 'nombre_prueba',
                header: 'Prueba',
                cell: (item: LabResult) => item.nombre_prueba
              },
              {
                id: 'valor',
                header: 'Valor',
                cell: (item: LabResult) => `${item.valor} ${item.unidad}`
              },
              {
                id: 'estado',
                header: 'Estado',
                cell: (item: LabResult) => (
                  <Badge color={item.estado === 'normal' ? 'green' : 'red'}>
                    {item.estado}
                  </Badge>
                )
              },
              {
                id: 'rango_referencia',
                header: 'Rango de referencia',
                cell: (item: LabResult) => item.rango_referencia
              }
            ]}
            items={results}
            variant="embedded"
          />
        </Container>
      );
    } catch {
      return null;
    }
  };

  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header variant="h2">
            {es.patient.title}
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Patient Photo Placeholder and Basic Info */}
          <ColumnLayout columns={2} variant="text-grid">
            <SpaceBetween size="s" alignItems="center">
              <Box textAlign="center" padding="l">
                <SpaceBetween size="s" alignItems="center">
                  <Icon name="user-profile-active" size="big" />
                  <Box variant="h3" fontWeight="bold">
                    {patient.full_name}
                  </Box>
                  <Box variant="small" color="text-body-secondary">
                    ID: {patient.patient_id}
                  </Box>
                </SpaceBetween>
              </Box>
            </SpaceBetween>

            <SpaceBetween size="m">
              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">{es.patient.dateOfBirth}</Box>
                <SpaceBetween size="xs" direction="horizontal" alignItems="center">
                  <Box>{formatDate(patient.date_of_birth)}</Box>
                  <Badge color="blue">
                    {patient.age || calculateAge(patient.date_of_birth)} años
                  </Badge>
                </SpaceBetween>
              </SpaceBetween>

              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Género</Box>
                <Box>{getGenderBadge(patient.gender)}</Box>
              </SpaceBetween>

              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Email</Box>
                <Box>{patient.email || 'N/A'}</Box>
              </SpaceBetween>

              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Teléfono</Box>
                <Box>{patient.phone || 'N/A'}</Box>
              </SpaceBetween>

              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">Documento</Box>
                <Box>
                  {patient.document_type && patient.document_number
                    ? `${patient.document_type}: ${patient.document_number}`
                    : 'N/A'
                  }
                </Box>
              </SpaceBetween>

              <SpaceBetween size="xs">
                <Box variant="awsui-key-label">{es.patient.status}</Box>
                <Badge color="green">Activo</Badge>
              </SpaceBetween>
            </SpaceBetween>
          </ColumnLayout>

          {/* Address */}
          <ColumnLayout columns={1} variant="text-grid">
            <SpaceBetween size="xs">
              <Box variant="awsui-key-label">Dirección</Box>
              <Box>{formatAddress(patient.address)}</Box>
            </SpaceBetween>
          </ColumnLayout>

          {/* System Information */}
          <ColumnLayout columns={3} variant="text-grid">
            <SpaceBetween size="xs">
              <Box variant="awsui-key-label">Fecha de registro</Box>
              <Box>{formatDate(patient.created_at)}</Box>
            </SpaceBetween>

            <SpaceBetween size="xs">
              <Box variant="awsui-key-label">Última actualización</Box>
              <Box>{formatDate(patient.updated_at)}</Box>
            </SpaceBetween>

            <SpaceBetween size="xs">
              <Box variant="awsui-key-label">Documento fuente</Box>
              <Box>{patient.source_scan && patient.source_scan.trim() !== '' ? (
                <Badge color="blue">Sí</Badge>
              ) : (
                <Badge color="grey">No</Badge>
              )}</Box>
            </SpaceBetween>
          </ColumnLayout>
        </SpaceBetween>
      </Container>

      {/* Medical History */}
      {renderMedicalHistory()}

      {/* Lab Results */}
      {renderLabResults()}
    </SpaceBetween>
  );
};

/**
 * PatientInfo Component
 * Displays comprehensive patient information using Cloudscape Cards
 */

import {
  Container,
  Header,
  SpaceBetween,
  ColumnLayout,
  Box,
  Badge
} from '@cloudscape-design/components';
import { Patient } from '../../types/api';
import { es } from '../../i18n/es';

interface PatientInfoProps {
  patient: Patient;
}

export const PatientInfo: React.FC<PatientInfoProps> = ({ patient }) => {
  const formatDate = (dateString: string) => {
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

  return (
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
          <div>
            <Box textAlign="center" padding="l">
              <Box
                margin={{ bottom: 's' }}
                color="text-body-secondary"
              >
                <svg
                  width="120"
                  height="120"
                  viewBox="0 0 120 120"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <circle cx="60" cy="60" r="60" fill="#E9EBED" />
                  <circle cx="60" cy="45" r="20" fill="#687078" />
                  <path
                    d="M20 100C20 80 35 70 60 70C85 70 100 80 100 100"
                    fill="#687078"
                  />
                </svg>
              </Box>
              <Box variant="h3" fontWeight="bold">
                {patient.full_name}
              </Box>
              <Box variant="small" color="text-body-secondary">
                ID: {patient.patient_id}
              </Box>
            </Box>
          </div>

          <SpaceBetween size="m">
            <div>
              <Box variant="awsui-key-label">{es.patient.dateOfBirth}</Box>
              <Box>
                {formatDate(patient.date_of_birth)}{' '}
                <Badge color="blue">
                  {calculateAge(patient.date_of_birth)} años
                </Badge>
              </Box>
            </div>

            <div>
              <Box variant="awsui-key-label">Fecha de registro</Box>
              <Box>{formatDate(patient.created_at)}</Box>
            </div>

            <div>
              <Box variant="awsui-key-label">Última actualización</Box>
              <Box>{formatDate(patient.updated_at)}</Box>
            </div>

            <div>
              <Box variant="awsui-key-label">{es.patient.status}</Box>
              <Badge color="green">Activo</Badge>
            </div>
          </SpaceBetween>
        </ColumnLayout>
      </SpaceBetween>
    </Container>
  );
};

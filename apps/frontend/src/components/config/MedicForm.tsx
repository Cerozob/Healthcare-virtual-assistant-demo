/**
 * MedicForm Component
 * Form for creating and editing medic data
 */

import { useState, useEffect } from 'react';
import {
  Form,
  FormField,
  Input,
  SpaceBetween,
  Button,
  Container,
  Header,
  Alert,
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Medic, CreateMedicRequest } from '../../types/api';

export interface MedicFormProps {
  medic?: Medic;
  onSubmit: (data: CreateMedicRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

interface FormData {
  full_name: string;
  specialty: string;
}

interface FormErrors {
  full_name?: string;
  specialty?: string;
}

export function MedicForm({ medic, onSubmit, onCancel, loading = false }: MedicFormProps) {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<FormData>({
    full_name: medic?.full_name || '',
    specialty: medic?.specialty || '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string>('');

  useEffect(() => {
    if (medic) {
      setFormData({
        full_name: medic.full_name,
        specialty: medic.specialty,
      });
    }
  }, [medic]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.full_name.trim()) {
      newErrors.full_name = t.validation.required;
    } else if (formData.full_name.trim().length < 2) {
      newErrors.full_name = 'El nombre debe tener al menos 2 caracteres';
    }

    if (!formData.specialty.trim()) {
      newErrors.specialty = t.validation.required;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');

    if (!validateForm()) {
      return;
    }

    try {
      // Generate a random license number for demo purposes
      const randomLicense = `MED-${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
      const submitData = {
        ...formData,
        license_number: randomLicense
      };
      await onSubmit(submitData);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : t.errors.generic);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Form
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onCancel} disabled={loading}>
              {t.common.cancel}
            </Button>
            <Button variant="primary" loading={loading} formAction="submit">
              {medic ? t.common.update : t.common.create}
            </Button>
          </SpaceBetween>
        }
        errorText={submitError}
      >
        <Container header={<Header variant="h2">{medic ? 'Editar Médico' : 'Nuevo Médico'}</Header>}>
          <SpaceBetween size="l">
            {submitError && (
              <Alert type="error" dismissible onDismiss={() => setSubmitError('')}>
                {submitError}
              </Alert>
            )}

            <FormField
              label="Nombre completo"
              errorText={errors.full_name}
              constraintText="Ingrese el nombre completo del médico"
            >
              <Input
                value={formData.full_name}
                onChange={({ detail }) => {
                  setFormData({ ...formData, full_name: detail.value });
                  if (errors.full_name) {
                    setErrors({ ...errors, full_name: undefined });
                  }
                }}
                placeholder="Ej: Dra. María González"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Especialidad"
              errorText={errors.specialty}
              constraintText="Ingrese la especialidad médica"
            >
              <Input
                value={formData.specialty}
                onChange={({ detail }) => {
                  setFormData({ ...formData, specialty: detail.value });
                  if (errors.specialty) {
                    setErrors({ ...errors, specialty: undefined });
                  }
                }}
                placeholder="Ej: Cardiología"
                disabled={loading}
              />
            </FormField>

            <Alert type="info" dismissible={false}>
              Nota: El número de licencia se generará automáticamente para esta demostración.
            </Alert>
          </SpaceBetween>
        </Container>
      </Form>
    </form>
  );
}

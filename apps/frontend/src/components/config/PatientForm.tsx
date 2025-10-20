/**
 * PatientForm Component
 * Form for creating and editing patient data
 */

import { useState, useEffect } from 'react';
import {
  Form,
  FormField,
  Input,
  DatePicker,
  SpaceBetween,
  Button,
  Container,
  Header,
  Alert,
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Patient, CreatePatientRequest } from '../../types/api';

export interface PatientFormProps {
  patient?: Patient;
  onSubmit: (data: CreatePatientRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

interface FormData {
  full_name: string;
  date_of_birth: string;
}

interface FormErrors {
  full_name?: string;
  date_of_birth?: string;
}

export function PatientForm({ patient, onSubmit, onCancel, loading = false }: PatientFormProps) {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<FormData>({
    full_name: patient?.full_name || '',
    date_of_birth: patient?.date_of_birth || '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string>('');

  useEffect(() => {
    if (patient) {
      setFormData({
        full_name: patient.full_name,
        date_of_birth: patient.date_of_birth,
      });
    }
  }, [patient]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.full_name.trim()) {
      newErrors.full_name = t.validation.required;
    } else if (formData.full_name.trim().length < 2) {
      newErrors.full_name = 'El nombre debe tener al menos 2 caracteres';
    }

    if (!formData.date_of_birth) {
      newErrors.date_of_birth = t.validation.required;
    } else {
      const birthDate = new Date(formData.date_of_birth);
      const today = new Date();
      if (birthDate > today) {
        newErrors.date_of_birth = 'La fecha de nacimiento no puede ser futura';
      }
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
      await onSubmit(formData);
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
              {patient ? t.common.update : t.common.create}
            </Button>
          </SpaceBetween>
        }
        errorText={submitError}
      >
        <Container header={<Header variant="h2">{patient ? 'Editar Paciente' : 'Nuevo Paciente'}</Header>}>
          <SpaceBetween size="l">
            {submitError && (
              <Alert type="error" dismissible onDismiss={() => setSubmitError('')}>
                {submitError}
              </Alert>
            )}

            <FormField
              label="Nombre completo"
              errorText={errors.full_name}
              constraintText="Ingrese el nombre completo del paciente"
            >
              <Input
                value={formData.full_name}
                onChange={({ detail }) => {
                  setFormData({ ...formData, full_name: detail.value });
                  if (errors.full_name) {
                    setErrors({ ...errors, full_name: undefined });
                  }
                }}
                placeholder="Ej: Juan Pérez García"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Fecha de nacimiento"
              errorText={errors.date_of_birth}
              constraintText="Seleccione la fecha de nacimiento del paciente"
            >
              <DatePicker
                value={formData.date_of_birth}
                onChange={({ detail }) => {
                  setFormData({ ...formData, date_of_birth: detail.value });
                  if (errors.date_of_birth) {
                    setErrors({ ...errors, date_of_birth: undefined });
                  }
                }}
                placeholder="YYYY-MM-DD"
                disabled={loading}
                openCalendarAriaLabel={(selectedDate) =>
                  selectedDate ? `Fecha seleccionada: ${selectedDate}` : 'Seleccionar fecha'
                }
              />
            </FormField>
          </SpaceBetween>
        </Container>
      </Form>
    </form>
  );
}

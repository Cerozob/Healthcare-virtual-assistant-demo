/**
 * ExamForm Component
 * Form for creating and editing exam templates/types
 */

import { useState, useEffect } from 'react';
import {
  Form,
  FormField,
  Input,
  Textarea,
  SpaceBetween,
  Button,
  Container,
  Header,
  Alert,
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Exam, CreateExamRequest } from '../../types/api';

export interface ExamFormProps {
  exam?: Exam;
  onSubmit: (data: CreateExamRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

interface FormData {
  exam_name: string;
  exam_type: string;
  description: string;
  duration_minutes: number;
  preparation_instructions: string;
}

interface FormErrors {
  exam_name?: string;
  exam_type?: string;
  duration_minutes?: string;
}

export function ExamForm({ exam, onSubmit, onCancel, loading = false }: ExamFormProps) {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<FormData>({
    exam_name: exam?.exam_name || '',
    exam_type: exam?.exam_type || '',
    description: exam?.description || '',
    duration_minutes: exam?.duration_minutes || 30,
    preparation_instructions: exam?.preparation_instructions || '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string>('');

  useEffect(() => {
    if (exam) {
      setFormData({
        exam_name: exam.exam_name,
        exam_type: exam.exam_type,
        description: exam.description || '',
        duration_minutes: exam.duration_minutes,
        preparation_instructions: exam.preparation_instructions || '',
      });
    }
  }, [exam]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.exam_name.trim()) {
      newErrors.exam_name = t.validation.required;
    }

    if (!formData.exam_type.trim()) {
      newErrors.exam_type = t.validation.required;
    }

    if (!formData.duration_minutes || formData.duration_minutes <= 0) {
      newErrors.duration_minutes = 'Duration must be greater than 0';
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
      const submitData: CreateExamRequest = {
        exam_name: formData.exam_name,
        exam_type: formData.exam_type,
        duration_minutes: formData.duration_minutes,
      };

      if (formData.description.trim()) {
        submitData.description = formData.description;
      }

      if (formData.preparation_instructions.trim()) {
        submitData.preparation_instructions = formData.preparation_instructions;
      }

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
              {exam ? t.common.update : t.common.create}
            </Button>
          </SpaceBetween>
        }
        errorText={submitError}
      >
        <Container header={<Header variant="h2">{exam ? 'Editar Tipo de Examen' : 'Nuevo Tipo de Examen'}</Header>}>
          <SpaceBetween size="l">
            {submitError && (
              <Alert type="error" dismissible onDismiss={() => setSubmitError('')}>
                {submitError}
              </Alert>
            )}

            <FormField
              label="Nombre del examen"
              errorText={errors.exam_name}
              constraintText="Ingrese el nombre del examen"
            >
              <Input
                value={formData.exam_name}
                onChange={({ detail }) => {
                  setFormData({ ...formData, exam_name: detail.value });
                  if (errors.exam_name) {
                    setErrors({ ...errors, exam_name: undefined });
                  }
                }}
                placeholder="Ej: Radiografía de tórax"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Tipo de examen"
              errorText={errors.exam_type}
              constraintText="Ingrese la categoría del examen"
            >
              <Input
                value={formData.exam_type}
                onChange={({ detail }) => {
                  setFormData({ ...formData, exam_type: detail.value });
                  if (errors.exam_type) {
                    setErrors({ ...errors, exam_type: undefined });
                  }
                }}
                placeholder="Ej: Radiología, Laboratorio, Cardiología"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Duración (minutos)"
              errorText={errors.duration_minutes}
              constraintText="Duración estimada del examen en minutos"
            >
              <Input
                type="number"
                value={formData.duration_minutes.toString()}
                onChange={({ detail }) => {
                  const value = parseInt(detail.value) || 0;
                  setFormData({ ...formData, duration_minutes: value });
                  if (errors.duration_minutes) {
                    setErrors({ ...errors, duration_minutes: undefined });
                  }
                }}
                placeholder="30"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Descripción"
              description="Opcional - Descripción detallada del examen"
            >
              <Textarea
                value={formData.description}
                onChange={({ detail }) => setFormData({ ...formData, description: detail.value })}
                placeholder="Descripción del examen..."
                disabled={loading}
                rows={3}
              />
            </FormField>

            <FormField
              label="Instrucciones de preparación"
              description="Opcional - Instrucciones para el paciente antes del examen"
            >
              <Textarea
                value={formData.preparation_instructions}
                onChange={({ detail }) => setFormData({ ...formData, preparation_instructions: detail.value })}
                placeholder="Instrucciones de preparación..."
                disabled={loading}
                rows={3}
              />
            </FormField>
          </SpaceBetween>
        </Container>
      </Form>
    </form>
  );
}

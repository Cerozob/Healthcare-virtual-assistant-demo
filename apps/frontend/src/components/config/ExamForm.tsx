/**
 * ExamForm Component
 * Form for creating and editing exam data
 */

import { useState, useEffect } from 'react';
import {
  Form,
  FormField,
  Input,
  DatePicker,
  Select,
  Textarea,
  SpaceBetween,
  Button,
  Container,
  Header,
  Alert,
  SelectProps,
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';
import type { Exam, CreateExamRequest } from '../../types/api';

export interface ExamFormProps {
  exam?: Exam;
  onSubmit: (data: CreateExamRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  patients?: Array<{ patient_id: string; full_name: string }>;
  medics?: Array<{ medic_id: string; full_name: string }>;
}

interface FormData {
  patient_id: string;
  medic_id: string;
  exam_type: string;
  exam_date: string;
  results: string;
  status: string;
}

interface FormErrors {
  patient_id?: string;
  medic_id?: string;
  exam_type?: string;
  exam_date?: string;
  status?: string;
}

const examStatusOptions: SelectProps.Option[] = [
  { label: 'Programado', value: 'scheduled' },
  { label: 'En progreso', value: 'in-progress' },
  { label: 'Completado', value: 'completed' },
  { label: 'Cancelado', value: 'cancelled' },
];

export function ExamForm({ exam, onSubmit, onCancel, loading = false, patients = [], medics = [] }: ExamFormProps) {
  const { t } = useLanguage();
  const [formData, setFormData] = useState<FormData>({
    patient_id: exam?.patient_id || '',
    medic_id: exam?.medic_id || '',
    exam_type: exam?.exam_type || '',
    exam_date: exam?.exam_date || '',
    results: exam?.results || '',
    status: exam?.status || 'scheduled',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string>('');

  useEffect(() => {
    if (exam) {
      setFormData({
        patient_id: exam.patient_id,
        medic_id: exam.medic_id,
        exam_type: exam.exam_type,
        exam_date: exam.exam_date,
        results: exam.results || '',
        status: exam.status,
      });
    }
  }, [exam]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.patient_id) {
      newErrors.patient_id = t.validation.required;
    }

    if (!formData.medic_id) {
      newErrors.medic_id = t.validation.required;
    }

    if (!formData.exam_type.trim()) {
      newErrors.exam_type = t.validation.required;
    }

    if (!formData.exam_date) {
      newErrors.exam_date = t.validation.required;
    }

    if (!formData.status) {
      newErrors.status = t.validation.required;
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
        patient_id: formData.patient_id,
        medic_id: formData.medic_id,
        exam_type: formData.exam_type,
        exam_date: formData.exam_date,
        status: formData.status,
      };

      if (formData.results.trim()) {
        submitData.results = formData.results;
      }

      await onSubmit(submitData);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : t.errors.generic);
    }
  };

  const patientOptions: SelectProps.Option[] = patients.map((p) => ({
    label: `${p.full_name} (${p.patient_id})`,
    value: p.patient_id,
  }));

  const medicOptions: SelectProps.Option[] = medics.map((m) => ({
    label: `${m.full_name} (${m.medic_id})`,
    value: m.medic_id,
  }));

  const selectedPatient = patientOptions.find((opt) => opt.value === formData.patient_id) || null;
  const selectedMedic = medicOptions.find((opt) => opt.value === formData.medic_id) || null;
  const selectedStatus = examStatusOptions.find((opt) => opt.value === formData.status) || null;

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
        <Container header={<Header variant="h2">{exam ? 'Editar Examen' : 'Nuevo Examen'}</Header>}>
          <SpaceBetween size="l">
            {submitError && (
              <Alert type="error" dismissible onDismiss={() => setSubmitError('')}>
                {submitError}
              </Alert>
            )}

            <FormField
              label="Paciente"
              errorText={errors.patient_id}
              constraintText="Seleccione el paciente para el examen"
            >
              <Select
                selectedOption={selectedPatient}
                onChange={({ detail }) => {
                  setFormData({ ...formData, patient_id: detail.selectedOption.value || '' });
                  if (errors.patient_id) {
                    setErrors({ ...errors, patient_id: undefined });
                  }
                }}
                options={patientOptions}
                placeholder="Seleccione un paciente"
                disabled={loading}
                filteringType="auto"
              />
            </FormField>

            <FormField
              label="Médico"
              errorText={errors.medic_id}
              constraintText="Seleccione el médico responsable"
            >
              <Select
                selectedOption={selectedMedic}
                onChange={({ detail }) => {
                  setFormData({ ...formData, medic_id: detail.selectedOption.value || '' });
                  if (errors.medic_id) {
                    setErrors({ ...errors, medic_id: undefined });
                  }
                }}
                options={medicOptions}
                placeholder="Seleccione un médico"
                disabled={loading}
                filteringType="auto"
              />
            </FormField>

            <FormField
              label="Tipo de examen"
              errorText={errors.exam_type}
              constraintText="Ingrese el tipo de examen"
            >
              <Input
                value={formData.exam_type}
                onChange={({ detail }) => {
                  setFormData({ ...formData, exam_type: detail.value });
                  if (errors.exam_type) {
                    setErrors({ ...errors, exam_type: undefined });
                  }
                }}
                placeholder="Ej: Radiografía de tórax"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Fecha del examen"
              errorText={errors.exam_date}
              constraintText="Seleccione la fecha del examen"
            >
              <DatePicker
                value={formData.exam_date}
                onChange={({ detail }) => {
                  setFormData({ ...formData, exam_date: detail.value });
                  if (errors.exam_date) {
                    setErrors({ ...errors, exam_date: undefined });
                  }
                }}
                placeholder="YYYY-MM-DD"
                disabled={loading}
                openCalendarAriaLabel={(selectedDate) =>
                  selectedDate ? `Fecha seleccionada: ${selectedDate}` : 'Seleccionar fecha'
                }
              />
            </FormField>

            <FormField
              label="Estado"
              errorText={errors.status}
              constraintText="Seleccione el estado del examen"
            >
              <Select
                selectedOption={selectedStatus}
                onChange={({ detail }) => {
                  setFormData({ ...formData, status: detail.selectedOption.value || 'scheduled' });
                  if (errors.status) {
                    setErrors({ ...errors, status: undefined });
                  }
                }}
                options={examStatusOptions}
                placeholder="Seleccione un estado"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Resultados"
              description="Opcional - Ingrese los resultados del examen"
            >
              <Textarea
                value={formData.results}
                onChange={({ detail }) => setFormData({ ...formData, results: detail.value })}
                placeholder="Ingrese los resultados del examen..."
                disabled={loading}
                rows={4}
              />
            </FormField>
          </SpaceBetween>
        </Container>
      </Form>
    </form>
  );
}

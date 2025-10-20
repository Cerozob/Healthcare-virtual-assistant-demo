/**
 * ReservationForm Component
 * Form for creating and editing reservation data
 */

import { useState, useEffect } from 'react';
import {
  Form,
  FormField,
  DatePicker,
  TimeInput,
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
import type { Reservation, CreateReservationRequest } from '../../types/api';

export interface ReservationFormProps {
  reservation?: Reservation;
  onSubmit: (data: CreateReservationRequest) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
  patients?: Array<{ patient_id: string; full_name: string }>;
  medics?: Array<{ medic_id: string; full_name: string }>;
}

interface FormData {
  patient_id: string;
  medic_id: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
  notes: string;
}

interface FormErrors {
  patient_id?: string;
  medic_id?: string;
  appointment_date?: string;
  appointment_time?: string;
  status?: string;
}

const reservationStatusOptions: SelectProps.Option[] = [
  { label: 'Confirmada', value: 'confirmed' },
  { label: 'Pendiente', value: 'pending' },
  { label: 'Cancelada', value: 'cancelled' },
];

export function ReservationForm({
  reservation,
  onSubmit,
  onCancel,
  loading = false,
  patients = [],
  medics = [],
}: ReservationFormProps) {
  const { t } = useLanguage();
  
  // Parse existing appointment_date if available
  const parseDateTime = (dateTimeStr?: string) => {
    if (!dateTimeStr) return { date: '', time: '' };
    const dt = new Date(dateTimeStr);
    const date = dt.toISOString().split('T')[0];
    const time = dt.toTimeString().slice(0, 5);
    return { date, time };
  };

  const { date: initialDate, time: initialTime } = parseDateTime(reservation?.appointment_date);

  const [formData, setFormData] = useState<FormData>({
    patient_id: reservation?.patient_id || '',
    medic_id: reservation?.medic_id || '',
    appointment_date: initialDate,
    appointment_time: initialTime,
    status: reservation?.status || 'pending',
    notes: reservation?.notes || '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState<string>('');

  useEffect(() => {
    if (reservation) {
      const { date, time } = parseDateTime(reservation.appointment_date);
      setFormData({
        patient_id: reservation.patient_id,
        medic_id: reservation.medic_id,
        appointment_date: date,
        appointment_time: time,
        status: reservation.status,
        notes: reservation.notes || '',
      });
    }
  }, [reservation]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.patient_id) {
      newErrors.patient_id = t.validation.required;
    }

    if (!formData.medic_id) {
      newErrors.medic_id = t.validation.required;
    }

    if (!formData.appointment_date) {
      newErrors.appointment_date = t.validation.required;
    }

    if (!formData.appointment_time) {
      newErrors.appointment_time = t.validation.required;
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
      // Combine date and time into ISO string
      const appointmentDateTime = `${formData.appointment_date}T${formData.appointment_time}:00`;

      const submitData: CreateReservationRequest = {
        patient_id: formData.patient_id,
        medic_id: formData.medic_id,
        appointment_date: appointmentDateTime,
        status: formData.status,
      };

      if (formData.notes.trim()) {
        submitData.notes = formData.notes;
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
  const selectedStatus = reservationStatusOptions.find((opt) => opt.value === formData.status) || null;

  return (
    <form onSubmit={handleSubmit}>
      <Form
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link" onClick={onCancel} disabled={loading}>
              {t.common.cancel}
            </Button>
            <Button variant="primary" loading={loading} formAction="submit">
              {reservation ? t.common.update : t.common.create}
            </Button>
          </SpaceBetween>
        }
        errorText={submitError}
      >
        <Container header={<Header variant="h2">{reservation ? 'Editar Reserva' : 'Nueva Reserva'}</Header>}>
          <SpaceBetween size="l">
            {submitError && (
              <Alert type="error" dismissible onDismiss={() => setSubmitError('')}>
                {submitError}
              </Alert>
            )}

            <FormField
              label="Paciente"
              errorText={errors.patient_id}
              constraintText="Seleccione el paciente para la cita"
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
              constraintText="Seleccione el médico para la cita"
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
              label="Fecha de la cita"
              errorText={errors.appointment_date}
              constraintText="Seleccione la fecha de la cita"
            >
              <DatePicker
                value={formData.appointment_date}
                onChange={({ detail }) => {
                  setFormData({ ...formData, appointment_date: detail.value });
                  if (errors.appointment_date) {
                    setErrors({ ...errors, appointment_date: undefined });
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
              label="Hora de la cita"
              errorText={errors.appointment_time}
              constraintText="Seleccione la hora de la cita"
            >
              <TimeInput
                value={formData.appointment_time}
                onChange={({ detail }) => {
                  setFormData({ ...formData, appointment_time: detail.value });
                  if (errors.appointment_time) {
                    setErrors({ ...errors, appointment_time: undefined });
                  }
                }}
                placeholder="HH:MM"
                disabled={loading}
                format="hh:mm"
              />
            </FormField>

            <FormField
              label="Estado"
              errorText={errors.status}
              constraintText="Seleccione el estado de la reserva"
            >
              <Select
                selectedOption={selectedStatus}
                onChange={({ detail }) => {
                  setFormData({ ...formData, status: detail.selectedOption.value || 'pending' });
                  if (errors.status) {
                    setErrors({ ...errors, status: undefined });
                  }
                }}
                options={reservationStatusOptions}
                placeholder="Seleccione un estado"
                disabled={loading}
              />
            </FormField>

            <FormField
              label="Notas"
              description="Opcional - Ingrese notas adicionales sobre la cita"
            >
              <Textarea
                value={formData.notes}
                onChange={({ detail }) => setFormData({ ...formData, notes: detail.value })}
                placeholder="Ingrese notas adicionales..."
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

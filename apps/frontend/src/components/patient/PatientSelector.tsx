/**
 * PatientSelector Component
 * Allows users to search and select patients with autocomplete functionality
 */

import { useState, useEffect, useCallback } from 'react';
import {
  FormField,
  Input,
  Autosuggest,
  SpaceBetween,
  Button,
  Alert
} from '@cloudscape-design/components';
import { patientService } from '../../services/patientService';
import type { Patient } from '../../types/api';
import { es } from '../../i18n/es';

interface PatientSelectorProps {
  onPatientSelect?: (patient: Patient | null) => void;
  onPatientSelected?: () => void;
  selectedPatient?: Patient | null;
}

export const PatientSelector: React.FC<PatientSelectorProps> = ({
  onPatientSelect,
  onPatientSelected,
  selectedPatient
}) => {
  const [patientId, setPatientId] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [suggestions, setSuggestions] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Load suggestions when search value changes
  useEffect(() => {
    const loadSuggestions = async () => {
      if (searchValue.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        setLoading(true);
        const response = await patientService.getPatients({ limit: 10 });
        // Filter patients by search value (client-side filtering)
        const filtered = response.patients.filter(patient =>
          patient.full_name.toLowerCase().includes(searchValue.toLowerCase()) ||
          patient.patient_id.toLowerCase().includes(searchValue.toLowerCase())
        );
        setSuggestions(filtered);
      } catch (err) {
        console.error('Error loading patient suggestions:', err);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(loadSuggestions, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchValue]);

  const handlePatientIdSubmit = async () => {
    if (!patientId.trim()) {
      setValidationError(es.validation.required);
      return;
    }

    setValidationError(null);
    setError(null);
    setLoading(true);

    try {
      const response = await patientService.getPatient(patientId.trim());
      if (onPatientSelect) {
        onPatientSelect(response.patient);
      }
      setSearchValue(response.patient.full_name);
      if (onPatientSelected) {
        onPatientSelected();
      }
    } catch (err) {
      console.error('Error fetching patient:', err);
      setError('No se encontró el paciente con el ID especificado');
      if (onPatientSelect) {
        onPatientSelect(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAutosuggestSelect = useCallback(
    ({ detail }: { detail: { value: string } }) => {
      setSearchValue(detail.value);
      
      // Find selected patient from suggestions
      const selected = suggestions.find(
        p => p.full_name === detail.value || p.patient_id === detail.value
      );
      
      if (selected) {
        setPatientId(selected.patient_id);
        if (onPatientSelect) {
          onPatientSelect(selected);
        }
        setError(null);
        setValidationError(null);
        if (onPatientSelected) {
          onPatientSelected();
        }
      }
    },
    [suggestions, onPatientSelect, onPatientSelected]
  );

  const handleClearSelection = () => {
    setPatientId('');
    setSearchValue('');
    setSuggestions([]);
    setError(null);
    setValidationError(null);
    if (onPatientSelect) {
      onPatientSelect(null);
    }
  };

  return (
    <SpaceBetween size="m">
      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <FormField
        label={es.patient.id}
        description="Ingrese el ID del paciente para buscar"
        errorText={validationError}
      >
        <SpaceBetween size="xs" direction="horizontal">
          <Input
            value={patientId}
            onChange={({ detail }) => {
              setPatientId(detail.value);
              setValidationError(null);
            }}
            placeholder="Ej: PAT001"
            disabled={loading}
          />
          <Button
            onClick={handlePatientIdSubmit}
            loading={loading}
            disabled={!patientId.trim()}
          >
            {es.common.search}
          </Button>
        </SpaceBetween>
      </FormField>

      <FormField
        label={es.patient.searchPatient}
        description="O busque por nombre del paciente"
      >
        <Autosuggest
          value={searchValue}
          onChange={handleAutosuggestSelect}
          options={suggestions.map(patient => ({
            value: patient.full_name,
            label: patient.full_name,
            description: `ID: ${patient.patient_id}`,
            tags: [patient.patient_id]
          }))}
          placeholder="Escriba el nombre del paciente..."
          empty={searchValue.length < 2 ? "Escriba al menos 2 caracteres" : "No se encontraron pacientes"}
          loadingText="Buscando pacientes..."
          statusType={loading ? "loading" : "finished"}
          disabled={loading}
        />
      </FormField>

      {selectedPatient && (
        <Alert
          type="success"
          dismissible
          onDismiss={handleClearSelection}
          header="Paciente seleccionado"
        >
          <SpaceBetween size="xs">
            <div><strong>Nombre:</strong> {selectedPatient.full_name}</div>
            <div><strong>ID:</strong> {selectedPatient.patient_id}</div>
            <div><strong>Fecha de nacimiento:</strong> {new Date(selectedPatient.date_of_birth).toLocaleDateString('es-MX')}</div>
          </SpaceBetween>
        </Alert>
      )}
    </SpaceBetween>
  );
};

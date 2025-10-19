/**
 * API Example Component
 * Demonstrates how to use the API services and hooks
 */

import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  Box,
  Alert,
  Spinner,
  Table,
  Input,
  FormField,
  Modal,
  Form
} from '@cloudscape-design/components';
import { usePatients, useCreatePatient } from '../hooks';
import { Patient } from '../types/api';

const ApiExample: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPatient, setNewPatient] = useState({
    full_name: '',
    date_of_birth: ''
  });

  // Use hooks for API operations
  const patientsApi = usePatients();
  const createPatientApi = useCreatePatient();

  // Load patients on component mount
  useEffect(() => {
    patientsApi.execute({ limit: 10, offset: 0 });
  }, []);

  const handleCreatePatient = async () => {
    const result = await createPatientApi.execute(newPatient);
    if (result) {
      setShowCreateModal(false);
      setNewPatient({ full_name: '', date_of_birth: '' });
      // Refresh patients list
      patientsApi.execute({ limit: 10, offset: 0 });
    }
  };

  const patients = patientsApi.data?.patients || [];

  return (
    <SpaceBetween size="l">
      <Header
        variant="h2"
        actions={
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            Create Patient
          </Button>
        }
      >
        API Example - Patients
      </Header>

      {patientsApi.error && (
        <Alert type="error" dismissible onDismiss={patientsApi.reset}>
          {patientsApi.error}
        </Alert>
      )}

      {createPatientApi.error && (
        <Alert type="error" dismissible onDismiss={createPatientApi.reset}>
          {createPatientApi.error}
        </Alert>
      )}

      <Container>
        {patientsApi.loading ? (
          <Box textAlign="center" padding="l">
            <Spinner size="large" />
          </Box>
        ) : (
          <Table
            columnDefinitions={[
              {
                id: 'full_name',
                header: 'Full Name',
                cell: (item: Patient) => item.full_name
              },
              {
                id: 'date_of_birth',
                header: 'Date of Birth',
                cell: (item: Patient) => item.date_of_birth
              },
              {
                id: 'created_at',
                header: 'Created At',
                cell: (item: Patient) => new Date(item.created_at).toLocaleDateString()
              }
            ]}
            items={patients}
            empty={
              <Box textAlign="center" color="inherit">
                <b>No patients found</b>
                <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                  No patients to display.
                </Box>
              </Box>
            }
          />
        )}
      </Container>

      <Modal
        visible={showCreateModal}
        onDismiss={() => setShowCreateModal(false)}
        header="Create New Patient"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                variant="link"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleCreatePatient}
                loading={createPatientApi.loading}
              >
                Create
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <Form>
          <SpaceBetween size="m">
            <FormField label="Full Name">
              <Input
                value={newPatient.full_name}
                onChange={({ detail }) =>
                  setNewPatient(prev => ({ ...prev, full_name: detail.value }))
                }
                placeholder="Enter patient's full name"
              />
            </FormField>
            <FormField label="Date of Birth">
              <Input
                value={newPatient.date_of_birth}
                onChange={({ detail }) =>
                  setNewPatient(prev => ({ ...prev, date_of_birth: detail.value }))
                }
                placeholder="YYYY-MM-DD"
              />
            </FormField>
          </SpaceBetween>
        </Form>
      </Modal>
    </SpaceBetween>
  );
};

export default ApiExample;

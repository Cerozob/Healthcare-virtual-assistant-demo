/**
 * Debug Panel Component
 * Shows debug information for chat responses and patient context
 */

import { useState } from 'react';
import {
  Box,
  Button,
  Container,
  ExpandableSection,
  Header,
  SpaceBetween,
  Alert
} from '@cloudscape-design/components';

interface DebugPanelProps {
  lastResponse?: unknown;
  lastRequest?: unknown;
  patientContext?: unknown;
  selectedPatient?: unknown;
}

export function DebugPanel({ 
  lastResponse, 
  lastRequest, 
  patientContext, 
  selectedPatient 
}: DebugPanelProps) {
  const [isVisible, setIsVisible] = useState(false);

  if (!isVisible) {
    return (
      <Box margin={{ top: 's' }}>
        <Button
          variant="link"
          iconName="bug"
          onClick={() => setIsVisible(true)}
        >
          Show Debug Panel
        </Button>
      </Box>
    );
  }

  return (
    <Container
      header={
        <Header
          variant="h3"
          actions={
            <Button
              variant="icon"
              iconName="close"
              onClick={() => setIsVisible(false)}
            />
          }
        >
          🐛 Debug Panel
        </Header>
      }
    >
      <SpaceBetween size="m">
        <Alert type="info">
          This panel shows debug information for troubleshooting patient identification issues.
        </Alert>

        <ExpandableSection headerText="Last Chat Response" defaultExpanded>
          <Box>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              fontSize: '12px',
              whiteSpace: 'pre-wrap'
            }}>
              {JSON.stringify(lastResponse, null, 2)}
            </pre>
          </Box>
        </ExpandableSection>

        <ExpandableSection headerText="Last Chat Request">
          <Box>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              fontSize: '12px',
              whiteSpace: 'pre-wrap'
            }}>
              {JSON.stringify(lastRequest, null, 2)}
            </pre>
          </Box>
        </ExpandableSection>

        <ExpandableSection headerText="Patient Context from Response">
          <Box>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              fontSize: '12px',
              whiteSpace: 'pre-wrap'
            }}>
              {JSON.stringify(patientContext, null, 2)}
            </pre>
          </Box>
        </ExpandableSection>

        <ExpandableSection headerText="Selected Patient State">
          <Box>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px', 
              overflow: 'auto',
              fontSize: '12px',
              whiteSpace: 'pre-wrap'
            }}>
              {JSON.stringify(selectedPatient, null, 2)}
            </pre>
          </Box>
        </ExpandableSection>

        <ExpandableSection headerText="Debug Instructions">
          <Box>
            <SpaceBetween size="s">
              <Box variant="h4">How to Debug Patient Identification Issues:</Box>
              
              <Box>
                <strong>1. Check Last Chat Response:</strong>
                <ul>
                  <li>Look for <code>patient_context</code> object</li>
                  <li>Verify <code>patient_found</code> is true</li>
                  <li>Check if <code>patient_data</code> exists and has correct structure</li>
                </ul>
              </Box>

              <Box>
                <strong>2. Verify Patient Data Structure:</strong>
                <ul>
                  <li><code>patient_id</code> should not be null/undefined</li>
                  <li><code>full_name</code> should contain the patient name</li>
                  <li>Check for alternative field names like <code>patient_name</code> or <code>id</code></li>
                </ul>
              </Box>

              <Box>
                <strong>3. Console Logs:</strong>
                <ul>
                  <li>Open browser DevTools (F12)</li>
                  <li>Look for debug logs starting with 🔍, 📤, 📥</li>
                  <li>Check for any error messages or warnings</li>
                </ul>
              </Box>

              <Box>
                <strong>4. Common Issues:</strong>
                <ul>
                  <li><strong>undefined (undefined):</strong> Patient data fields are null/undefined</li>
                  <li><strong>Empty patient_context:</strong> Agent didn't identify a patient</li>
                  <li><strong>Wrong patient selected:</strong> Check patient_id matching logic</li>
                </ul>
              </Box>
            </SpaceBetween>
          </Box>
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
}

/**
 * Database Settings Component
 * Displays Aurora Serverless v2 real-time status using CloudWatch metrics
 */

import { useState, useEffect } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  StatusIndicator,
  Button,
  ColumnLayout,
  KeyValuePairs
} from '@cloudscape-design/components';
import { CloudWatchClient, GetMetricStatisticsCommand } from '@aws-sdk/client-cloudwatch';
import { fetchAuthSession } from 'aws-amplify/auth';

interface DatabaseStatus {
  status: 'active' | 'paused' | 'unknown' | 'loading';
  cpuUtilization: number | null;
  acuUtilization: number | null;
  serverlessCapacity: number | null;
  lastUpdated: Date | null;
}

export function DatabaseSettings() {
  const [dbStatus, setDbStatus] = useState<DatabaseStatus>({
    status: 'unknown',
    cpuUtilization: null,
    acuUtilization: null,
    serverlessCapacity: null,
    lastUpdated: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkDatabaseStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get AWS credentials from Amplify
      const session = await fetchAuthSession();
      const credentials = session.credentials;

      if (!credentials) {
        throw new Error('No se pudieron obtener las credenciales de AWS');
      }

      console.log('🔍 DatabaseSettings: Checking database status...');
      console.log('📍 Region:', import.meta.env.VITE_AWS_REGION || 'us-east-1');

      // Get cluster identifier from environment
      const clusterIdentifier = import.meta.env.VITE_DB_CLUSTER_IDENTIFIER;
      
      if (!clusterIdentifier) {
        throw new Error('VITE_DB_CLUSTER_IDENTIFIER no está configurado en las variables de entorno');
      }
      
      console.log('🗄️ Cluster ID:', clusterIdentifier);

      // Create CloudWatch client
      const cloudwatch = new CloudWatchClient({
        region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
        credentials: {
          accessKeyId: credentials.accessKeyId,
          secretAccessKey: credentials.secretAccessKey,
          sessionToken: credentials.sessionToken
        }
      });

      const now = new Date();
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

      // Query ServerlessDatabaseCapacity metric (most reliable for pause detection)
      const capacityCommand = new GetMetricStatisticsCommand({
        Namespace: 'AWS/RDS',
        MetricName: 'ServerlessDatabaseCapacity',
        Dimensions: [
          {
            Name: 'DBClusterIdentifier',
            Value: clusterIdentifier
          }
        ],
        StartTime: fiveMinutesAgo,
        EndTime: now,
        Period: 60,
        Statistics: ['Average']
      });

      console.log('📊 Querying ServerlessDatabaseCapacity...');
      const capacityResponse = await cloudwatch.send(capacityCommand);
      console.log('📊 Capacity response:', capacityResponse);
      console.log('📊 Datapoints:', capacityResponse.Datapoints);
      
      const latestCapacity = capacityResponse.Datapoints && capacityResponse.Datapoints.length > 0
        ? capacityResponse.Datapoints[capacityResponse.Datapoints.length - 1]
        : null;
      
      console.log('📊 Latest capacity datapoint:', latestCapacity);

      // Query ACUUtilization metric
      const acuCommand = new GetMetricStatisticsCommand({
        Namespace: 'AWS/RDS',
        MetricName: 'ACUUtilization',
        Dimensions: [
          {
            Name: 'DBClusterIdentifier',
            Value: clusterIdentifier
          }
        ],
        StartTime: fiveMinutesAgo,
        EndTime: now,
        Period: 60,
        Statistics: ['Average']
      });

      console.log('📊 Querying ACUUtilization...');
      const acuResponse = await cloudwatch.send(acuCommand);
      console.log('📊 ACU response:', acuResponse);
      
      const latestAcu = acuResponse.Datapoints && acuResponse.Datapoints.length > 0
        ? acuResponse.Datapoints[acuResponse.Datapoints.length - 1]
        : null;
      
      console.log('📊 Latest ACU datapoint:', latestAcu);

      // Determine status based on metrics
      // Per AWS docs: Paused instances show 0% for CPUUtilization and ACUUtilization, and 0 for ServerlessDatabaseCapacity
      let status: 'active' | 'paused' | 'unknown' = 'unknown';
      
      if (latestCapacity && latestCapacity.Average !== undefined) {
        status = latestCapacity.Average === 0 ? 'paused' : 'active';
        console.log('✅ Status determined from capacity:', status);
      } else {
        console.warn('⚠️ No capacity datapoints found');
      }

      setDbStatus({
        status,
        cpuUtilization: null, // Not querying CPU to reduce API calls
        acuUtilization: latestAcu?.Average ?? null,
        serverlessCapacity: latestCapacity?.Average ?? null,
        lastUpdated: new Date()
      });

      console.log('✅ Database status updated:', {
        status,
        capacity: latestCapacity?.Average,
        acu: latestAcu?.Average
      });

    } catch (err: any) {
      console.error('❌ Error checking database status:', err);
      console.error('❌ Error details:', {
        name: err instanceof Error ? err.name : 'Unknown',
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : undefined,
        fullError: err,
        // Log AWS SDK specific error details
        $metadata: err?.$metadata,
        $response: err?.$response
      });
      
      // Handle specific error types
      let errorMessage = 'Error al verificar el estado de la base de datos';
      
      if (err instanceof Error) {
        // Check for CloudWatch deserialization errors (invalid cluster ID or bad request)
        if (err.message.includes('Deserialization error') || err.message.includes("Cannot read properties of undefined (reading 'Type')")) {
          errorMessage = 'Error al consultar CloudWatch. Verifica que VITE_DB_CLUSTER_IDENTIFIER sea correcto y que el cluster exista.';
        }
        // Check for database resuming error
        else if (err.message.includes('DatabaseResumingException') || err.message.includes('Database error')) {
          errorMessage = 'La base de datos se está reanudando. Por favor, intenta de nuevo en 30-45 segundos.';
        } 
        // Check for CloudWatch permission errors
        else if (err.message.includes('AccessDenied') || err.message.includes('not authorized')) {
          errorMessage = 'No tienes permisos para acceder a las métricas de CloudWatch. Verifica la configuración de IAM.';
        }
        // Check for missing cluster identifier
        else if (err.message.includes('VITE_DB_CLUSTER_IDENTIFIER')) {
          errorMessage = err.message;
        }
        // Generic error
        else {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Check status on mount
  useEffect(() => {
    checkDatabaseStatus();
  }, []);

  const getStatusIndicator = () => {
    if (loading || dbStatus.status === 'loading') {
      return <StatusIndicator type="loading">Verificando...</StatusIndicator>;
    }

    switch (dbStatus.status) {
      case 'active':
        return <StatusIndicator type="success">Activa</StatusIndicator>;
      case 'paused':
        return <StatusIndicator type="stopped">Pausada</StatusIndicator>;
      default:
        return <StatusIndicator type="info">Desconocido</StatusIndicator>;
    }
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Estado en tiempo real de Aurora Serverless v2"
          actions={
            <Button
              iconName="refresh"
              loading={loading}
              onClick={checkDatabaseStatus}
            >
              Actualizar Estado
            </Button>
          }
        >
          Estado de Base de Datos
        </Header>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Box variant="p" color="text-status-error">
            {error}
          </Box>
        )}

        <ColumnLayout columns={2} variant="text-grid">
          <KeyValuePairs
            columns={1}
            items={[
              {
                label: 'Estado Actual',
                value: getStatusIndicator()
              },
              {
                label: 'Capacidad Actual (ACU)',
                value: dbStatus.serverlessCapacity !== null 
                  ? `${dbStatus.serverlessCapacity} ACU` 
                  : 'N/A'
              },
              {
                label: 'Utilización ACU',
                value: dbStatus.acuUtilization !== null 
                  ? `${dbStatus.acuUtilization.toFixed(2)}%` 
                  : 'N/A'
              },
              {
                label: 'Última Actualización',
                value: dbStatus.lastUpdated 
                  ? dbStatus.lastUpdated.toLocaleTimeString('es-MX') 
                  : 'N/A'
              }
            ]}
          />
        </ColumnLayout>

        {dbStatus.status === 'paused' && (
          <Box variant="p" color="text-status-info">
            La base de datos está pausada. Se reanudará automáticamente con la próxima consulta (puede tardar 30-45 segundos).
          </Box>
        )}
      </SpaceBetween>
    </Container>
  );
}

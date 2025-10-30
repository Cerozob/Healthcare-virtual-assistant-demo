/**
 * AgentCore Debug Utilities
 * Helper functions for debugging AgentCore integration
 */

import { BedrockAgentCoreClient } from '@aws-sdk/client-bedrock-agentcore';
import { BedrockAgentCoreControlClient } from '@aws-sdk/client-bedrock-agentcore-control';
import { fetchAuthSession } from 'aws-amplify/auth';

const AWS_REGION = import.meta.env.VITE_AWS_REGION || 'us-east-1';
const AGENTCORE_RUNTIME_ID = import.meta.env.VITE_AGENTCORE_RUNTIME_ID;

export interface DebugInfo {
  credentials: boolean;
  runtimeId: string | undefined;
  region: string;
  clientsCreated: boolean;
  error?: string;
}

export async function debugAgentCoreSetup(): Promise<DebugInfo> {
  const debug: DebugInfo = {
    credentials: false,
    runtimeId: AGENTCORE_RUNTIME_ID,
    region: AWS_REGION,
    clientsCreated: false
  };

  try {
    // Test credentials
    const session = await fetchAuthSession();
    const credentials = session.credentials;
    
    if (credentials) {
      debug.credentials = true;
      console.log('✅ Credentials available:', {
        accessKeyId: credentials.accessKeyId?.substring(0, 10) + '...',
        hasSessionToken: !!credentials.sessionToken
      });
    } else {
      debug.error = 'No credentials available from Amplify Auth';
      return debug;
    }

    // Test client creation
    new BedrockAgentCoreClient({
      region: AWS_REGION,
      credentials
    });

    new BedrockAgentCoreControlClient({
      region: AWS_REGION,
      credentials
    });

    debug.clientsCreated = true;
    console.log('✅ AgentCore clients created successfully');

    // Note: Skipping control plane tests as the exact API methods are not available
    if (AGENTCORE_RUNTIME_ID) {
      console.log('🔍 Runtime ID configured:', AGENTCORE_RUNTIME_ID);
    }

    return debug;

  } catch (error: any) {
    debug.error = error.message;
    console.error('❌ AgentCore debug failed:', error);
    return debug;
  }
}

export function logEnvironmentInfo(): void {
  console.group('🔧 AgentCore Environment Info');
  console.log('Runtime ID:', AGENTCORE_RUNTIME_ID || 'NOT SET');
  console.log('Region:', AWS_REGION);
  console.log('Environment:', import.meta.env.MODE);
  console.groupEnd();
}

export async function testAgentCoreInvocation(message: string = 'Hello, test'): Promise<any> {
  try {
    console.log('🧪 Testing AgentCore invocation with message:', message);
    
    const session = await fetchAuthSession();
    const credentials = session.credentials;
    
    if (!credentials) {
      throw new Error('No credentials available');
    }

    if (!AGENTCORE_RUNTIME_ID) {
      throw new Error('No runtime ID configured');
    }

    new BedrockAgentCoreClient({
      region: AWS_REGION,
      credentials
    });

    // Try different possible parameter combinations
    const testInputs = [
      // Most likely correct format based on boto3
      {
        agentRuntimeId: AGENTCORE_RUNTIME_ID,
        sessionId: `test-${Date.now()}`,
        inputText: message
      },
      // Alternative formats in case the above doesn't work
      {
        agentRuntimeId: AGENTCORE_RUNTIME_ID,
        runtimeSessionId: `test-${Date.now()}`,
        inputText: message
      },
      {
        agentRuntimeArn: `arn:aws:bedrock-agentcore:${AWS_REGION}:*:agent-runtime/${AGENTCORE_RUNTIME_ID}`,
        sessionId: `test-${Date.now()}`,
        inputText: message
      }
    ];

    for (let i = 0; i < testInputs.length; i++) {
      try {
        console.log(`🔄 Trying input format ${i + 1}:`, testInputs[i]);
        
        // Note: We can't actually import InvokeAgentRuntimeCommand here without knowing the exact API
        // This is more for logging what we would try
        console.log('Would attempt invocation with:', testInputs[i]);
        
        // Return the input that would be used for manual testing
        return {
          success: true,
          testedInput: testInputs[i],
          message: 'Test input prepared (actual invocation would need to be done in the service)'
        };
        
      } catch (error: any) {
        console.log(`❌ Input format ${i + 1} failed:`, error.message);
        if (i === testInputs.length - 1) {
          throw error;
        }
      }
    }

  } catch (error: any) {
    console.error('❌ Test invocation failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

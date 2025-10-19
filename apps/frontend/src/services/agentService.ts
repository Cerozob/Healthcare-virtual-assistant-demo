/**
 * Agent Service
 * Service class for agent-related API operations
 */

import { API_ENDPOINTS } from '../config/api';
import type {
  AgentRequest,
  AgentResponse
} from '../types/api';
import { apiClient } from './apiClient';

export class AgentService {
  /**
   * Send query to agent
   */
  async queryAgent(data: AgentRequest): Promise<AgentResponse> {
    return apiClient.post<AgentResponse>(API_ENDPOINTS.agent, data);
  }

  /**
   * Get agent information
   */
  async getAgentInfo(): Promise<any> {
    return apiClient.get<any>(API_ENDPOINTS.agent);
  }
}

// Export singleton instance
export const agentService = new AgentService();

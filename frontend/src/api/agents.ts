/**
 * API client for agent management.
 */
import { apiClient } from './client'
import type { AgentType, Tool } from '@/types/agent'

/**
 * List all available agents.
 */
export async function listAgents(enabledOnly: boolean = true): Promise<AgentType[]> {
  const response = await apiClient.get<AgentType[]>('/agents', {
    params: { enabled_only: enabledOnly }
  })
  return response.data
}

/**
 * Get specific agent configuration.
 */
export async function getAgentConfig(agentName: string): Promise<AgentType> {
  const response = await apiClient.get<AgentType>(`/agents/${agentName}`)
  return response.data
}

/**
 * Get tools assigned to an agent.
 */
export async function getAgentTools(agentId: number, enabledOnly: boolean = true): Promise<Tool[]> {
  const response = await apiClient.get<Tool[]>(`/agents/${agentId}/tools`, {
    params: { enabled_only: enabledOnly }
  })
  return response.data
}

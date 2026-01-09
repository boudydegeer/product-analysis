/**
 * Admin API client for managing agents and tools.
 */
import { apiClient } from './client'

// ===== Types =====

export interface AgentTypeCreate {
  name: string
  display_name: string
  description?: string
  avatar_url?: string
  avatar_color?: string
  personality_traits?: string[]
  model: string
  system_prompt: string
  streaming_enabled?: boolean
  max_context_tokens?: number
  temperature?: number
  enabled?: boolean
  is_default?: boolean
  version?: string
}

export interface AgentTypeUpdate {
  display_name?: string
  description?: string
  avatar_url?: string
  avatar_color?: string
  personality_traits?: string[]
  model?: string
  system_prompt?: string
  streaming_enabled?: boolean
  max_context_tokens?: number
  temperature?: number
  enabled?: boolean
  is_default?: boolean
  version?: string
}

export interface AgentTypeResponse {
  id: number
  name: string
  display_name: string
  description?: string
  avatar_url?: string
  avatar_color: string
  personality_traits: string[]
  model: string
  system_prompt: string
  streaming_enabled: boolean
  max_context_tokens: number
  temperature: number
  enabled: boolean
  is_default: boolean
  version: string
  created_at: string
  updated_at: string
}

export interface ToolCreate {
  name: string
  description: string
  category: string
  tool_type: 'builtin' | 'custom' | 'mcp'
  definition: Record<string, unknown>
  enabled?: boolean
  is_dangerous?: boolean
  requires_approval?: boolean
  version?: string
  tags?: string[]
  example_usage?: string
  created_by?: string
}

export interface ToolUpdate {
  description?: string
  category?: string
  tool_type?: 'builtin' | 'custom' | 'mcp'
  definition?: Record<string, unknown>
  enabled?: boolean
  is_dangerous?: boolean
  requires_approval?: boolean
  version?: string
  tags?: string[]
  example_usage?: string
}

export interface ToolResponse {
  id: number
  name: string
  description: string
  category: string
  tool_type: string
  definition: Record<string, unknown>
  enabled: boolean
  is_dangerous: boolean
  requires_approval: boolean
  version: string
  tags: string[]
  example_usage?: string
  created_at: string
  updated_at: string
  created_by?: string
}

export interface AgentToolAssignment {
  tool_id: number
  enabled_for_agent?: boolean
  order_index?: number
  allow_use?: boolean
  requires_approval?: boolean
  usage_limit?: number
  allowed_parameters?: Record<string, unknown>
  denied_parameters?: Record<string, unknown>
  parameter_defaults?: Record<string, unknown>
}

export interface AgentToolConfigResponse {
  id: number
  agent_type_id: number
  tool_id: number
  enabled_for_agent: boolean
  order_index?: number
  allow_use: boolean
  requires_approval: boolean
  usage_limit?: number
  allowed_parameters?: Record<string, unknown>
  denied_parameters?: Record<string, unknown>
  parameter_defaults?: Record<string, unknown>
  created_at: string
  updated_at: string
}

// ===== Agent Management =====

/**
 * Create a new agent type.
 */
export async function createAgent(data: AgentTypeCreate): Promise<AgentTypeResponse> {
  const response = await apiClient.post<AgentTypeResponse>('/admin/agents', data)
  return response.data
}

/**
 * List all agent types (including disabled).
 */
export async function listAllAgents(): Promise<AgentTypeResponse[]> {
  const response = await apiClient.get<AgentTypeResponse[]>('/admin/agents')
  return response.data
}

/**
 * Get an agent type by ID.
 */
export async function getAgent(agentId: number): Promise<AgentTypeResponse> {
  const response = await apiClient.get<AgentTypeResponse>(`/admin/agents/${agentId}`)
  return response.data
}

/**
 * Update an agent type.
 */
export async function updateAgent(
  agentId: number,
  data: AgentTypeUpdate
): Promise<AgentTypeResponse> {
  const response = await apiClient.put<AgentTypeResponse>(`/admin/agents/${agentId}`, data)
  return response.data
}

/**
 * Delete an agent type.
 */
export async function deleteAgent(agentId: number): Promise<void> {
  await apiClient.delete(`/admin/agents/${agentId}`)
}

// ===== Tool Management =====

/**
 * Create a new tool.
 */
export async function createTool(data: ToolCreate): Promise<ToolResponse> {
  const response = await apiClient.post<ToolResponse>('/admin/tools', data)
  return response.data
}

/**
 * List all tools (including disabled).
 */
export async function listAllTools(): Promise<ToolResponse[]> {
  const response = await apiClient.get<ToolResponse[]>('/admin/tools')
  return response.data
}

/**
 * Get a tool by ID.
 */
export async function getTool(toolId: number): Promise<ToolResponse> {
  const response = await apiClient.get<ToolResponse>(`/admin/tools/${toolId}`)
  return response.data
}

/**
 * Update a tool.
 */
export async function updateTool(toolId: number, data: ToolUpdate): Promise<ToolResponse> {
  const response = await apiClient.put<ToolResponse>(`/admin/tools/${toolId}`, data)
  return response.data
}

/**
 * Delete a tool.
 */
export async function deleteTool(toolId: number): Promise<void> {
  await apiClient.delete(`/admin/tools/${toolId}`)
}

// ===== Agent-Tool Assignments =====

/**
 * Assign a tool to an agent.
 */
export async function assignToolToAgent(
  agentId: number,
  data: AgentToolAssignment
): Promise<AgentToolConfigResponse> {
  const response = await apiClient.post<AgentToolConfigResponse>(
    `/admin/agents/${agentId}/tools`,
    data
  )
  return response.data
}

/**
 * List all tool assignments for an agent.
 */
export async function listAgentToolAssignments(
  agentId: number
): Promise<AgentToolConfigResponse[]> {
  const response = await apiClient.get<AgentToolConfigResponse[]>(
    `/admin/agents/${agentId}/tools`
  )
  return response.data
}

/**
 * Remove a tool assignment from an agent.
 */
export async function removeToolFromAgent(agentId: number, toolId: number): Promise<void> {
  await apiClient.delete(`/admin/agents/${agentId}/tools/${toolId}`)
}

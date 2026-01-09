/**
 * Admin store for managing agents and tools.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as adminApi from '@/api/admin'
import type {
  AgentTypeResponse,
  AgentTypeCreate,
  AgentTypeUpdate,
  ToolResponse,
  ToolCreate,
  ToolUpdate,
  AgentToolAssignment,
  AgentToolConfigResponse,
} from '@/api/admin'

export const useAdminStore = defineStore('admin', () => {
  // State
  const agents = ref<AgentTypeResponse[]>([])
  const tools = ref<ToolResponse[]>([])
  const agentToolConfigs = ref<Record<number, AgentToolConfigResponse[]>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const enabledAgents = computed(() => agents.value.filter((a) => a.enabled))
  const disabledAgents = computed(() => agents.value.filter((a) => !a.enabled))
  const enabledTools = computed(() => tools.value.filter((t) => t.enabled))
  const disabledTools = computed(() => tools.value.filter((t) => !t.enabled))

  const toolsByCategory = computed(() => {
    const grouped: Record<string, ToolResponse[]> = {}
    for (const tool of tools.value) {
      if (!grouped[tool.category]) {
        grouped[tool.category] = []
      }
      grouped[tool.category].push(tool)
    }
    return grouped
  })

  // Agent Actions
  async function fetchAgents() {
    loading.value = true
    error.value = null

    try {
      agents.value = await adminApi.listAllAgents()
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch agents'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data: AgentTypeCreate) {
    loading.value = true
    error.value = null

    try {
      const agent = await adminApi.createAgent(data)
      agents.value.push(agent)
      return agent
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create agent'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(agentId: number, data: AgentTypeUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await adminApi.updateAgent(agentId, data)

      // Update in list
      const index = agents.value.findIndex((a) => a.id === agentId)
      if (index !== -1) {
        agents.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update agent'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(agentId: number) {
    loading.value = true
    error.value = null

    try {
      await adminApi.deleteAgent(agentId)

      // Remove from list
      agents.value = agents.value.filter((a) => a.id !== agentId)

      // Remove tool configs
      delete agentToolConfigs.value[agentId]
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete agent'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function toggleAgentEnabled(agentId: number) {
    const agent = agents.value.find((a) => a.id === agentId)
    if (!agent) return

    await updateAgent(agentId, { enabled: !agent.enabled })
  }

  // Tool Actions
  async function fetchTools() {
    loading.value = true
    error.value = null

    try {
      tools.value = await adminApi.listAllTools()
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch tools'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTool(data: ToolCreate) {
    loading.value = true
    error.value = null

    try {
      const tool = await adminApi.createTool(data)
      tools.value.push(tool)
      return tool
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create tool'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTool(toolId: number, data: ToolUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await adminApi.updateTool(toolId, data)

      // Update in list
      const index = tools.value.findIndex((t) => t.id === toolId)
      if (index !== -1) {
        tools.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update tool'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTool(toolId: number) {
    loading.value = true
    error.value = null

    try {
      await adminApi.deleteTool(toolId)

      // Remove from list
      tools.value = tools.value.filter((t) => t.id !== toolId)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete tool'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function toggleToolEnabled(toolId: number) {
    const tool = tools.value.find((t) => t.id === toolId)
    if (!tool) return

    await updateTool(toolId, { enabled: !tool.enabled })
  }

  // Agent-Tool Assignment Actions
  async function fetchAgentToolAssignments(agentId: number) {
    loading.value = true
    error.value = null

    try {
      const configs = await adminApi.listAgentToolAssignments(agentId)
      agentToolConfigs.value[agentId] = configs
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch tool assignments'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function assignToolToAgent(agentId: number, data: AgentToolAssignment) {
    loading.value = true
    error.value = null

    try {
      const config = await adminApi.assignToolToAgent(agentId, data)

      // Add to configs
      if (!agentToolConfigs.value[agentId]) {
        agentToolConfigs.value[agentId] = []
      }
      agentToolConfigs.value[agentId].push(config)

      return config
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to assign tool'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function removeToolFromAgent(agentId: number, toolId: number) {
    loading.value = true
    error.value = null

    try {
      await adminApi.removeToolFromAgent(agentId, toolId)

      // Remove from configs
      if (agentToolConfigs.value[agentId]) {
        agentToolConfigs.value[agentId] = agentToolConfigs.value[agentId].filter(
          (c) => c.tool_id !== toolId
        )
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to remove tool'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  function getAgentToolConfigs(agentId: number): AgentToolConfigResponse[] {
    return agentToolConfigs.value[agentId] || []
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    agents,
    tools,
    agentToolConfigs,
    loading,
    error,
    // Getters
    enabledAgents,
    disabledAgents,
    enabledTools,
    disabledTools,
    toolsByCategory,
    // Agent Actions
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    toggleAgentEnabled,
    // Tool Actions
    fetchTools,
    createTool,
    updateTool,
    deleteTool,
    toggleToolEnabled,
    // Assignment Actions
    fetchAgentToolAssignments,
    assignToolToAgent,
    removeToolFromAgent,
    getAgentToolConfigs,
    // Utility
    clearError,
  }
})

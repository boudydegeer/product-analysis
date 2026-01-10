import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { brainstormsApi } from '@/api/brainstorms'
import { getAgentConfig } from '@/api/agents'
import type {
  BrainstormSession,
  BrainstormSessionCreate,
  BrainstormSessionUpdate,
  Message,
  Block,
  ToolExecution,
} from '@/types/brainstorm'
import type { AgentType } from '@/types/agent'

export const useBrainstormStore = defineStore('brainstorm', () => {
  // State
  const currentSession = ref<BrainstormSession | null>(null)
  const sessions = ref<BrainstormSession[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Agent config state
  const currentAgentConfig = ref<AgentType | null>(null)
  const agentConfigLoading = ref(false)

  // WebSocket state
  const wsConnected = ref(false)
  const streamingMessageId = ref<string | null>(null)
  const pendingBlocks = ref<Block[]>([])
  const interactiveElementsActive = ref(false)
  const activeToolExecution = ref<ToolExecution | null>(null)

  // Getters
  const isActive = computed(
    () => currentSession.value?.status === 'active' && wsConnected.value
  )

  // Actions
  async function createSession(data: BrainstormSessionCreate) {
    loading.value = true
    error.value = null

    try {
      const session = await brainstormsApi.createSession(data)
      sessions.value.push(session)
      currentSession.value = session
      return session
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to create session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchSessions() {
    loading.value = true
    error.value = null

    try {
      sessions.value = await brainstormsApi.listSessions()
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to fetch sessions'
      error.value = errorMessage
    } finally {
      loading.value = false
    }
  }

  async function fetchSession(id: string) {
    loading.value = true
    error.value = null

    try {
      currentSession.value = await brainstormsApi.getSession(id)
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to fetch session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateSession(id: string, data: BrainstormSessionUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await brainstormsApi.updateSession(id, data)
      currentSession.value = updated

      // Update in sessions list
      const index = sessions.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        sessions.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to update session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteSession(id: string) {
    loading.value = true
    error.value = null

    try {
      await brainstormsApi.deleteSession(id)

      // Remove from sessions list
      sessions.value = sessions.value.filter((s) => s.id !== id)

      if (currentSession.value?.id === id) {
        currentSession.value = null
      }
    } catch (e: unknown) {
      const errorMessage =
        e instanceof Error ? e.message : 'Failed to delete session'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  // WebSocket actions
  function addMessage(message: Message) {
    if (currentSession.value) {
      currentSession.value.messages.push(message)
    }
  }

  function startStreamingMessage(messageId: string) {
    streamingMessageId.value = messageId
    pendingBlocks.value = []
    interactiveElementsActive.value = false
  }

  function appendBlock(block: Block) {
    pendingBlocks.value.push(block)

    // Check if this is an interactive block
    if (block.type === 'button_group' || block.type === 'multi_select') {
      interactiveElementsActive.value = true
    }
  }

  function completeStreamingMessage() {
    if (!streamingMessageId.value || !currentSession.value) {
      return
    }

    // Check if we had interactive blocks
    const hadInteractiveBlocks = pendingBlocks.value.some(
      b => b.type === 'button_group' || b.type === 'multi_select'
    )

    // Create the complete message
    const message: Message = {
      id: streamingMessageId.value,
      session_id: currentSession.value.id,
      role: 'assistant',
      content: {
        blocks: [...pendingBlocks.value],
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    // Add to session messages
    addMessage(message)

    // Clear streaming state
    streamingMessageId.value = null
    pendingBlocks.value = []

    // Keep interactiveElementsActive if we had interactive blocks
    // This will be cleared when user interacts or sends a new message
    if (!hadInteractiveBlocks) {
      interactiveElementsActive.value = false
    }
  }

  function clearInteractiveState() {
    interactiveElementsActive.value = false
  }

  function setWsConnected(connected: boolean) {
    wsConnected.value = connected

    // Clear streaming state if disconnected
    if (!connected) {
      streamingMessageId.value = null
      pendingBlocks.value = []
      interactiveElementsActive.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  async function fetchAgentConfig(agentName: string) {
    agentConfigLoading.value = true
    try {
      currentAgentConfig.value = await getAgentConfig(agentName)
    } catch (error) {
      console.error('[STORE] Failed to fetch agent config:', error)
      // Use default fallback
      currentAgentConfig.value = {
        id: 0,
        name: agentName,
        display_name: 'Claude',
        avatar_url: '🤖',
        avatar_color: '#6366f1',
        personality_traits: [],
        model: 'claude-sonnet-4-5',
        temperature: 0.7,
      }
    } finally {
      agentConfigLoading.value = false
    }
  }

  // Tool execution actions
  function setToolExecuting(execution: ToolExecution) {
    activeToolExecution.value = execution
  }

  function clearToolExecution() {
    activeToolExecution.value = null
  }

  function updateToolExecutionStatus(status: ToolExecution['status'], message?: string) {
    if (activeToolExecution.value) {
      activeToolExecution.value.status = status
      if (message) {
        activeToolExecution.value.message = message
      }
      if (status === 'completed' || status === 'failed') {
        activeToolExecution.value.completed_at = new Date().toISOString()
      }
    }
  }

  return {
    // State
    currentSession,
    sessions,
    loading,
    error,
    currentAgentConfig,
    agentConfigLoading,
    wsConnected,
    streamingMessageId,
    pendingBlocks,
    interactiveElementsActive,
    activeToolExecution,
    // Getters
    isActive,
    // Actions
    createSession,
    fetchSessions,
    fetchSession,
    updateSession,
    deleteSession,
    addMessage,
    startStreamingMessage,
    appendBlock,
    completeStreamingMessage,
    clearInteractiveState,
    setWsConnected,
    clearError,
    fetchAgentConfig,
    setToolExecuting,
    clearToolExecution,
    updateToolExecutionStatus,
  }
})

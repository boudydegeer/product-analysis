import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { brainstormsApi } from '@/api/brainstorms'
import type {
  BrainstormSession,
  BrainstormSessionCreate,
  BrainstormSessionUpdate,
  BrainstormMessage,
} from '@/types/brainstorm'

export const useBrainstormStore = defineStore('brainstorm', () => {
  // State
  const currentSession = ref<BrainstormSession | null>(null)
  const sessions = ref<BrainstormSession[]>([])
  const loading = ref(false)
  const streaming = ref(false)
  const error = ref<string | null>(null)
  const streamingContent = ref('')

  // Getters
  const isActive = computed(() => currentSession.value?.status === 'active')

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

  function setStreaming(value: boolean) {
    streaming.value = value
  }

  function setStreamingContent(content: string) {
    streamingContent.value = content
  }

  function appendStreamingContent(chunk: string) {
    streamingContent.value += chunk
  }

  function clearStreamingContent() {
    streamingContent.value = ''
  }

  function addMessage(message: BrainstormMessage) {
    if (currentSession.value) {
      currentSession.value.messages.push(message)
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    currentSession,
    sessions,
    loading,
    streaming,
    error,
    streamingContent,
    // Getters
    isActive,
    // Actions
    createSession,
    fetchSessions,
    fetchSession,
    updateSession,
    deleteSession,
    setStreaming,
    setStreamingContent,
    appendStreamingContent,
    clearStreamingContent,
    addMessage,
    clearError,
  }
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ideasApi, type ListIdeasParams } from '@/api/ideas'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
  IdeaStatus,
  IdeaPriority,
} from '@/types/idea'

export const useIdeasStore = defineStore('ideas', () => {
  // State
  const ideas = ref<Idea[]>([])
  const currentIdea = ref<Idea | null>(null)
  const loading = ref(false)
  const evaluating = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const ideasByStatus = computed(() => {
    return (status: IdeaStatus) => ideas.value.filter((idea) => idea.status === status)
  })

  const ideasByPriority = computed(() => {
    return (priority: IdeaPriority) => ideas.value.filter((idea) => idea.priority === priority)
  })

  const evaluatedIdeas = computed(() => {
    return ideas.value.filter((idea) => idea.business_value !== null)
  })

  // Actions
  async function createIdea(data: IdeaCreate) {
    loading.value = true
    error.value = null

    try {
      const idea = await ideasApi.createIdea(data)
      ideas.value.push(idea)
      currentIdea.value = idea
      return idea
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchIdeas(params: ListIdeasParams = {}) {
    loading.value = true
    error.value = null

    try {
      ideas.value = await ideasApi.listIdeas(params)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch ideas'
      error.value = errorMessage
    } finally {
      loading.value = false
    }
  }

  async function fetchIdea(id: string) {
    loading.value = true
    error.value = null

    try {
      currentIdea.value = await ideasApi.getIdea(id)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateIdea(id: string, data: IdeaUpdate) {
    loading.value = true
    error.value = null

    try {
      const updated = await ideasApi.updateIdea(id, data)
      currentIdea.value = updated

      // Update in ideas list
      const index = ideas.value.findIndex((i) => i.id === id)
      if (index !== -1) {
        ideas.value[index] = updated
      }

      return updated
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteIdea(id: string) {
    loading.value = true
    error.value = null

    try {
      await ideasApi.deleteIdea(id)

      // Remove from ideas list
      ideas.value = ideas.value.filter((i) => i.id !== id)

      if (currentIdea.value?.id === id) {
        currentIdea.value = null
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete idea'
      error.value = errorMessage
      throw e
    } finally {
      loading.value = false
    }
  }

  async function evaluateIdea(data: IdeaEvaluationRequest): Promise<IdeaEvaluationResponse> {
    evaluating.value = true
    error.value = null

    try {
      const evaluation = await ideasApi.evaluateIdea(data)
      return evaluation
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to evaluate idea'
      error.value = errorMessage
      throw e
    } finally {
      evaluating.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    ideas,
    currentIdea,
    loading,
    evaluating,
    error,
    // Getters
    ideasByStatus,
    ideasByPriority,
    evaluatedIdeas,
    // Actions
    createIdea,
    fetchIdeas,
    fetchIdea,
    updateIdea,
    deleteIdea,
    evaluateIdea,
    clearError,
  }
})

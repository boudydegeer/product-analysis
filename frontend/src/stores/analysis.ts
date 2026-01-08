import { defineStore } from 'pinia'
import { ref } from 'vue'
import { featuresApi } from '../api/features'
import type { AnalysisResponse, AnalysisDetail } from '../types/analysis'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const currentAnalysis = ref<AnalysisResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchAnalysis(featureId: string) {
    loading.value = true
    error.value = null

    try {
      const response = await featuresApi.getAnalysis(featureId)
      currentAnalysis.value = response
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch analysis'
      currentAnalysis.value = null
    } finally {
      loading.value = false
    }
  }

  function clearAnalysis() {
    currentAnalysis.value = null
    error.value = null
  }

  // Getters
  function isCompleted(analysis: AnalysisResponse | null): analysis is AnalysisDetail {
    return analysis?.status === 'completed'
  }

  return {
    // State
    currentAnalysis,
    loading,
    error,
    // Actions
    fetchAnalysis,
    clearAnalysis,
    // Getters
    isCompleted,
  }
})

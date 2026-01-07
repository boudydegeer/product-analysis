import { defineStore } from 'pinia'
import { ref } from 'vue'
import { featureApi } from '@/services/api'
import type { Feature, FeatureCreate } from '@/types/feature'

export const useFeaturesStore = defineStore('features', () => {
  const features = ref<Feature[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFeatures() {
    loading.value = true
    error.value = null
    try {
      features.value = await featureApi.list()
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to fetch features'
      error.value = errorMessage
      console.error('Error fetching features:', e)
    } finally {
      loading.value = false
    }
  }

  async function createFeature(data: FeatureCreate) {
    loading.value = true
    error.value = null
    try {
      const newFeature = await featureApi.create(data)
      features.value.push(newFeature)
      return newFeature
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create feature'
      error.value = errorMessage
      console.error('Error creating feature:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteFeature(id: string) {
    loading.value = true
    error.value = null
    try {
      await featureApi.delete(id)
      features.value = features.value.filter(f => f.id !== id)
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete feature'
      error.value = errorMessage
      console.error('Error deleting feature:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function triggerAnalysis(id: string) {
    loading.value = true
    error.value = null
    try {
      await featureApi.triggerAnalysis(id)
      // Refresh feature to get updated status
      const updated = await featureApi.get(id)
      const index = features.value.findIndex(f => f.id === id)
      if (index !== -1) {
        features.value[index] = updated
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to trigger analysis'
      error.value = errorMessage
      console.error('Error triggering analysis:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    features,
    loading,
    error,
    fetchFeatures,
    createFeature,
    deleteFeature,
    triggerAnalysis,
  }
})

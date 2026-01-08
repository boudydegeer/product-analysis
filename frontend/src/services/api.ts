import axios from 'axios'
import type { Feature, FeatureCreate, FeatureUpdate } from '@/types/feature'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8891/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const featureApi = {
  // List all features
  list: async (): Promise<Feature[]> => {
    const response = await api.get('/features/')
    return response.data
  },

  // Get single feature
  get: async (id: string): Promise<Feature> => {
    const response = await api.get(`/features/${id}`)
    return response.data
  },

  // Create new feature
  create: async (data: FeatureCreate): Promise<Feature> => {
    const response = await api.post('/features/', data)
    return response.data
  },

  // Update feature
  update: async (id: string, data: FeatureUpdate): Promise<Feature> => {
    const response = await api.patch(`/features/${id}`, data)
    return response.data
  },

  // Delete feature
  delete: async (id: string): Promise<void> => {
    await api.delete(`/features/${id}`)
  },

  // Trigger analysis
  triggerAnalysis: async (id: string): Promise<void> => {
    await api.post(`/features/${id}/analyze`, {})
  },
}

export default api

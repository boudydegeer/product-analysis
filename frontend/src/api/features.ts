import { apiClient } from './client'
import type { Feature, FeatureCreate, FeatureUpdate } from '../types/feature'
import type { AnalysisResponse } from '../types/analysis'

/**
 * Response type for triggering analysis
 */
interface TriggerAnalysisResponse {
  run_id: number
}

/**
 * Features API client
 */
export const featuresApi = {
  /**
   * List all features
   * GET /api/features/
   */
  async list(): Promise<Feature[]> {
    const response = await apiClient.get<Feature[]>('/features/')
    return response.data
  },

  /**
   * Get a single feature by ID
   * GET /api/features/{id}
   */
  async get(id: string): Promise<Feature> {
    const response = await apiClient.get<Feature>(`/features/${id}`)
    return response.data
  },

  /**
   * Create a new feature
   * POST /api/features/
   */
  async create(data: FeatureCreate): Promise<Feature> {
    const response = await apiClient.post<Feature>('/features/', data)
    return response.data
  },

  /**
   * Update an existing feature
   * PATCH /api/features/{id}
   */
  async update(id: string, data: FeatureUpdate): Promise<Feature> {
    const response = await apiClient.patch<Feature>(`/features/${id}`, data)
    return response.data
  },

  /**
   * Delete a feature
   * DELETE /api/features/{id}
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/features/${id}`)
  },

  /**
   * Trigger analysis for a feature
   * POST /api/features/{id}/analyze
   */
  async triggerAnalysis(id: string): Promise<TriggerAnalysisResponse> {
    const response = await apiClient.post<TriggerAnalysisResponse>(
      `/features/${id}/analyze`,
      {}
    )
    return response.data
  },

  /**
   * Get analysis details for a feature
   * GET /api/features/{id}/analysis
   */
  async getAnalysis(id: string): Promise<AnalysisResponse> {
    const response = await apiClient.get<AnalysisResponse>(`/features/${id}/analysis`)
    return response.data
  },
}

export default featuresApi

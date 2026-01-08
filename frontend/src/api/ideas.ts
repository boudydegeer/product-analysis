import apiClient from './client'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
} from '@/types/idea'

export interface ListIdeasParams {
  status?: string
  priority?: string
  skip?: number
  limit?: number
}

export const ideasApi = {
  /**
   * Create a new idea
   */
  async createIdea(data: IdeaCreate): Promise<Idea> {
    const response = await apiClient.post<Idea>('/ideas/', data)
    return response.data
  },

  /**
   * List all ideas with optional filtering
   */
  async listIdeas(params: ListIdeasParams = {}): Promise<Idea[]> {
    const response = await apiClient.get<Idea[]>('/ideas/', { params })
    return response.data
  },

  /**
   * Get a specific idea
   */
  async getIdea(id: string): Promise<Idea> {
    const response = await apiClient.get<Idea>(`/ideas/${id}`)
    return response.data
  },

  /**
   * Update an idea
   */
  async updateIdea(id: string, data: IdeaUpdate): Promise<Idea> {
    const response = await apiClient.put<Idea>(`/ideas/${id}`, data)
    return response.data
  },

  /**
   * Delete an idea
   */
  async deleteIdea(id: string): Promise<void> {
    await apiClient.delete(`/ideas/${id}`)
  },

  /**
   * Evaluate an idea with AI
   */
  async evaluateIdea(data: IdeaEvaluationRequest): Promise<IdeaEvaluationResponse> {
    const response = await apiClient.post<IdeaEvaluationResponse>('/ideas/evaluate', data)
    return response.data
  },
}

export default ideasApi

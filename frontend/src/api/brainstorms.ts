import apiClient from './client'
import type {
  BrainstormSession,
  BrainstormSessionCreate,
  BrainstormSessionUpdate,
} from '@/types/brainstorm'

export const brainstormsApi = {
  /**
   * Create a new brainstorm session
   */
  async createSession(data: BrainstormSessionCreate): Promise<BrainstormSession> {
    const response = await apiClient.post<BrainstormSession>('/brainstorms/', data)
    return response.data
  },

  /**
   * List all brainstorm sessions
   */
  async listSessions(): Promise<BrainstormSession[]> {
    const response = await apiClient.get<BrainstormSession[]>('/brainstorms/')
    return response.data
  },

  /**
   * Get a specific brainstorm session
   */
  async getSession(id: string): Promise<BrainstormSession> {
    const response = await apiClient.get<BrainstormSession>(`/brainstorms/${id}`)
    return response.data
  },

  /**
   * Update a brainstorm session
   */
  async updateSession(
    id: string,
    data: BrainstormSessionUpdate
  ): Promise<BrainstormSession> {
    const response = await apiClient.put<BrainstormSession>(`/brainstorms/${id}`, data)
    return response.data
  },

  /**
   * Delete a brainstorm session
   */
  async deleteSession(id: string): Promise<void> {
    await apiClient.delete(`/brainstorms/${id}`)
  },

  /**
   * Create EventSource for streaming brainstorm
   */
  streamBrainstorm(sessionId: string, message: string): EventSource {
    const baseUrl = apiClient.defaults.baseURL || 'http://localhost:8891/api/v1'
    const url = `${baseUrl}/brainstorms/${sessionId}/stream?message=${encodeURIComponent(message)}`
    return new EventSource(url)
  },
}

export default brainstormsApi

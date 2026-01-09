import { describe, it, expect, beforeEach, vi } from 'vitest'
import { brainstormsApi } from '../brainstorms'
import apiClient from '../client'

vi.mock('../client')

describe('Brainstorms API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create a session', async () => {
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockSession })

    const result = await brainstormsApi.createSession({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockSession)
    expect(apiClient.post).toHaveBeenCalledWith('/brainstorms/', {
      title: 'Test',
      description: 'Test desc',
    })
  })

  it('should list sessions', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Session 1',
        description: 'Desc 1',
        status: 'active' as const,
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSessions })

    const result = await brainstormsApi.listSessions()

    expect(result).toEqual(mockSessions)
    expect(apiClient.get).toHaveBeenCalledWith('/brainstorms/')
  })

  it('should get a session by id', async () => {
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSession })

    const result = await brainstormsApi.getSession('session-1')

    expect(result).toEqual(mockSession)
    expect(apiClient.get).toHaveBeenCalledWith('/brainstorms/session-1')
  })
})

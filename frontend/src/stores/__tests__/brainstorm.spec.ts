import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBrainstormStore } from '../brainstorm'
import { brainstormsApi } from '@/api/brainstorms'

vi.mock('@/api/brainstorms')

describe('Brainstorm Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should create a session', async () => {
    const store = useBrainstormStore()
    const mockSession = {
      id: 'session-1',
      title: 'Test',
      description: 'Test desc',
      status: 'active' as const,
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(brainstormsApi.createSession).mockResolvedValue(mockSession)

    await store.createSession({ title: 'Test', description: 'Test desc' })

    expect(store.currentSession).toEqual(mockSession)
    expect(store.sessions).toHaveLength(1)
  })

  it('should fetch sessions', async () => {
    const store = useBrainstormStore()
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

    vi.mocked(brainstormsApi.listSessions).mockResolvedValue(mockSessions)

    await store.fetchSessions()

    expect(store.sessions).toEqual(mockSessions)
    expect(store.loading).toBe(false)
  })

  it('should handle errors', async () => {
    const store = useBrainstormStore()
    vi.mocked(brainstormsApi.listSessions).mockRejectedValue(new Error('Failed'))

    await store.fetchSessions()

    expect(store.error).toBe('Failed')
    expect(store.loading).toBe(false)
  })

  it('should set streaming state', () => {
    const store = useBrainstormStore()

    store.setStreaming(true)
    expect(store.streaming).toBe(true)

    store.setStreaming(false)
    expect(store.streaming).toBe(false)
  })
})

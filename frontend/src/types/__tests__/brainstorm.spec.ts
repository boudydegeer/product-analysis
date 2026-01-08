import { describe, it, expect } from 'vitest'
import type {
  BrainstormSession,
  BrainstormMessage,
  BrainstormSessionCreate,
  MessageRole,
  BrainstormSessionStatus,
} from '../brainstorm'

describe('Brainstorm Types', () => {
  it('should define BrainstormSession type correctly', () => {
    const session: BrainstormSession = {
      id: 'session-1',
      title: 'Test Session',
      description: 'Test description',
      status: 'active',
      messages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(session.id).toBe('session-1')
    expect(session.status).toBe('active')
  })

  it('should define BrainstormMessage type correctly', () => {
    const message: BrainstormMessage = {
      id: 'msg-1',
      session_id: 'session-1',
      role: 'user',
      content: 'Hello',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(message.role).toBe('user')
    expect(message.content).toBe('Hello')
  })

  it('should define BrainstormSessionCreate type correctly', () => {
    const create: BrainstormSessionCreate = {
      title: 'New Session',
      description: 'New description',
    }

    expect(create.title).toBe('New Session')
  })
})

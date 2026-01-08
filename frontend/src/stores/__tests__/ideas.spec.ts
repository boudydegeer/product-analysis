import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIdeasStore } from '../ideas'
import { ideasApi } from '@/api/ideas'

vi.mock('@/api/ideas')

describe('Ideas Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should create an idea', async () => {
    const store = useIdeasStore()
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test desc',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: null,
      technical_complexity: null,
      estimated_effort: null,
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    vi.mocked(ideasApi.createIdea).mockResolvedValue(mockIdea)

    await store.createIdea({ title: 'Test Idea', description: 'Test desc' })

    expect(store.ideas).toHaveLength(1)
    expect(store.ideas[0]).toEqual(mockIdea)
  })

  it('should fetch ideas', async () => {
    const store = useIdeasStore()
    const mockIdeas = [
      {
        id: 'idea-1',
        title: 'Idea 1',
        description: 'Desc 1',
        status: 'backlog' as const,
        priority: 'medium' as const,
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(ideasApi.listIdeas).mockResolvedValue(mockIdeas)

    await store.fetchIdeas()

    expect(store.ideas).toEqual(mockIdeas)
    expect(store.loading).toBe(false)
  })

  it('should evaluate an idea', async () => {
    const store = useIdeasStore()
    const mockEvaluation = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    vi.mocked(ideasApi.evaluateIdea).mockResolvedValue(mockEvaluation)

    const result = await store.evaluateIdea({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockEvaluation)
    expect(store.evaluating).toBe(false)
  })

  it('should filter ideas by status', () => {
    const store = useIdeasStore()
    store.ideas = [
      {
        id: 'idea-1',
        title: 'Idea 1',
        description: 'Desc 1',
        status: 'backlog',
        priority: 'medium',
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 'idea-2',
        title: 'Idea 2',
        description: 'Desc 2',
        status: 'approved',
        priority: 'high',
        business_value: null,
        technical_complexity: null,
        estimated_effort: null,
        market_fit_analysis: null,
        risk_assessment: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const approved = store.ideasByStatus('approved')

    expect(approved).toHaveLength(1)
    expect(approved[0].id).toBe('idea-2')
  })
})

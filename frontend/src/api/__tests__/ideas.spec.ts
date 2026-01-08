import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ideasApi } from '../ideas'
import apiClient from '../client'

vi.mock('../client')

describe('Ideas API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create an idea', async () => {
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

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockIdea })

    const result = await ideasApi.createIdea({
      title: 'Test Idea',
      description: 'Test desc',
    })

    expect(result).toEqual(mockIdea)
    expect(apiClient.post).toHaveBeenCalledWith('/ideas/', {
      title: 'Test Idea',
      description: 'Test desc',
    })
  })

  it('should list ideas', async () => {
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

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockIdeas })

    const result = await ideasApi.listIdeas()

    expect(result).toEqual(mockIdeas)
    expect(apiClient.get).toHaveBeenCalledWith('/ideas/', { params: {} })
  })

  it('should filter ideas by status', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: [] })

    await ideasApi.listIdeas({ status: 'approved' })

    expect(apiClient.get).toHaveBeenCalledWith('/ideas/', {
      params: { status: 'approved' },
    })
  })

  it('should evaluate an idea', async () => {
    const mockEvaluation = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockEvaluation })

    const result = await ideasApi.evaluateIdea({
      title: 'Test',
      description: 'Test desc',
    })

    expect(result).toEqual(mockEvaluation)
    expect(apiClient.post).toHaveBeenCalledWith('/ideas/evaluate', {
      title: 'Test',
      description: 'Test desc',
    })
  })
})

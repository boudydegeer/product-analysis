import { describe, it, expect } from 'vitest'
import type {
  Idea,
  IdeaCreate,
  IdeaUpdate,
  IdeaStatus,
  IdeaPriority,
  IdeaEvaluationRequest,
  IdeaEvaluationResponse,
} from '../idea'

describe('Idea Types', () => {
  it('should define Idea type correctly', () => {
    const idea: Idea = {
      id: 'idea-1',
      title: 'Dark Mode Feature',
      description: 'Add dark mode support',
      status: 'backlog',
      priority: 'medium',
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong demand',
      risk_assessment: 'Low risk',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    expect(idea.id).toBe('idea-1')
    expect(idea.business_value).toBe(8)
  })

  it('should define IdeaCreate type correctly', () => {
    const create: IdeaCreate = {
      title: 'New Idea',
      description: 'New description',
      priority: 'high',
    }

    expect(create.title).toBe('New Idea')
    expect(create.priority).toBe('high')
  })

  it('should define IdeaEvaluationResponse type correctly', () => {
    const evaluation: IdeaEvaluationResponse = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
    }

    expect(evaluation.business_value).toBe(8)
  })
})

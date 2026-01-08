import { describe, it, expect } from 'vitest'
import type {
  AnalysisOverview,
  AnalysisImplementation,
  AnalysisRisks,
  AnalysisRecommendations,
  AnalysisDetail,
  AnalysisStatus,
} from '../types/analysis'

describe('Analysis Types', () => {
  it('should accept valid AnalysisOverview', () => {
    const overview: AnalysisOverview = {
      summary: 'Test summary',
      key_points: ['Point 1', 'Point 2'],
      metrics: {
        complexity: 'medium',
        estimated_effort: '3 days',
        confidence: 0.85,
      },
    }
    expect(overview.summary).toBe('Test summary')
    expect(overview.key_points).toHaveLength(2)
  })

  it('should accept valid AnalysisDetail', () => {
    const detail: AnalysisDetail = {
      feature_id: 'test-123',
      feature_name: 'Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Summary',
        key_points: [],
        metrics: {},
      },
      implementation: {
        architecture: {},
        technical_details: [],
        data_flow: {},
      },
      risks: {
        technical_risks: [],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: [],
      },
      recommendations: {
        improvements: [],
        best_practices: [],
        next_steps: [],
      },
    }
    expect(detail.feature_id).toBe('test-123')
    expect(detail.status).toBe('completed')
  })

  it('should enforce AnalysisStatus literals', () => {
    const statuses: AnalysisStatus[] = ['completed', 'no_analysis', 'failed', 'analyzing']
    expect(statuses).toHaveLength(4)
  })
})

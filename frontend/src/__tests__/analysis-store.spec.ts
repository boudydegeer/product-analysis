import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAnalysisStore } from '../stores/analysis'
import type { AnalysisDetail } from '../types/analysis'

vi.mock('../api/features', () => ({
  featuresApi: {
    getAnalysis: vi.fn(),
  },
}))

describe('Analysis Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should initialize with empty state', () => {
    const store = useAnalysisStore()
    expect(store.currentAnalysis).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should fetch and store analysis', async () => {
    const { featuresApi } = await import('../api/features')
    const mockAnalysis: AnalysisDetail = {
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

    vi.mocked(featuresApi.getAnalysis).mockResolvedValue(mockAnalysis)

    const store = useAnalysisStore()
    await store.fetchAnalysis('test-123')

    expect(store.currentAnalysis).toEqual(mockAnalysis)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('should handle fetch errors', async () => {
    const { featuresApi } = await import('../api/features')
    vi.mocked(featuresApi.getAnalysis).mockRejectedValue(new Error('Network error'))

    const store = useAnalysisStore()
    await store.fetchAnalysis('test-123')

    expect(store.currentAnalysis).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Network error')
  })
})

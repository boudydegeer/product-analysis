import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AnalysisDialog from '../components/analysis/AnalysisDialog.vue'
import { useAnalysisStore } from '../stores/analysis'
import type { AnalysisDetail } from '../types/analysis'

vi.mock('../api/features', () => ({
  featuresApi: {
    getAnalysis: vi.fn(),
  },
}))

describe('Analysis Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should display full analysis flow', async () => {
    const { featuresApi } = await import('../api/features')

    const mockAnalysis: AnalysisDetail = {
      feature_id: 'integration-test',
      feature_name: 'Integration Test Feature',
      analyzed_at: '2026-01-08T10:30:00Z',
      status: 'completed',
      overview: {
        summary: 'Integration test summary',
        key_points: ['Test point 1', 'Test point 2'],
        metrics: {
          complexity: 'medium',
          estimated_effort: '3 days',
          confidence: 0.85,
        },
      },
      implementation: {
        architecture: {
          pattern: 'Test Pattern',
          components: ['Component A'],
        },
        technical_details: [
          {
            category: 'Backend',
            description: 'Test detail',
          },
        ],
        data_flow: {
          description: 'Test flow',
          steps: ['Step 1', 'Step 2'],
        },
      },
      risks: {
        technical_risks: [
          {
            severity: 'high',
            description: 'Test risk',
          },
        ],
        security_concerns: [],
        scalability_issues: [],
        mitigation_strategies: ['Strategy 1'],
      },
      recommendations: {
        improvements: [
          {
            priority: 'high',
            title: 'Test improvement',
            description: 'Improve this',
            effort: '1 day',
          },
        ],
        best_practices: ['Practice 1'],
        next_steps: ['Next step 1'],
      },
    }

    vi.mocked(featuresApi.getAnalysis).mockResolvedValue(mockAnalysis)

    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'integration-test',
        featureName: 'Integration Test Feature',
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    })

    // Wait for async data load and component updates
    await flushPromises()
    await wrapper.vm.$nextTick()

    // Verify the store was called
    expect(featuresApi.getAnalysis).toHaveBeenCalledWith('integration-test')

    // Verify the analysis was loaded into the store
    const analysisStore = useAnalysisStore()
    expect(analysisStore.currentAnalysis).toEqual(mockAnalysis)
  })
})

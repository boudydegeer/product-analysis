import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import DashboardView from '../views/DashboardView.vue'
import { useFeaturesStore } from '../stores/features'

vi.mock('../stores/features', () => ({
  useFeaturesStore: vi.fn()
}))

describe('DashboardView - Analysis Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())

    // Mock store with sample features
    vi.mocked(useFeaturesStore).mockReturnValue({
      features: [
        {
          id: 'FEAT-001',
          name: 'Test Feature 1',
          description: 'Test description',
          status: 'completed',
          priority: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ],
      loading: false,
      error: null,
      fetchFeatures: vi.fn()
    } as any)
  })

  it('should open analysis dialog when feature is clicked', async () => {
    const wrapper = mount(DashboardView)

    // Find and click a feature row
    const featureRow = wrapper.find('[data-testid="feature-row"]')
    expect(featureRow.exists()).toBe(true)

    // Click the feature row
    await featureRow.trigger('click')

    // Wait for next tick to allow state to update
    await wrapper.vm.$nextTick()

    // Verify the dialog component receives the correct props
    const dialog = wrapper.findComponent({ name: 'AnalysisDialog' })
    expect(dialog.exists()).toBe(true)
    expect(dialog.props('open')).toBe(true)
    expect(dialog.props('featureId')).toBe('FEAT-001')
    expect(dialog.props('featureName')).toBe('Test Feature 1')
  })

  it('should show AnalysisDialog component when integrated', () => {
    const wrapper = mount(DashboardView)

    // Once integrated, we should find the AnalysisDialog component
    const dialog = wrapper.findComponent({ name: 'AnalysisDialog' })

    // Dialog component should now exist
    expect(dialog.exists()).toBe(true)
  })
})

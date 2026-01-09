import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import { useFeaturesStore } from '../stores/features'

vi.mock('../stores/features', () => ({
  useFeaturesStore: vi.fn()
}))

// Create a mock router for tests
const createMockRouter = () => {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/',
        name: 'dashboard',
        component: { template: '<div>Dashboard</div>' },
      },
      {
        path: '/analysis/:id',
        name: 'analysis',
        component: { template: '<div>Analysis</div>' },
      },
      {
        path: '/features',
        name: 'features',
        component: { template: '<div>Features</div>' },
      },
    ],
  })
}

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

  it('should navigate to analysis page when feature is clicked', async () => {
    const router = createMockRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    // Find and click a feature row
    const featureRow = wrapper.find('[data-testid="feature-row"]')
    expect(featureRow.exists()).toBe(true)

    // Click the feature row
    await featureRow.trigger('click')

    // Wait for all promises to flush (including router navigation)
    await flushPromises()

    // Verify router navigation was called
    expect(router.currentRoute.value.name).toBe('analysis')
    expect(router.currentRoute.value.params.id).toBe('FEAT-001')
  })

  it('should render feature cards with correct data', async () => {
    const router = createMockRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    // Verify feature data is rendered
    expect(wrapper.text()).toContain('Test Feature 1')
    expect(wrapper.text()).toContain('FEAT-001')
    expect(wrapper.text()).toContain('completed')
  })
})

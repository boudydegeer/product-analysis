import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import App from '../App.vue'

// Mock the API module
vi.mock('@/services/api', () => ({
  featureApi: {
    list: vi.fn().mockResolvedValue([]),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    triggerAnalysis: vi.fn(),
  },
}))

describe('App', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders successfully', () => {
    const wrapper = mount(App, {
      global: {
        plugins: [createPinia()],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders the FeatureList component', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()
    expect(wrapper.findComponent({ name: 'FeatureList' }).exists()).toBe(true)
  })

  it('displays the Product Analysis Platform header', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [createPinia()],
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Product Analysis Platform')
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
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
        path: '/features',
        name: 'features',
        component: { template: '<div>Features</div>' },
      },
    ],
  })
}

describe('App', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders successfully', async () => {
    const router = createMockRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders router-view component', async () => {
    const router = createMockRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })
    await flushPromises()

    // Check that router-view rendered the route component
    expect(wrapper.html()).toContain('Dashboard')
  })

  it('navigates between routes', async () => {
    const router = createMockRouter()
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), router],
      },
    })

    expect(wrapper.html()).toContain('Dashboard')

    // Navigate to features
    await router.push('/features')
    await flushPromises()

    expect(wrapper.html()).toContain('Features')
  })
})

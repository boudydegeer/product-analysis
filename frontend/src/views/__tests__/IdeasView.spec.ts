import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import IdeasView from '../IdeasView.vue'
import { useIdeasStore } from '@/stores/ideas'

// Mock the router
const mockRouter = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/ideas', name: 'ideas', component: { template: '<div>Ideas</div>' } },
    { path: '/ideas/:id', name: 'idea-detail', component: { template: '<div>Detail</div>' } },
  ],
})

vi.mock('@/stores/ideas', () => ({
  useIdeasStore: vi.fn(),
}))

describe('IdeasView', () => {
  let mockStore: any

  beforeEach(() => {
    setActivePinia(createPinia())

    mockStore = {
      ideas: [],
      loading: false,
      evaluating: false,
      createIdea: vi.fn(),
      evaluateIdea: vi.fn(),
      updateIdea: vi.fn(),
      fetchIdeas: vi.fn(),
    }

    vi.mocked(useIdeasStore).mockReturnValue(mockStore)
  })

  it('should render IdeaList component', () => {
    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    expect(wrapper.findComponent({ name: 'IdeaList' }).exists()).toBe(true)
  })

  it('should open create dialog when create-idea event is emitted', async () => {
    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    const ideaList = wrapper.findComponent({ name: 'IdeaList' })
    await ideaList.vm.$emit('create-idea')
    await wrapper.vm.$nextTick()

    const dialog = wrapper.findComponent({ name: 'Dialog' })
    expect(dialog.props('open')).toBe(true)
  })

  it('should navigate to idea detail when select-idea event is emitted', async () => {
    const pushSpy = vi.spyOn(mockRouter, 'push')
    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    const ideaList = wrapper.findComponent({ name: 'IdeaList' })
    await ideaList.vm.$emit('select-idea', 'idea-123')

    expect(pushSpy).toHaveBeenCalledWith('/ideas/idea-123')
  })

  it('should have correct initial form state', async () => {
    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    // Access component instance to check initial state
    const vm = wrapper.vm as any
    expect(vm.formData.title).toBe('')
    expect(vm.formData.description).toBe('')
    expect(vm.formData.priority).toBe('medium')
    expect(vm.evaluateAfterCreate).toBe(true)
    expect(vm.showCreateDialog).toBe(false)
  })

  it('should call createIdea when form is submitted', async () => {
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test description',
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

    mockStore.createIdea.mockResolvedValue(mockIdea)
    const pushSpy = vi.spyOn(mockRouter, 'push')

    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    // Set form data directly on component instance
    const vm = wrapper.vm as any
    vm.formData.title = 'Test Idea'
    vm.formData.description = 'Test description'
    vm.evaluateAfterCreate = false
    vm.showCreateDialog = true

    // Call handleCreate directly
    await vm.handleCreate()
    await flushPromises()

    expect(mockStore.createIdea).toHaveBeenCalledWith({
      title: 'Test Idea',
      description: 'Test description',
      priority: 'medium',
    })
    expect(mockStore.evaluateIdea).not.toHaveBeenCalled()
    expect(pushSpy).toHaveBeenCalledWith('/ideas/idea-1')
  })

  it('should call evaluateIdea when evaluateAfterCreate is true', async () => {
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test description',
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

    const mockEvaluation = {
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong market fit',
      risk_assessment: 'Low risk',
    }

    mockStore.createIdea.mockResolvedValue(mockIdea)
    mockStore.evaluateIdea.mockResolvedValue(mockEvaluation)

    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    // Set form data directly on component instance
    const vm = wrapper.vm as any
    vm.formData.title = 'Test Idea'
    vm.formData.description = 'Test description'
    vm.evaluateAfterCreate = true
    vm.showCreateDialog = true

    // Call handleCreate directly
    await vm.handleCreate()
    await flushPromises()

    expect(mockStore.createIdea).toHaveBeenCalledWith({
      title: 'Test Idea',
      description: 'Test description',
      priority: 'medium',
    })
    expect(mockStore.evaluateIdea).toHaveBeenCalledWith({
      title: 'Test Idea',
      description: 'Test description',
    })
    expect(mockStore.updateIdea).toHaveBeenCalledWith('idea-1', mockEvaluation)
  })

  it('should reset form after successful creation', async () => {
    const mockIdea = {
      id: 'idea-1',
      title: 'Test Idea',
      description: 'Test description',
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

    mockStore.createIdea.mockResolvedValue(mockIdea)

    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    const vm = wrapper.vm as any
    vm.formData.title = 'Test Idea'
    vm.formData.description = 'Test description'
    vm.evaluateAfterCreate = false

    await vm.handleCreate()
    await flushPromises()

    // Form should be reset
    expect(vm.formData.title).toBe('')
    expect(vm.formData.description).toBe('')
    expect(vm.formData.priority).toBe('medium')
    expect(vm.evaluateAfterCreate).toBe(true)
    expect(vm.showCreateDialog).toBe(false)
  })

  it('should handle creation error gracefully', async () => {
    mockStore.createIdea.mockRejectedValue(new Error('Creation failed'))
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const wrapper = mount(IdeasView, {
      global: {
        plugins: [mockRouter],
      },
    })

    const vm = wrapper.vm as any
    vm.formData.title = 'Test Idea'
    vm.formData.description = 'Test description'

    await vm.handleCreate()
    await flushPromises()

    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to create idea:', expect.any(Error))
    consoleErrorSpy.mockRestore()
  })
})

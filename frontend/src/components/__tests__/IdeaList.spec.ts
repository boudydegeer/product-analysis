import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import IdeaList from '../IdeaList.vue'
import { useIdeasStore } from '@/stores/ideas'
import type { Idea } from '@/types/ideas'

// Mock lucide-vue-next icons
vi.mock('lucide-vue-next', () => ({
  Plus: { name: 'Plus', template: '<div>Plus Icon</div>' },
  Lightbulb: { name: 'Lightbulb', template: '<div>Lightbulb Icon</div>' },
}))

// Mock IdeaCard component
vi.mock('../IdeaCard.vue', () => ({
  default: {
    name: 'IdeaCard',
    props: ['idea'],
    template: '<div class="idea-card" @click="$emit(\'click\')">{{ idea.title }}</div>',
  },
}))

// Mock shadcn-vue components
vi.mock('@/components/ui/button', () => ({
  Button: {
    name: 'Button',
    template: '<button><slot /></button>',
  },
}))

vi.mock('@/components/ui/select', () => ({
  Select: {
    name: 'Select',
    props: ['modelValue'],
    template: '<div class="select"><slot /></div>',
  },
  SelectTrigger: {
    name: 'SelectTrigger',
    template: '<div class="select-trigger"><slot /></div>',
  },
  SelectValue: {
    name: 'SelectValue',
    template: '<div class="select-value"><slot /></div>',
  },
  SelectContent: {
    name: 'SelectContent',
    template: '<div class="select-content"><slot /></div>',
  },
  SelectItem: {
    name: 'SelectItem',
    props: ['value'],
    template: '<div class="select-item" :data-value="value"><slot /></div>',
  },
}))

describe('IdeaList', () => {
  let wrapper: VueWrapper<any>
  let store: ReturnType<typeof useIdeasStore>

  const mockIdeas: Idea[] = [
    {
      id: '1',
      title: 'Test Idea 1',
      description: 'Description 1',
      status: 'backlog',
      priority: 'high',
      created_by: 'user1',
      created_at: '2026-01-08T10:00:00Z',
      updated_at: '2026-01-08T10:00:00Z',
    },
    {
      id: '2',
      title: 'Test Idea 2',
      description: 'Description 2',
      status: 'approved',
      priority: 'medium',
      created_by: 'user2',
      created_at: '2026-01-08T11:00:00Z',
      updated_at: '2026-01-08T11:00:00Z',
    },
    {
      id: '3',
      title: 'Test Idea 3',
      description: 'Description 3',
      status: 'backlog',
      priority: 'low',
      created_by: 'user3',
      created_at: '2026-01-08T12:00:00Z',
      updated_at: '2026-01-08T12:00:00Z',
    },
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useIdeasStore()
    store.ideas = []
    store.loading = false
    store.error = null
    // Mock fetchIdeas to prevent actual API calls and manage loading state
    vi.spyOn(store, 'fetchIdeas').mockImplementation(async () => {
      store.loading = false
    })
  })

  describe('Rendering', () => {
    it('renders header with title and New Idea button', () => {
      wrapper = mount(IdeaList)

      expect(wrapper.text()).toContain('Ideas')
      expect(wrapper.text()).toContain('Capture and evaluate product ideas')
      expect(wrapper.text()).toContain('New Idea')
    })

    it('renders filter controls', () => {
      wrapper = mount(IdeaList)

      const selects = wrapper.findAll('.select')
      expect(selects).toHaveLength(2)
    })

    it('renders loading state when loading is true', () => {
      store.loading = true
      wrapper = mount(IdeaList)

      expect(wrapper.text()).toContain('Loading ideas...')
    })

    it('renders error state when error exists', () => {
      store.error = 'Failed to load ideas'
      wrapper = mount(IdeaList)

      expect(wrapper.text()).toContain('Failed to load ideas')
      expect(wrapper.text()).toContain('Retry')
    })

    it('renders empty state when no ideas exist', () => {
      wrapper = mount(IdeaList)

      expect(wrapper.text()).toContain('No Ideas Yet')
      expect(wrapper.text()).toContain('Start capturing product ideas and evaluate them with AI')
      expect(wrapper.text()).toContain('Create Your First Idea')
    })

    it('renders ideas grid when ideas exist', () => {
      store.ideas = mockIdeas
      wrapper = mount(IdeaList)

      const ideaCards = wrapper.findAll('.idea-card')
      expect(ideaCards).toHaveLength(3)
      expect(wrapper.text()).toContain('Test Idea 1')
      expect(wrapper.text()).toContain('Test Idea 2')
      expect(wrapper.text()).toContain('Test Idea 3')
    })
  })

  describe('Filtering', () => {
    beforeEach(() => {
      store.ideas = mockIdeas
    })

    it('shows all ideas by default', () => {
      wrapper = mount(IdeaList)

      const ideaCards = wrapper.findAll('.idea-card')
      expect(ideaCards).toHaveLength(3)
    })

    it('filters ideas by status', async () => {
      wrapper = mount(IdeaList)
      await wrapper.vm.$nextTick()

      // Change status filter to 'approved'
      wrapper.vm.statusFilter = 'approved'
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick() // Wait for computed to update

      const ideaCards = wrapper.findAll('.idea-card')
      expect(ideaCards).toHaveLength(1)
      expect(wrapper.text()).toContain('Test Idea 2')
      expect(wrapper.text()).not.toContain('Test Idea 1')
      expect(wrapper.text()).not.toContain('Test Idea 3')
    })

    it('filters ideas by priority', async () => {
      wrapper = mount(IdeaList)
      await wrapper.vm.$nextTick()

      // Change priority filter to 'high'
      wrapper.vm.priorityFilter = 'high'
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick() // Wait for computed to update

      const ideaCards = wrapper.findAll('.idea-card')
      expect(ideaCards).toHaveLength(1)
      expect(wrapper.text()).toContain('Test Idea 1')
      expect(wrapper.text()).not.toContain('Test Idea 2')
      expect(wrapper.text()).not.toContain('Test Idea 3')
    })

    it('filters ideas by both status and priority', async () => {
      wrapper = mount(IdeaList)
      await wrapper.vm.$nextTick()

      // Change filters to status='backlog' and priority='high'
      wrapper.vm.statusFilter = 'backlog'
      wrapper.vm.priorityFilter = 'high'
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick() // Wait for computed to update

      const ideaCards = wrapper.findAll('.idea-card')
      expect(ideaCards).toHaveLength(1)
      expect(wrapper.text()).toContain('Test Idea 1')
    })

    it('shows empty state when filters result in no ideas', async () => {
      wrapper = mount(IdeaList)
      await wrapper.vm.$nextTick()

      // Set filters that won't match any ideas
      wrapper.vm.statusFilter = 'approved'
      wrapper.vm.priorityFilter = 'low'
      await wrapper.vm.$nextTick()
      await wrapper.vm.$nextTick() // Wait for computed to update

      expect(wrapper.text()).toContain('No Ideas Yet')
    })
  })

  describe('Events', () => {
    beforeEach(() => {
      store.ideas = mockIdeas
    })

    it('emits create-idea event when New Idea button is clicked', async () => {
      wrapper = mount(IdeaList)

      const buttons = wrapper.findAll('button')
      const newIdeaButton = buttons[0]
      await newIdeaButton.trigger('click')

      expect(wrapper.emitted('create-idea')).toBeTruthy()
      expect(wrapper.emitted('create-idea')).toHaveLength(1)
    })

    it('emits create-idea event when Create Your First Idea button is clicked', async () => {
      wrapper = mount(IdeaList)

      const buttons = wrapper.findAll('button')
      const createFirstButton = buttons[buttons.length - 1]
      await createFirstButton.trigger('click')

      expect(wrapper.emitted('create-idea')).toBeTruthy()
    })

    it('emits select-idea event when an idea card is clicked', async () => {
      wrapper = mount(IdeaList)

      const ideaCards = wrapper.findAll('.idea-card')
      await ideaCards[0].trigger('click')

      expect(wrapper.emitted('select-idea')).toBeTruthy()
      expect(wrapper.emitted('select-idea')?.[0]).toEqual(['1'])
    })
  })

  describe('Lifecycle', () => {
    it('fetches ideas on mount', async () => {
      const fetchSpy = vi.spyOn(store, 'fetchIdeas')
      wrapper = mount(IdeaList)

      await wrapper.vm.$nextTick()

      expect(fetchSpy).toHaveBeenCalled()
    })

    it('refetches ideas when status filter changes', async () => {
      wrapper = mount(IdeaList)

      const fetchSpy = vi.spyOn(store, 'fetchIdeas')

      wrapper.vm.statusFilter = 'approved'
      await wrapper.vm.$nextTick()

      expect(fetchSpy).toHaveBeenCalledWith({ status: 'approved' })
    })

    it('refetches ideas when priority filter changes', async () => {
      wrapper = mount(IdeaList)

      const fetchSpy = vi.spyOn(store, 'fetchIdeas')

      wrapper.vm.priorityFilter = 'high'
      await wrapper.vm.$nextTick()

      expect(fetchSpy).toHaveBeenCalledWith({ priority: 'high' })
    })

    it('calls fetchIdeas when retry button is clicked', async () => {
      store.error = 'Failed to load ideas'
      const fetchSpy = vi.spyOn(store, 'fetchIdeas')

      wrapper = mount(IdeaList)
      await wrapper.vm.$nextTick()

      // Find the retry button (should be visible when error state is shown)
      const buttons = wrapper.findAll('button')
      const retryButton = buttons.find(btn => btn.text().includes('Retry'))

      expect(retryButton).toBeDefined()
      await retryButton!.trigger('click')

      expect(fetchSpy).toHaveBeenCalled()
    })
  })
})

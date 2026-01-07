import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useFeaturesStore } from '@/stores/features'
import FeatureList from '@/components/FeatureList.vue'
import { FeatureStatus, type Feature, type FeatureCreate } from '@/types/feature'

// Mock the API module
vi.mock('@/services/api', () => ({
  featureApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    triggerAnalysis: vi.fn(),
  },
}))

import { featureApi } from '@/services/api'

const mockFeatures: Feature[] = [
  {
    id: 'FEAT-001',
    name: 'Test Feature 1',
    description: 'Description for feature 1',
    status: FeatureStatus.DRAFT,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'FEAT-002',
    name: 'Test Feature 2',
    description: 'Description for feature 2',
    status: FeatureStatus.ANALYZING,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 'FEAT-003',
    name: 'Test Feature 3',
    description: 'Description for feature 3',
    status: FeatureStatus.ANALYZED,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
]

// ============================================
// PINIA STORE TESTS
// ============================================
describe('useFeaturesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has features array state', () => {
      const store = useFeaturesStore()
      expect(store.features).toEqual([])
      expect(Array.isArray(store.features)).toBe(true)
    })

    it('has loading boolean state', () => {
      const store = useFeaturesStore()
      expect(store.loading).toBe(false)
      expect(typeof store.loading).toBe('boolean')
    })

    it('has error state', () => {
      const store = useFeaturesStore()
      expect(store.error).toBeNull()
    })
  })

  describe('fetchFeatures action', () => {
    it('calls API and updates state with features', async () => {
      const store = useFeaturesStore()
      vi.mocked(featureApi.list).mockResolvedValue(mockFeatures)

      await store.fetchFeatures()

      expect(featureApi.list).toHaveBeenCalledTimes(1)
      expect(store.features).toEqual(mockFeatures)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets loading to true while fetching', async () => {
      const store = useFeaturesStore()
      let loadingDuringFetch = false

      vi.mocked(featureApi.list).mockImplementation(async () => {
        loadingDuringFetch = store.loading
        return mockFeatures
      })

      await store.fetchFeatures()

      expect(loadingDuringFetch).toBe(true)
    })

    it('sets error on API failure', async () => {
      const store = useFeaturesStore()
      vi.mocked(featureApi.list).mockRejectedValue(new Error('Network error'))

      await store.fetchFeatures()

      expect(store.error).toBe('Network error')
      expect(store.features).toEqual([])
      expect(store.loading).toBe(false)
    })
  })

  describe('createFeature action', () => {
    it('calls API and adds feature to list', async () => {
      const store = useFeaturesStore()
      const newFeatureData: FeatureCreate = {
        id: 'FEAT-004',
        name: 'New Feature',
        description: 'New feature description',
      }
      const createdFeature: Feature = {
        ...newFeatureData,
        status: FeatureStatus.DRAFT,
        created_at: '2024-01-04T00:00:00Z',
        updated_at: '2024-01-04T00:00:00Z',
      }

      vi.mocked(featureApi.create).mockResolvedValue(createdFeature)

      const result = await store.createFeature(newFeatureData)

      expect(featureApi.create).toHaveBeenCalledWith(newFeatureData)
      expect(store.features).toContainEqual(createdFeature)
      expect(result).toEqual(createdFeature)
    })

    it('sets error on create failure', async () => {
      const store = useFeaturesStore()
      vi.mocked(featureApi.create).mockRejectedValue(new Error('Create failed'))

      await expect(store.createFeature({
        id: 'FEAT-005',
        name: 'Failed Feature',
        description: 'Will fail',
      })).rejects.toThrow()

      expect(store.error).toBe('Create failed')
    })
  })

  describe('deleteFeature action', () => {
    it('calls API and removes feature from list', async () => {
      const store = useFeaturesStore()
      store.features = [...mockFeatures]

      vi.mocked(featureApi.delete).mockResolvedValue(undefined)

      await store.deleteFeature('FEAT-001')

      expect(featureApi.delete).toHaveBeenCalledWith('FEAT-001')
      expect(store.features.find(f => f.id === 'FEAT-001')).toBeUndefined()
      expect(store.features.length).toBe(2)
    })

    it('sets error on delete failure', async () => {
      const store = useFeaturesStore()
      store.features = [...mockFeatures]
      vi.mocked(featureApi.delete).mockRejectedValue(new Error('Delete failed'))

      await expect(store.deleteFeature('FEAT-001')).rejects.toThrow()

      expect(store.error).toBe('Delete failed')
      // Features should remain unchanged on failure
      expect(store.features.length).toBe(3)
    })
  })

  describe('triggerAnalysis action', () => {
    it('calls API and updates feature status', async () => {
      const store = useFeaturesStore()
      store.features = [...mockFeatures]

      const updatedFeature: Feature = {
        ...mockFeatures[0],
        status: FeatureStatus.ANALYZING,
      }

      vi.mocked(featureApi.triggerAnalysis).mockResolvedValue(undefined)
      vi.mocked(featureApi.get).mockResolvedValue(updatedFeature)

      await store.triggerAnalysis('FEAT-001')

      expect(featureApi.triggerAnalysis).toHaveBeenCalledWith('FEAT-001')
      expect(featureApi.get).toHaveBeenCalledWith('FEAT-001')
      expect(store.features.find(f => f.id === 'FEAT-001')?.status).toBe(FeatureStatus.ANALYZING)
    })

    it('sets error on analysis trigger failure', async () => {
      const store = useFeaturesStore()
      store.features = [...mockFeatures]
      vi.mocked(featureApi.triggerAnalysis).mockRejectedValue(new Error('Analysis failed'))

      await expect(store.triggerAnalysis('FEAT-001')).rejects.toThrow()

      expect(store.error).toBe('Analysis failed')
    })
  })
})

// ============================================
// FEATURELIST COMPONENT TESTS
// ============================================
describe('FeatureList Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mountComponent = () => {
    return mount(FeatureList, {
      global: {
        plugins: [createPinia()],
      },
    })
  }

  describe('loading state', () => {
    it('renders loading state when loading', async () => {
      vi.mocked(featureApi.list).mockImplementation(() => new Promise(() => {})) // Never resolves

      const wrapper = mountComponent()

      // Store should be loading after mount triggers fetchFeatures
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Loading')
    })
  })

  describe('feature list rendering', () => {
    it('renders list of features when loaded', async () => {
      vi.mocked(featureApi.list).mockResolvedValue(mockFeatures)

      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.text()).toContain('Test Feature 1')
      expect(wrapper.text()).toContain('Test Feature 2')
      expect(wrapper.text()).toContain('Test Feature 3')
    })

    it('each feature shows name, status, and id', async () => {
      vi.mocked(featureApi.list).mockResolvedValue(mockFeatures)

      const wrapper = mountComponent()
      await flushPromises()

      // Check first feature
      expect(wrapper.text()).toContain('Test Feature 1')
      expect(wrapper.text()).toContain('FEAT-001')
      expect(wrapper.text()).toContain('draft')

      // Check second feature with analyzing status
      expect(wrapper.text()).toContain('Test Feature 2')
      expect(wrapper.text()).toContain('analyzing')
    })

    it('renders empty state when no features', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([])

      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.text()).toContain('No features')
    })
  })

  describe('New Feature button', () => {
    it('has "New Feature" button', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([])

      const wrapper = mountComponent()
      await flushPromises()

      const newFeatureButton = wrapper.find('button')
      expect(newFeatureButton.exists()).toBe(true)
      expect(newFeatureButton.text()).toContain('New Feature')
    })

    it('shows create form when New Feature button is clicked', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([])

      const wrapper = mountComponent()
      await flushPromises()

      const newFeatureButton = wrapper.find('button')
      await newFeatureButton.trigger('click')

      // Form should appear
      expect(wrapper.find('form').exists()).toBe(true)
      expect(wrapper.find('input').exists()).toBe(true)
    })
  })

  describe('Analyze button', () => {
    it('has "Analyze" button for each feature', async () => {
      vi.mocked(featureApi.list).mockResolvedValue(mockFeatures)

      const wrapper = mountComponent()
      await flushPromises()

      // Count both "Analyze" and "Analyzing..." buttons (one per feature)
      const analyzeButtons = wrapper.findAll('button').filter(btn => {
        const text = btn.text().toLowerCase()
        return text.includes('analyze') || text.includes('analyzing')
      })

      // Should have one analyze/analyzing button for each feature
      expect(analyzeButtons.length).toBe(mockFeatures.length)
    })

    it('Analyze button is disabled when feature status is analyzing', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([mockFeatures[1]]) // Only the analyzing feature

      const wrapper = mountComponent()
      await flushPromises()

      const analyzeButton = wrapper.findAll('button').find(btn =>
        btn.text().toLowerCase().includes('analyz')
      )

      expect(analyzeButton?.attributes('disabled')).toBeDefined()
    })

    it('calls store triggerAnalysis on Analyze button click', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([mockFeatures[0]]) // Draft feature
      vi.mocked(featureApi.triggerAnalysis).mockResolvedValue(undefined)
      vi.mocked(featureApi.get).mockResolvedValue({ ...mockFeatures[0], status: FeatureStatus.ANALYZING })

      const wrapper = mountComponent()
      await flushPromises()

      const analyzeButton = wrapper.findAll('button').find(btn =>
        btn.text().toLowerCase().includes('analyze') && !btn.text().toLowerCase().includes('analyzing')
      )

      await analyzeButton?.trigger('click')
      await flushPromises()

      expect(featureApi.triggerAnalysis).toHaveBeenCalledWith('FEAT-001')
    })
  })

  describe('Delete button', () => {
    it('has "Delete" button for each feature', async () => {
      vi.mocked(featureApi.list).mockResolvedValue(mockFeatures)

      const wrapper = mountComponent()
      await flushPromises()

      const deleteButtons = wrapper.findAll('button').filter(btn =>
        btn.text().toLowerCase().includes('delete')
      )

      expect(deleteButtons.length).toBe(mockFeatures.length)
    })

    it('calls store deleteFeature on Delete button click', async () => {
      vi.mocked(featureApi.list).mockResolvedValue([mockFeatures[0]])
      vi.mocked(featureApi.delete).mockResolvedValue(undefined)

      const wrapper = mountComponent()
      await flushPromises()

      const deleteButton = wrapper.findAll('button').find(btn =>
        btn.text().toLowerCase().includes('delete')
      )

      await deleteButton?.trigger('click')
      await flushPromises()

      expect(featureApi.delete).toHaveBeenCalledWith('FEAT-001')
    })
  })

  describe('error state', () => {
    it('renders error message when error occurs', async () => {
      vi.mocked(featureApi.list).mockRejectedValue(new Error('Failed to fetch'))

      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.text()).toContain('Failed to fetch')
    })
  })
})

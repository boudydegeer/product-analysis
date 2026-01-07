import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    })),
  },
}))

// Import types
import { FeatureStatus, type Feature, type FeatureCreate, type FeatureUpdate, type Analysis } from '@/types/feature'

describe('TypeScript Types', () => {
  describe('FeatureStatus enum', () => {
    it('has draft status', () => {
      expect(FeatureStatus.DRAFT).toBe('draft')
    })

    it('has analyzing status', () => {
      expect(FeatureStatus.ANALYZING).toBe('analyzing')
    })

    it('has analyzed status', () => {
      expect(FeatureStatus.ANALYZED).toBe('analyzed')
    })

    it('has approved status', () => {
      expect(FeatureStatus.APPROVED).toBe('approved')
    })

    it('has rejected status', () => {
      expect(FeatureStatus.REJECTED).toBe('rejected')
    })

    it('has in_progress status', () => {
      expect(FeatureStatus.IN_PROGRESS).toBe('in_progress')
    })

    it('has completed status', () => {
      expect(FeatureStatus.COMPLETED).toBe('completed')
    })
  })

  describe('Feature interface', () => {
    it('matches backend schema', () => {
      const feature: Feature = {
        id: 'FEAT-001',
        name: 'Test Feature',
        description: 'Test description',
        status: FeatureStatus.DRAFT,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      expect(feature.id).toBe('FEAT-001')
      expect(feature.name).toBe('Test Feature')
      expect(feature.description).toBe('Test description')
      expect(feature.status).toBe(FeatureStatus.DRAFT)
      expect(feature.created_at).toBeDefined()
      expect(feature.updated_at).toBeDefined()
    })

    it('supports optional github_workflow_run_id', () => {
      const feature: Feature = {
        id: 'FEAT-002',
        name: 'Feature with workflow',
        description: 'Description',
        status: FeatureStatus.ANALYZING,
        github_workflow_run_id: '12345',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      expect(feature.github_workflow_run_id).toBe('12345')
    })
  })

  describe('FeatureCreate interface', () => {
    it('requires id, name, and description', () => {
      const createData: FeatureCreate = {
        id: 'FEAT-001',
        name: 'New Feature',
        description: 'Feature description',
      }

      expect(createData.id).toBe('FEAT-001')
      expect(createData.name).toBe('New Feature')
      expect(createData.description).toBe('Feature description')
    })
  })

  describe('FeatureUpdate interface', () => {
    it('has all fields optional', () => {
      const updateData: FeatureUpdate = {}

      expect(updateData.name).toBeUndefined()
      expect(updateData.description).toBeUndefined()
      expect(updateData.status).toBeUndefined()
    })

    it('allows partial updates', () => {
      const updateData: FeatureUpdate = {
        name: 'Updated Name',
      }

      expect(updateData.name).toBe('Updated Name')
      expect(updateData.description).toBeUndefined()
    })
  })

  describe('Analysis interface', () => {
    it('matches backend schema', () => {
      const analysis: Analysis = {
        id: 1,
        feature_id: 'FEAT-001',
        workflow_run_id: '12345',
        workflow_run_number: 42,
        analyzed_at: '2024-01-01T00:00:00Z',
        story_points: 5,
        estimated_hours: 20,
        prerequisite_hours: 5,
        total_hours: 25,
        complexity_level: 'medium',
        rationale: 'Based on analysis',
        repository_maturity: 'mature',
        warnings: [],
        repository_state: {},
        affected_modules: [],
        implementation_tasks: [],
        technical_risks: [],
        recommendations: {},
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      expect(analysis.id).toBe(1)
      expect(analysis.feature_id).toBe('FEAT-001')
      expect(analysis.workflow_run_id).toBe('12345')
      expect(analysis.story_points).toBe(5)
      expect(analysis.complexity_level).toBe('medium')
    })
  })
})

describe('API Client (featuresApi)', () => {
  let mockAxiosInstance: {
    get: ReturnType<typeof vi.fn>
    post: ReturnType<typeof vi.fn>
    patch: ReturnType<typeof vi.fn>
    delete: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    vi.resetModules()
    mockAxiosInstance = {
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    }
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any)
  })

  describe('list()', () => {
    it('calls GET /api/features and returns Feature[]', async () => {
      const mockFeatures: Feature[] = [
        {
          id: 'FEAT-001',
          name: 'Feature 1',
          description: 'Description 1',
          status: FeatureStatus.DRAFT,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'FEAT-002',
          name: 'Feature 2',
          description: 'Description 2',
          status: FeatureStatus.COMPLETED,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ]
      mockAxiosInstance.get.mockResolvedValue({ data: mockFeatures })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.list()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/features/')
      expect(Array.isArray(result)).toBe(true)
      expect(result).toHaveLength(2)
      expect(result).toEqual(mockFeatures)
    })
  })

  describe('get(id: string)', () => {
    it('calls GET /api/features/{id} and returns Feature', async () => {
      const mockFeature: Feature = {
        id: 'FEAT-001',
        name: 'Feature 1',
        description: 'Description 1',
        status: FeatureStatus.DRAFT,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      mockAxiosInstance.get.mockResolvedValue({ data: mockFeature })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.get('FEAT-001')

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/features/FEAT-001')
      expect(result).toEqual(mockFeature)
      expect(result.id).toBe('FEAT-001')
      expect(result.name).toBe('Feature 1')
    })
  })

  describe('create(data: FeatureCreate)', () => {
    it('calls POST /api/features and returns Feature', async () => {
      const createData: FeatureCreate = {
        id: 'FEAT-001',
        name: 'New Feature',
        description: 'New description',
      }
      const mockFeature: Feature = {
        id: 'FEAT-001',
        name: 'New Feature',
        description: 'New description',
        status: FeatureStatus.DRAFT,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      mockAxiosInstance.post.mockResolvedValue({ data: mockFeature })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.create(createData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/features/', createData)
      expect(result).toEqual(mockFeature)
      expect(result.id).toBeDefined()
      expect(result.status).toBe(FeatureStatus.DRAFT)
    })
  })

  describe('update(id: string, data: FeatureUpdate)', () => {
    it('calls PATCH /api/features/{id} and returns Feature', async () => {
      const updateData: FeatureUpdate = {
        name: 'Updated Feature',
      }
      const mockFeature: Feature = {
        id: 'FEAT-001',
        name: 'Updated Feature',
        description: 'Original description',
        status: FeatureStatus.DRAFT,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }
      mockAxiosInstance.patch.mockResolvedValue({ data: mockFeature })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.update('FEAT-001', updateData)

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/features/FEAT-001', updateData)
      expect(result).toEqual(mockFeature)
    })

    it('allows updating status', async () => {
      const updateData: FeatureUpdate = {
        status: FeatureStatus.COMPLETED,
      }
      const mockFeature: Feature = {
        id: 'FEAT-001',
        name: 'Feature 1',
        description: 'Description 1',
        status: FeatureStatus.COMPLETED,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }
      mockAxiosInstance.patch.mockResolvedValue({ data: mockFeature })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.update('FEAT-001', updateData)

      expect(result.status).toBe(FeatureStatus.COMPLETED)
    })
  })

  describe('delete(id: string)', () => {
    it('calls DELETE /api/features/{id}', async () => {
      mockAxiosInstance.delete.mockResolvedValue({ data: null })

      const { featureApi: featuresApi } = await import('@/services/api')
      await featuresApi.delete('FEAT-001')

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/features/FEAT-001')
    })

    it('returns void', async () => {
      mockAxiosInstance.delete.mockResolvedValue({ data: null })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.delete('FEAT-001')

      expect(result).toBeUndefined()
    })
  })

  describe('triggerAnalysis(id: string)', () => {
    it('calls POST /api/features/{id}/analyze and returns void', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { message: 'Analysis started' } })

      const { featureApi: featuresApi } = await import('@/services/api')
      const result = await featuresApi.triggerAnalysis('FEAT-001')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/features/FEAT-001/analyze', {})
      expect(result).toBeUndefined()
    })
  })
})

describe('API Client Configuration', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  it('creates axios instance with baseURL', async () => {
    await import('@/services/api')

    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: expect.any(String),
      })
    )
  })

  it('sets Content-Type header to application/json', async () => {
    await import('@/services/api')

    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })
})

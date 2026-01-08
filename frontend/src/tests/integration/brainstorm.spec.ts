import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import BrainstormListView from '@/views/BrainstormListView.vue'
import { brainstormsApi } from '@/api/brainstorms'

vi.mock('@/api/brainstorms')

describe('Brainstorm Integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should complete create session workflow', async () => {
    const mockSessions = [
      {
        id: 'session-1',
        title: 'Test Session',
        description: 'Test',
        status: 'active' as const,
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    vi.mocked(brainstormsApi.listSessions).mockResolvedValue(mockSessions)
    vi.mocked(brainstormsApi.createSession).mockResolvedValue(mockSessions[0])

    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: BrainstormListView },
        { path: '/brainstorm/:id', component: { template: '<div>Detail</div>' } },
      ],
    })

    const wrapper = mount(BrainstormListView, {
      global: {
        plugins: [router],
      },
    })

    await wrapper.vm.$nextTick()

    // Verify sessions loaded
    expect(brainstormsApi.listSessions).toHaveBeenCalled()
  })
})

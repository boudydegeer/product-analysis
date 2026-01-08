import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BrainstormList from '../BrainstormList.vue'
import { useBrainstormStore } from '@/stores/brainstorm'

describe('BrainstormList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render sessions list', async () => {
    const wrapper = mount(BrainstormList)
    const store = useBrainstormStore()

    store.sessions = [
      {
        id: 'session-1',
        title: 'Mobile App Redesign',
        description: 'Reimagine the mobile experience',
        status: 'active',
        messages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    store.loading = false

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Mobile App Redesign')
  })

  it('should show loading state', async () => {
    const wrapper = mount(BrainstormList)
    const store = useBrainstormStore()

    store.loading = true
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Loading')
  })

  it('should emit create-session event', async () => {
    const wrapper = mount(BrainstormList)

    // Simulate clicking create button
    const createButton = wrapper.find('[data-testid="create-session-btn"]')
    await createButton.trigger('click')

    expect(wrapper.emitted('create-session')).toBeTruthy()
  })
})

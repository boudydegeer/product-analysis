import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import BrainstormChat from '../BrainstormChat.vue'
import { useBrainstormStore } from '@/stores/brainstorm'

describe('BrainstormChat', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render messages', async () => {
    const store = useBrainstormStore()
    store.currentSession = {
      id: 'session-1',
      title: 'Test Session',
      description: 'Test',
      status: 'active',
      messages: [
        {
          id: 'msg-1',
          session_id: 'session-1',
          role: 'user',
          content: {
            blocks: [
              {
                id: 'block-1',
                type: 'text',
                text: 'Hello',
              },
            ],
          },
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'msg-2',
          session_id: 'session-1',
          role: 'assistant',
          content: {
            blocks: [
              {
                id: 'block-2',
                type: 'text',
                text: 'Hi there!',
              },
            ],
          },
          created_at: '2024-01-01T00:00:01Z',
          updated_at: '2024-01-01T00:00:01Z',
        },
      ],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:01Z',
    }
    store.loading = false
    store.setWsConnected(true)

    const wrapper = mount(BrainstormChat, {
      props: { sessionId: 'session-1' },
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Hello')
    expect(wrapper.text()).toContain('Hi there!')
  })

  it('should show streaming indicator', async () => {
    const store = useBrainstormStore()
    store.startStreamingMessage('msg-streaming')
    store.loading = false

    const wrapper = mount(BrainstormChat, {
      props: { sessionId: 'session-1' },
    })

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Thinking...')
  })
})

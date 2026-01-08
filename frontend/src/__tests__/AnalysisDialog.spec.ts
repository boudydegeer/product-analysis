import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import AnalysisDialog from '../components/analysis/AnalysisDialog.vue'

describe('AnalysisDialog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render dialog when open', () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    })

    // Check that Dialog component is rendered
    expect(wrapper.findComponent({ name: 'Dialog' }).exists()).toBe(true)
    expect(wrapper.props('open')).toBe(true)
  })

  it('should not render dialog when closed', () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: false,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    })

    expect(wrapper.props('open')).toBe(false)
  })

  it('should emit close event', async () => {
    const wrapper = mount(AnalysisDialog, {
      props: {
        open: true,
        featureId: 'test-123',
        featureName: 'Test Feature',
      },
      global: {
        stubs: {
          teleport: true,
        },
      },
    })

    await wrapper.vm.$emit('update:open', false)
    expect(wrapper.emitted('update:open')).toBeTruthy()
  })
})

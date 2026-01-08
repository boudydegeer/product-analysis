import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingState from '../components/analysis/states/LoadingState.vue'
import NoAnalysisState from '../components/analysis/states/NoAnalysisState.vue'
import FailedState from '../components/analysis/states/FailedState.vue'
import AnalyzingState from '../components/analysis/states/AnalyzingState.vue'

describe('Analysis State Components', () => {
  it('should render loading state', () => {
    const wrapper = mount(LoadingState)
    expect(wrapper.exists()).toBe(true)
  })

  it('should render no analysis state', () => {
    const wrapper = mount(NoAnalysisState)
    expect(wrapper.text()).toContain('No Analysis Available')
  })

  it('should render failed state with error message', () => {
    const wrapper = mount(FailedState, {
      props: { message: 'API timeout error' },
    })
    expect(wrapper.text()).toContain('API timeout error')
  })

  it('should render analyzing state', () => {
    const wrapper = mount(AnalyzingState, {
      props: { startedAt: '2026-01-08T10:00:00Z' },
    })
    expect(wrapper.text()).toContain('Analyzing')
  })
})

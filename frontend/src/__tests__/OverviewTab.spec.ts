import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import OverviewTab from '../components/analysis/tabs/OverviewTab.vue'
import type { AnalysisOverview } from '../types/analysis'

describe('OverviewTab', () => {
  it('should render summary', () => {
    const overview: AnalysisOverview = {
      summary: 'Test summary text',
      key_points: ['Point 1', 'Point 2'],
      metrics: {
        complexity: 'medium',
        estimated_effort: '3-5 days',
        confidence: 0.85,
      },
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('Test summary text')
  })

  it('should render key points', () => {
    const overview: AnalysisOverview = {
      summary: 'Summary',
      key_points: ['First point', 'Second point'],
      metrics: {},
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('First point')
    expect(wrapper.text()).toContain('Second point')
  })

  it('should display metrics', () => {
    const overview: AnalysisOverview = {
      summary: 'Summary',
      key_points: [],
      metrics: {
        complexity: 'high',
        estimated_effort: '5-7 days',
        confidence: 0.9,
      },
    }

    const wrapper = mount(OverviewTab, {
      props: { overview },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('5-7 days')
    expect(wrapper.text()).toContain('90')
  })
})

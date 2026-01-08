import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import IdeaCard from '../IdeaCard.vue'

describe('IdeaCard', () => {
  it('should render idea details', () => {
    const idea = {
      id: 'idea-1',
      title: 'Dark Mode Feature',
      description: 'Add dark mode support',
      status: 'backlog' as const,
      priority: 'high' as const,
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: 'Strong',
      risk_assessment: 'Low',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    expect(wrapper.text()).toContain('Dark Mode Feature')
    expect(wrapper.text()).toContain('Add dark mode support')
  })

  it('should show evaluation scores', () => {
    const idea = {
      id: 'idea-1',
      title: 'Test',
      description: 'Test',
      status: 'backlog' as const,
      priority: 'medium' as const,
      business_value: 8,
      technical_complexity: 5,
      estimated_effort: '2 weeks',
      market_fit_analysis: null,
      risk_assessment: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    expect(wrapper.text()).toContain('8')
    expect(wrapper.text()).toContain('5')
  })

  it('should emit click event', async () => {
    const idea = {
      id: 'idea-1',
      title: 'Test',
      description: 'Test',
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

    const wrapper = mount(IdeaCard, {
      props: { idea },
    })

    await wrapper.trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
  })
})

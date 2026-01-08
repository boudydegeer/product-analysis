import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RecommendationsTab from '../components/analysis/tabs/RecommendationsTab.vue'
import type { AnalysisRecommendations } from '../types/analysis'

describe('RecommendationsTab', () => {
  it('should render improvements with priority', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [
        {
          priority: 'high',
          title: 'Add caching layer',
          description: 'Implement Redis caching',
          effort: '2 days',
        },
      ],
      best_practices: [],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('Add caching layer')
    expect(wrapper.text()).toContain('2 days')
  })

  it('should render best practices', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: ['Use TypeScript', 'Write unit tests'],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('Use TypeScript')
    expect(wrapper.text()).toContain('Write unit tests')
  })

  it('should render next steps', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: [],
      next_steps: ['Setup CI/CD', 'Deploy to staging'],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('Setup CI/CD')
    expect(wrapper.text()).toContain('Deploy to staging')
  })
})

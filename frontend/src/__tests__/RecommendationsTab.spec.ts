import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RecommendationsTab from '../components/analysis/tabs/RecommendationsTab.vue'
import type { AnalysisRecommendations } from '../types/analysis'

describe('RecommendationsTab', () => {
  it('should render improvements with rich structure', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [
        {
          priority: 'high',
          title: 'Implement httpOnly cookies',
          description: 'Move token storage from localStorage to httpOnly cookies to prevent XSS attacks',
          effort: '1-2 days',
        },
        {
          priority: 'low',
          title: 'Add caching layer',
          description: 'Use Redis for caching to improve performance',
          effort: '3 days',
        },
      ],
      best_practices: [],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    // Check title
    expect(wrapper.text()).toContain('Implement httpOnly cookies')
    expect(wrapper.text()).toContain('Add caching layer')

    // Check description
    expect(wrapper.text()).toContain('localStorage')
    expect(wrapper.text()).toContain('XSS attacks')

    // Check effort
    expect(wrapper.text()).toContain('1-2 days')
    expect(wrapper.text()).toContain('3 days')

    // Check priority badges
    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('low')
  })

  it('should sort improvements by priority', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [
        {
          priority: 'low',
          title: 'Low priority task',
          description: 'This should be last',
        },
        {
          priority: 'high',
          title: 'High priority task',
          description: 'This should be first',
        },
        {
          priority: 'medium',
          title: 'Medium priority task',
          description: 'This should be in the middle',
        },
      ],
      best_practices: [],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    const text = wrapper.text()
    const highIndex = text.indexOf('High priority task')
    const mediumIndex = text.indexOf('Medium priority task')
    const lowIndex = text.indexOf('Low priority task')

    expect(highIndex).toBeLessThan(mediumIndex)
    expect(mediumIndex).toBeLessThan(lowIndex)
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

    expect(wrapper.text()).toContain('Best Practices')
    expect(wrapper.text()).toContain('Use TypeScript')
    expect(wrapper.text()).toContain('Write unit tests')
  })

  it('should render next steps with numbering', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: [],
      next_steps: ['Setup CI/CD', 'Deploy to staging', 'Run smoke tests'],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('Next Steps')
    expect(wrapper.text()).toContain('Setup CI/CD')
    expect(wrapper.text()).toContain('Deploy to staging')
    expect(wrapper.text()).toContain('Run smoke tests')

    // Check for numbered badges
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('3')
  })

  it('should handle empty improvements', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [],
      best_practices: ['Some practice'],
      next_steps: ['Some step'],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    // Should not show Priority Improvements header
    expect(wrapper.text()).not.toContain('Priority Improvements')
    // Should show other sections
    expect(wrapper.text()).toContain('Best Practices')
    expect(wrapper.text()).toContain('Next Steps')
  })

  it('should render improvements without effort', () => {
    const recommendations: AnalysisRecommendations = {
      improvements: [
        {
          priority: 'medium',
          title: 'No effort estimate',
          description: 'This improvement has no effort estimate',
        },
      ],
      best_practices: [],
      next_steps: [],
    }

    const wrapper = mount(RecommendationsTab, {
      props: { recommendations },
    })

    expect(wrapper.text()).toContain('No effort estimate')
    expect(wrapper.text()).toContain('This improvement has no effort estimate')
    // Should not show effort text when not provided
    expect(wrapper.text()).not.toContain('Estimated effort:')
  })
})

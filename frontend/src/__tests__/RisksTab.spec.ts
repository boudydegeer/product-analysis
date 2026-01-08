import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RisksTab from '../components/analysis/tabs/RisksTab.vue'
import type { AnalysisRisks } from '../types/analysis'

describe('RisksTab', () => {
  it('should render technical risks', () => {
    const risks: AnalysisRisks = {
      technical_risks: [
        {
          severity: 'high',
          category: 'Performance',
          description: 'Slow database queries',
        },
      ],
      security_concerns: [],
      scalability_issues: [],
      mitigation_strategies: [],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('high')
    expect(wrapper.text()).toContain('Slow database queries')
  })

  it('should render security concerns', () => {
    const risks: AnalysisRisks = {
      technical_risks: [],
      security_concerns: [
        {
          severity: 'critical',
          description: 'SQL injection vulnerability',
          cwe: 'CWE-89',
        },
      ],
      scalability_issues: [],
      mitigation_strategies: [],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('critical')
    expect(wrapper.text()).toContain('SQL injection')
    expect(wrapper.text()).toContain('CWE-89')
  })

  it('should render mitigation strategies', () => {
    const risks: AnalysisRisks = {
      technical_risks: [],
      security_concerns: [],
      scalability_issues: [],
      mitigation_strategies: ['Add caching', 'Implement rate limiting'],
    }

    const wrapper = mount(RisksTab, {
      props: { risks },
    })

    expect(wrapper.text()).toContain('Add caching')
    expect(wrapper.text()).toContain('Implement rate limiting')
  })
})

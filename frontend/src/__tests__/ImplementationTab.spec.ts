import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ImplementationTab from '../components/analysis/tabs/ImplementationTab.vue'
import type { AnalysisImplementation } from '../types/analysis'

describe('ImplementationTab', () => {
  it('should render architecture pattern', () => {
    const implementation: AnalysisImplementation = {
      architecture: {
        pattern: 'Microservices',
        components: ['Service A', 'Service B'],
      },
      technical_details: [],
      data_flow: {},
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Microservices')
    expect(wrapper.text()).toContain('Service A')
  })

  it('should render technical details', () => {
    const implementation: AnalysisImplementation = {
      architecture: {},
      technical_details: [
        {
          category: 'Backend',
          description: 'Uses FastAPI',
          code_locations: ['/api/main.py'],
        },
      ],
      data_flow: {},
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Backend')
    expect(wrapper.text()).toContain('Uses FastAPI')
  })

  it('should render data flow steps', () => {
    const implementation: AnalysisImplementation = {
      architecture: {},
      technical_details: [],
      data_flow: {
        description: 'Request flow',
        steps: ['Step 1', 'Step 2'],
      },
    }

    const wrapper = mount(ImplementationTab, {
      props: { implementation },
    })

    expect(wrapper.text()).toContain('Request flow')
    expect(wrapper.text()).toContain('Step 1')
    expect(wrapper.text()).toContain('Step 2')
  })
})

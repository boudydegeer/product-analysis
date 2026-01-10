import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TextBlock from '../TextBlock.vue'

describe('TextBlock', () => {
  it('renders plain text without markdown', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: 'Hello world'
        }
      }
    })

    expect(wrapper.text()).toContain('Hello world')
    expect(wrapper.find('p').exists()).toBe(true)
  })

  it('renders markdown headings', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '# Main Title\n## Subtitle'
        }
      }
    })

    expect(wrapper.find('h1').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toBe('Main Title')
    expect(wrapper.find('h2').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('Subtitle')
  })

  it('renders markdown lists', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '- Item 1\n- Item 2\n- Item 3'
        }
      }
    })

    expect(wrapper.find('ul').exists()).toBe(true)
    expect(wrapper.findAll('li')).toHaveLength(3)
    expect(wrapper.findAll('li')[0].text()).toBe('Item 1')
  })

  it('renders markdown bold and italic', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '**Bold text** and *italic text*'
        }
      }
    })

    expect(wrapper.find('strong').exists()).toBe(true)
    expect(wrapper.find('strong').text()).toBe('Bold text')
    expect(wrapper.find('em').exists()).toBe(true)
    expect(wrapper.find('em').text()).toBe('italic text')
  })

  it('renders markdown code blocks', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '```python\ndef hello():\n    print("world")\n```'
        }
      }
    })

    expect(wrapper.find('pre').exists()).toBe(true)
    expect(wrapper.find('code').exists()).toBe(true)
  })

  it('sanitizes dangerous HTML', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '<script>alert("xss")</script>'
        }
      }
    })

    expect(wrapper.html()).not.toContain('<script>')
  })

  it('preserves safe HTML from markdown', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[Link](https://example.com)'
        }
      }
    })

    expect(wrapper.find('a').exists()).toBe(true)
    expect(wrapper.find('a').attributes('href')).toBe('https://example.com')
  })
})

describe('TextBlock - Feature Links', () => {
  it('renders markdown links as router-links for internal routes', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[View Feature](/features/123)'
        }
      },
      global: {
        stubs: {
          'router-link': true
        }
      }
    })

    // Should convert to router-link for internal paths
    expect(wrapper.html()).toContain('/features/123')
  })

  it('renders external links as regular anchor tags', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '[External](https://example.com)'
        }
      }
    })

    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://example.com')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toContain('noopener')
  })

  it('renders feature creation success message correctly', () => {
    const wrapper = mount(TextBlock, {
      props: {
        block: {
          type: 'text',
          text: '✓ Feature created successfully!\n\nYou can view and manage it here: [Dark Mode Toggle](/features/abc-123)'
        }
      },
      global: {
        stubs: {
          'router-link': true
        }
      }
    })

    expect(wrapper.text()).toContain('Feature created successfully')
    expect(wrapper.text()).toContain('Dark Mode Toggle')
  })
})

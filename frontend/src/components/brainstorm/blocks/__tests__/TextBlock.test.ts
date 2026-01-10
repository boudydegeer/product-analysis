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

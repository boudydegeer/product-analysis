<template>
  <div class="text-block" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import sanitizer from 'markdown-it-sanitizer'

interface TextBlock {
  type: 'text'
  text: string
}

interface Props {
  block: TextBlock
}

const props = defineProps<Props>()
const router = useRouter()

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true
}).use(sanitizer)

// Custom link rendering to handle internal routes
const defaultRender = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}

md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')

  if (hrefIndex >= 0) {
    const href = token.attrs![hrefIndex][1]

    // External links get target="_blank" and rel="noopener noreferrer"
    if (href.startsWith('http://') || href.startsWith('https://')) {
      token.attrPush(['target', '_blank'])
      token.attrPush(['rel', 'noopener noreferrer'])
    } else {
      // Internal links get a data attribute for client-side routing
      token.attrPush(['data-internal-link', 'true'])
    }
  }

  return defaultRender(tokens, idx, options, env, self)
}

const renderedHtml = computed(() => {
  return md.render(props.block.text)
})

// Handle clicks on internal links
onMounted(() => {
  nextTick(() => {
    document.querySelectorAll('[data-internal-link="true"]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault()
        const href = (e.target as HTMLAnchorElement).getAttribute('href')
        if (href) {
          router.push(href)
        }
      })
    })
  })
})
</script>

<style scoped>
.text-block {
  line-height: 1.6;
}

.text-block :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
}

.text-block :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.text-block :deep(p) {
  margin-bottom: 0.75rem;
}

.text-block :deep(ul),
.text-block :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.text-block :deep(li) {
  margin-bottom: 0.25rem;
}

.text-block :deep(code) {
  background-color: rgb(243 244 246);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
}

.text-block :deep(pre) {
  background-color: rgb(243 244 246);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}

.text-block :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.text-block :deep(strong) {
  font-weight: 600;
}

.text-block :deep(em) {
  font-style: italic;
}

.text-block :deep(a) {
  color: rgb(59 130 246);
  text-decoration: underline;
  cursor: pointer;
}

.text-block :deep(a:hover) {
  color: rgb(37 99 235);
}

.text-block :deep(blockquote) {
  border-left: 4px solid rgb(229 231 235);
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 0.75rem;
  color: rgb(107 114 128);
}
</style>

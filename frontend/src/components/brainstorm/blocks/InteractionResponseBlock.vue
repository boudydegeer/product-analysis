<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import type { InteractionResponseBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: InteractionResponseBlock
}>()

const displayValue = computed(() => {
  if (Array.isArray(props.block.value)) {
    // Format list nicely
    const items = props.block.value.map(v =>
      // Convert kebab-case to Title Case
      v.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    )
    return items.join(', ')
  }
  // Convert single value kebab-case to Title Case
  return props.block.value.split('-').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
})

const isMultiple = computed(() => Array.isArray(props.block.value))
</script>

<template>
  <div class="flex items-start gap-2 text-sm">
    <Check class="h-4 w-4 mt-0.5 flex-shrink-0" />
    <span>{{ displayValue }}</span>
  </div>
</template>

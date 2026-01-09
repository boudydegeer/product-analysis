<script setup lang="ts">
import { computed } from 'vue'
import type { InteractionResponseBlock } from '@/types/brainstorm'

const props = defineProps<{
  block: InteractionResponseBlock
}>()

const displayValue = computed(() => {
  if (Array.isArray(props.block.value)) {
    return props.block.value.join(', ')
  }
  return props.block.value
})
</script>

<template>
  <div class="text-sm">
    Selected: <span class="font-medium">{{ displayValue }}</span>
  </div>
</template>

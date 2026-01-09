<script setup lang="ts">
import type { TextBlock } from '@/types/brainstorm'

defineProps<{
  block: TextBlock
}>()
</script>

<template>
  <div class="prose prose-sm dark:prose-invert max-w-none">
    <p class="whitespace-pre-wrap">{{ block.text }}</p>
  </div>
</template>

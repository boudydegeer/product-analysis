<script setup lang="ts">
import { computed } from 'vue'
import type { ToolExecution } from '@/types/brainstorm'

const props = defineProps<{
  execution: ToolExecution
}>()

const statusEmoji = computed(() => {
  switch (props.execution.status) {
    case 'pending': return '\u23F3'
    case 'executing': return '\uD83D\uDD0D'
    case 'completed': return '\u2705'
    case 'failed': return '\u274C'
    default: return '\uD83D\uDD04'
  }
})

const statusColor = computed(() => {
  switch (props.execution.status) {
    case 'pending': return 'text-yellow-600'
    case 'executing': return 'text-blue-600'
    case 'completed': return 'text-green-600'
    case 'failed': return 'text-red-600'
    default: return 'text-gray-600'
  }
})

const displayMessage = computed(() => {
  if (props.execution.message) return props.execution.message
  switch (props.execution.status) {
    case 'pending': return 'Preparing...'
    case 'executing': return 'Investigating codebase...'
    case 'completed': return 'Exploration complete'
    case 'failed': return 'Exploration failed'
    default: return 'Processing...'
  }
})
</script>

<template>
  <div class="tool-execution-status flex items-center gap-2 p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
    <span class="status-emoji text-xl">{{ statusEmoji }}</span>
    <div class="flex-1">
      <div class="font-medium" :class="statusColor">
        {{ execution.tool_name === 'explore_codebase' ? 'Exploring Codebase' : execution.tool_name }}
      </div>
      <div class="text-sm text-slate-500 dark:text-slate-400">
        {{ displayMessage }}
        <span v-if="execution.status === 'executing'" class="animate-pulse">...</span>
      </div>
    </div>
  </div>
</template>

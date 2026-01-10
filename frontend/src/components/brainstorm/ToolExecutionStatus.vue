<script setup lang="ts">
import type { ToolExecution } from '@/types/brainstorm'
import { Search } from 'lucide-vue-next'

defineProps<{
  execution: ToolExecution
}>()
</script>

<template>
  <div class="flex items-center gap-2 text-sm text-muted-foreground">
    <Search class="h-4 w-4 animate-pulse" />
    <div>
      <span class="font-medium text-foreground">Exploring Codebase</span>
      <span class="ml-2">Investigating codebase...</span>
    </div>
  </div>
</template>

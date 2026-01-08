<script setup lang="ts">
import type { AnalysisOverview } from '@/types/analysis'
import MarkdownRenderer from '@/components/shared/MarkdownRenderer.vue'

defineProps<{
  overview: AnalysisOverview
}>()
</script>

<template>
  <div class="space-y-6">
    <!-- Summary Section -->
    <div class="space-y-2">
      <h3 class="text-lg font-semibold">Summary</h3>
      <MarkdownRenderer :content="overview.summary" />
    </div>

    <!-- Key Points Section -->
    <div v-if="overview.key_points && overview.key_points.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Key Points</h3>
      <ul class="list-disc list-inside space-y-1">
        <li v-for="(point, index) in overview.key_points" :key="index" class="text-muted-foreground">
          {{ point }}
        </li>
      </ul>
    </div>

    <!-- Metrics Section -->
    <div v-if="overview.metrics && Object.keys(overview.metrics).length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Metrics</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-if="overview.metrics.complexity" class="border rounded-lg p-4">
          <div class="text-sm text-muted-foreground">Complexity</div>
          <div class="text-lg font-medium capitalize">{{ overview.metrics.complexity }}</div>
        </div>
        <div v-if="overview.metrics.estimated_effort" class="border rounded-lg p-4">
          <div class="text-sm text-muted-foreground">Estimated Effort</div>
          <div class="text-lg font-medium">{{ overview.metrics.estimated_effort }}</div>
        </div>
        <div v-if="overview.metrics.confidence !== undefined" class="border rounded-lg p-4">
          <div class="text-sm text-muted-foreground">Confidence</div>
          <div class="text-lg font-medium">{{ Math.round(overview.metrics.confidence * 100) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

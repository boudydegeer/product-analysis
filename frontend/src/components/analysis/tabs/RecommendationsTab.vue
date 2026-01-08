<script setup lang="ts">
import type { AnalysisRecommendations } from '@/types/analysis'

defineProps<{
  recommendations: AnalysisRecommendations
}>()

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    high: 'text-red-600 border-red-600',
    medium: 'text-yellow-600 border-yellow-600',
    low: 'text-blue-600 border-blue-600',
  }
  return colors[priority.toLowerCase()] || 'text-gray-600 border-gray-600'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Improvements Section -->
    <div v-if="recommendations.improvements && recommendations.improvements.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Improvements</h3>
      <div class="space-y-3">
        <div v-for="(improvement, index) in recommendations.improvements" :key="index" class="border rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span :class="['px-2 py-1 text-xs font-medium rounded-md border', getPriorityColor(improvement.priority)]">
              {{ improvement.priority }}
            </span>
            <div class="flex-1">
              <div class="font-medium mb-1">{{ improvement.title }}</div>
              <p class="text-sm text-muted-foreground mb-2">{{ improvement.description }}</p>
              <div v-if="improvement.effort" class="text-xs text-muted-foreground">
                Effort: {{ improvement.effort }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Best Practices Section -->
    <div v-if="recommendations.best_practices && recommendations.best_practices.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Best Practices</h3>
      <ul class="list-disc list-inside space-y-2">
        <li v-for="(practice, index) in recommendations.best_practices" :key="index" class="text-muted-foreground">
          {{ practice }}
        </li>
      </ul>
    </div>

    <!-- Next Steps Section -->
    <div v-if="recommendations.next_steps && recommendations.next_steps.length > 0" class="space-y-2">
      <h3 class="text-lg font-semibold">Next Steps</h3>
      <ol class="list-decimal list-inside space-y-2">
        <li v-for="(step, index) in recommendations.next_steps" :key="index" class="text-muted-foreground">
          {{ step }}
        </li>
      </ol>
    </div>
  </div>
</template>

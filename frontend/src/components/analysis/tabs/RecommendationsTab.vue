<script setup lang="ts">
import { computed } from 'vue'
import { Clock, Info } from 'lucide-vue-next'
import type { AnalysisRecommendations, Improvement } from '@/types/analysis'
import Card from '@/components/ui/card.vue'
import CardHeader from '@/components/ui/card-header.vue'
import CardTitle from '@/components/ui/card-title.vue'
import CardContent from '@/components/ui/card-content.vue'
import Badge from '@/components/ui/badge.vue'

const props = defineProps<{
  recommendations: AnalysisRecommendations
}>()

// Sort improvements by priority (high -> medium -> low)
const sortedImprovements = computed(() => {
  const priorityOrder = { high: 1, medium: 2, low: 3 }
  return [...props.recommendations.improvements].sort(
    (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
  )
})

// Get badge color class based on priority
const priorityColor = (priority: Improvement['priority']) => {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 hover:bg-red-100'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100'
    case 'low':
      return 'bg-blue-100 text-blue-800 hover:bg-blue-100'
    default:
      return ''
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Priority Improvements Section -->
    <div v-if="sortedImprovements.length > 0">
      <h3 class="text-lg font-semibold mb-4">Priority Improvements</h3>
      <div class="space-y-4">
        <Card v-for="improvement in sortedImprovements" :key="improvement.title">
          <CardHeader>
            <div class="flex items-start justify-between">
              <CardTitle class="text-base">{{ improvement.title }}</CardTitle>
              <Badge :class="priorityColor(improvement.priority)">
                {{ improvement.priority }}
              </Badge>
            </div>
          </CardHeader>
          <CardContent class="space-y-2">
            <p class="text-muted-foreground">{{ improvement.description }}</p>
            <div v-if="improvement.effort" class="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock class="w-4 h-4" />
              <span>Estimated effort: {{ improvement.effort }}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Best Practices Section -->
    <Card v-if="recommendations.best_practices && recommendations.best_practices.length > 0">
      <CardHeader>
        <CardTitle>Best Practices</CardTitle>
      </CardHeader>
      <CardContent>
        <ul class="space-y-2">
          <li
            v-for="(practice, index) in recommendations.best_practices"
            :key="index"
            class="flex items-start gap-2"
          >
            <Info class="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
            <span>{{ practice }}</span>
          </li>
        </ul>
      </CardContent>
    </Card>

    <!-- Next Steps Section -->
    <Card v-if="recommendations.next_steps && recommendations.next_steps.length > 0">
      <CardHeader>
        <CardTitle>Next Steps</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(step, index) in recommendations.next_steps"
            :key="index"
            class="flex items-start gap-3"
          >
            <div
              class="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold shrink-0"
            >
              {{ index + 1 }}
            </div>
            <p class="pt-1">{{ step }}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

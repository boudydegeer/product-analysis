<template>
  <Card
    class="cursor-pointer hover:shadow-md transition-shadow"
    @click="$emit('click')"
  >
    <CardHeader>
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <CardTitle class="text-lg truncate">{{ idea.title }}</CardTitle>
          <CardDescription class="line-clamp-2 mt-1">
            {{ idea.description }}
          </CardDescription>
        </div>
        <div class="flex flex-col gap-2">
          <Badge :variant="getStatusVariant(idea.status)">
            {{ formatStatus(idea.status) }}
          </Badge>
          <Badge :variant="getPriorityVariant(idea.priority)">
            {{ formatPriority(idea.priority) }}
          </Badge>
        </div>
      </div>
    </CardHeader>

    <CardContent class="space-y-3">
      <!-- Evaluation Scores -->
      <div
        v-if="idea.business_value !== null || idea.technical_complexity !== null"
        class="flex gap-4"
      >
        <div v-if="idea.business_value !== null" class="flex items-center gap-2">
          <TrendingUp class="h-4 w-4 text-green-600" />
          <span class="text-sm font-medium">Value: {{ idea.business_value }}/10</span>
        </div>
        <div v-if="idea.technical_complexity !== null" class="flex items-center gap-2">
          <Wrench class="h-4 w-4 text-orange-600" />
          <span class="text-sm font-medium">Complexity: {{ idea.technical_complexity }}/10</span>
        </div>
      </div>

      <!-- Estimated Effort -->
      <div v-if="idea.estimated_effort" class="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock class="h-4 w-4" />
        {{ idea.estimated_effort }}
      </div>

      <!-- Not Evaluated Badge -->
      <div v-else class="flex items-center gap-2 text-sm text-muted-foreground">
        <Sparkles class="h-4 w-4" />
        <span>Not evaluated yet</span>
      </div>

      <!-- Timestamp -->
      <div class="text-xs text-muted-foreground">
        {{ formatDate(idea.updated_at) }}
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import type { Idea } from '@/types/idea'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, Wrench, Clock, Sparkles } from 'lucide-vue-next'

defineProps<{
  idea: Idea
}>()

defineEmits<{
  click: []
}>()

function getStatusVariant(status: string) {
  switch (status) {
    case 'backlog':
      return 'secondary'
    case 'under_review':
      return 'default'
    case 'approved':
      return 'default'
    case 'rejected':
      return 'destructive'
    case 'implemented':
      return 'outline'
    default:
      return 'secondary'
  }
}

function getPriorityVariant(priority: string) {
  switch (priority) {
    case 'critical':
      return 'destructive'
    case 'high':
      return 'default'
    case 'medium':
      return 'secondary'
    case 'low':
      return 'outline'
    default:
      return 'secondary'
  }
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatPriority(priority: string): string {
  return priority.charAt(0).toUpperCase() + priority.slice(1)
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 60) {
    return `${diffMins}m ago`
  }

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }

  return date.toLocaleDateString()
}
</script>

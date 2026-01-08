<template>
  <div class="container mx-auto py-6">
    <div class="mb-4">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ArrowLeft class="mr-2 h-4 w-4" />
        Back to Ideas
      </Button>
    </div>

    <div v-if="loading" class="text-center py-12">
      <p class="text-muted-foreground">Loading idea...</p>
    </div>

    <div v-else-if="idea" class="space-y-6">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <h1 class="text-3xl font-bold">{{ idea.title }}</h1>
          <div class="flex gap-2 mt-2">
            <Badge :variant="getStatusVariant(idea.status)">
              {{ formatStatus(idea.status) }}
            </Badge>
            <Badge :variant="getPriorityVariant(idea.priority)">
              {{ formatPriority(idea.priority) }}
            </Badge>
          </div>
        </div>
        <Button variant="outline" @click="showEditDialog = true">
          <Edit class="mr-2 h-4 w-4" />
          Edit
        </Button>
      </div>

      <!-- Description -->
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p class="whitespace-pre-wrap">{{ idea.description }}</p>
        </CardContent>
      </Card>

      <!-- Evaluation -->
      <Card v-if="idea.business_value !== null">
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle>AI Evaluation</CardTitle>
            <Button variant="outline" size="sm" @click="handleReEvaluate">
              <RefreshCw class="mr-2 h-4 w-4" />
              Re-evaluate
            </Button>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <!-- Scores -->
          <div class="grid grid-cols-3 gap-4">
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Business Value</p>
              <p class="text-2xl font-bold">{{ idea.business_value }}/10</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Technical Complexity</p>
              <p class="text-2xl font-bold">{{ idea.technical_complexity }}/10</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">Estimated Effort</p>
              <p class="text-2xl font-bold">{{ idea.estimated_effort }}</p>
            </div>
          </div>

          <!-- Market Fit Analysis -->
          <div v-if="idea.market_fit_analysis" class="space-y-2">
            <h4 class="font-semibold">Market Fit Analysis</h4>
            <p class="text-sm text-muted-foreground">{{ idea.market_fit_analysis }}</p>
          </div>

          <!-- Risk Assessment -->
          <div v-if="idea.risk_assessment" class="space-y-2">
            <h4 class="font-semibold">Risk Assessment</h4>
            <p class="text-sm text-muted-foreground">{{ idea.risk_assessment }}</p>
          </div>
        </CardContent>
      </Card>

      <!-- No Evaluation -->
      <Card v-else>
        <CardContent class="text-center py-12">
          <Sparkles class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">Not Evaluated Yet</h3>
          <p class="text-muted-foreground mb-4">
            Use AI to evaluate business value, complexity, and market fit
          </p>
          <Button @click="handleEvaluate" :disabled="evaluating">
            {{ evaluating ? 'Evaluating...' : 'Evaluate with AI' }}
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useIdeasStore } from '@/stores/ideas'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Edit, RefreshCw, Sparkles } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const store = useIdeasStore()

const showEditDialog = ref(false)

const ideaId = route.params.id as string
const idea = computed(() => store.currentIdea)
const loading = computed(() => store.loading)
const evaluating = computed(() => store.evaluating)

async function handleEvaluate() {
  if (!idea.value) return

  try {
    const evaluation = await store.evaluateIdea({
      title: idea.value.title,
      description: idea.value.description,
    })

    await store.updateIdea(idea.value.id, {
      business_value: evaluation.business_value,
      technical_complexity: evaluation.technical_complexity,
      estimated_effort: evaluation.estimated_effort,
      market_fit_analysis: evaluation.market_fit_analysis,
      risk_assessment: evaluation.risk_assessment,
    })
  } catch (error) {
    console.error('Failed to evaluate idea:', error)
  }
}

async function handleReEvaluate() {
  await handleEvaluate()
}

function getStatusVariant(status: string) {
  // Same as IdeaCard
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
  // Same as IdeaCard
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

onMounted(async () => {
  await store.fetchIdea(ideaId)
})
</script>

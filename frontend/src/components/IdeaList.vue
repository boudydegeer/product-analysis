<template>
  <div class="space-y-4">
    <!-- Header with Filters -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Ideas</h2>
        <p class="text-muted-foreground">Capture and evaluate product ideas</p>
      </div>
      <Button @click="$emit('create-idea')">
        <Plus class="mr-2 h-4 w-4" />
        New Idea
      </Button>
    </div>

    <!-- Filters -->
    <div class="flex gap-4">
      <Select v-model="statusFilter">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="backlog">Backlog</SelectItem>
          <SelectItem value="under_review">Under Review</SelectItem>
          <SelectItem value="approved">Approved</SelectItem>
          <SelectItem value="rejected">Rejected</SelectItem>
          <SelectItem value="implemented">Implemented</SelectItem>
        </SelectContent>
      </Select>

      <Select v-model="priorityFilter">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="Filter by priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Priorities</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="low">Low</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading ideas...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="fetchIdeas" variant="outline" class="mt-4">Retry</Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredIdeas.length === 0" class="text-center py-12">
      <Lightbulb class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Ideas Yet</h3>
      <p class="text-muted-foreground mb-4">
        Start capturing product ideas and evaluate them with AI
      </p>
      <Button @click="$emit('create-idea')">Create Your First Idea</Button>
    </div>

    <!-- Ideas Grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <IdeaCard
        v-for="idea in filteredIdeas"
        :key="idea.id"
        :idea="idea"
        @click="$emit('select-idea', idea.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useIdeasStore } from '@/stores/ideas'
import IdeaCard from './IdeaCard.vue'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, Lightbulb } from 'lucide-vue-next'

defineEmits<{
  'create-idea': []
  'select-idea': [id: string]
}>()

const store = useIdeasStore()

const statusFilter = ref('all')
const priorityFilter = ref('all')

const ideas = computed(() => store.ideas)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

const filteredIdeas = computed(() => {
  let filtered = ideas.value

  if (statusFilter.value !== 'all') {
    filtered = filtered.filter((idea) => idea.status === statusFilter.value)
  }

  if (priorityFilter.value !== 'all') {
    filtered = filtered.filter((idea) => idea.priority === priorityFilter.value)
  }

  return filtered
})

async function fetchIdeas() {
  await store.fetchIdeas()
}

// Fetch ideas when filters change
watch([statusFilter, priorityFilter], () => {
  const params: any = {}
  if (statusFilter.value !== 'all') {
    params.status = statusFilter.value
  }
  if (priorityFilter.value !== 'all') {
    params.priority = priorityFilter.value
  }
  store.fetchIdeas(params)
})

onMounted(() => {
  fetchIdeas()
})
</script>

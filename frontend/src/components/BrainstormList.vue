<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold">Brainstorming Sessions</h2>
        <p class="text-muted-foreground">
          Collaborate with Claude to explore ideas
        </p>
      </div>
      <Button
        data-testid="create-session-btn"
        @click="$emit('create-session')"
      >
        <Plus class="mr-2 h-4 w-4" />
        New Session
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading sessions...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="fetchSessions" variant="outline" class="mt-4">
        Retry
      </Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="sessions.length === 0" class="text-center py-12">
      <Lightbulb class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Sessions Yet</h3>
      <p class="text-muted-foreground mb-4">
        Start a brainstorming session to collaborate with Claude
      </p>
      <Button @click="$emit('create-session')">
        Create Your First Session
      </Button>
    </div>

    <!-- Sessions Grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="session in sessions"
        :key="session.id"
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="$emit('select-session', session.id)"
      >
        <CardHeader>
          <div class="flex items-start justify-between">
            <CardTitle class="text-lg">{{ session.title }}</CardTitle>
            <Badge :variant="getStatusVariant(session.status)">
              {{ session.status }}
            </Badge>
          </div>
          <CardDescription class="line-clamp-2">
            {{ session.description }}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="flex items-center text-sm text-muted-foreground">
            <MessageSquare class="mr-2 h-4 w-4" />
            {{ session.messages.length }} messages
          </div>
          <div class="text-xs text-muted-foreground mt-2">
            {{ formatDate(session.updated_at) }}
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useBrainstormStore } from '@/stores/brainstorm'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plus, MessageSquare, Lightbulb } from 'lucide-vue-next'

defineEmits<{
  'create-session': []
  'select-session': [id: string]
}>()

const store = useBrainstormStore()

const sessions = computed(() => store.sessions)
const loading = computed(() => store.loading)
const error = computed(() => store.error)

function getStatusVariant(status: string) {
  switch (status) {
    case 'active':
      return 'default'
    case 'paused':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'archived':
      return 'outline'
    default:
      return 'default'
  }
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

async function fetchSessions() {
  await store.fetchSessions()
}

onMounted(() => {
  fetchSessions()
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold">Agents</h3>
        <p class="text-sm text-muted-foreground">Manage AI agent configurations</p>
      </div>
      <Button @click="$emit('create')">
        <Plus class="mr-2 h-4 w-4" />
        New Agent
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading agents...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-destructive">{{ error }}</p>
      <Button @click="$emit('retry')" variant="outline" class="mt-4">Retry</Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="agents.length === 0" class="text-center py-12">
      <Bot class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Agents Yet</h3>
      <p class="text-muted-foreground mb-4">
        Create your first AI agent to get started
      </p>
      <Button @click="$emit('create')">Create Agent</Button>
    </div>

    <!-- Agents Grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="agent in agents"
        :key="agent.id"
        class="hover:shadow-md transition-shadow cursor-pointer"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center text-lg"
                :style="{ backgroundColor: agent.avatar_color }"
              >
                {{ agent.avatar_url || '🤖' }}
              </div>
              <div>
                <CardTitle class="text-lg">{{ agent.display_name }}</CardTitle>
                <p class="text-sm text-muted-foreground">{{ agent.name }}</p>
              </div>
            </div>
            <Badge :variant="agent.enabled ? 'default' : 'secondary'">
              {{ agent.enabled ? 'Enabled' : 'Disabled' }}
            </Badge>
          </div>
        </CardHeader>

        <CardContent class="space-y-3">
          <p class="text-sm text-muted-foreground line-clamp-2">
            {{ agent.description || 'No description' }}
          </p>

          <div class="flex flex-wrap gap-2">
            <Badge variant="outline" class="text-xs">{{ agent.model }}</Badge>
            <Badge v-if="agent.is_default" variant="outline" class="text-xs">Default</Badge>
            <Badge variant="outline" class="text-xs">v{{ agent.version }}</Badge>
          </div>

          <div v-if="agent.personality_traits.length > 0" class="flex flex-wrap gap-1">
            <Badge
              v-for="trait in agent.personality_traits.slice(0, 3)"
              :key="trait"
              variant="secondary"
              class="text-xs"
            >
              {{ trait }}
            </Badge>
            <Badge v-if="agent.personality_traits.length > 3" variant="secondary" class="text-xs">
              +{{ agent.personality_traits.length - 3 }}
            </Badge>
          </div>

          <div class="flex items-center justify-between pt-2 border-t">
            <div class="text-xs text-muted-foreground">
              Temp: {{ agent.temperature }}
            </div>
            <div class="flex gap-2">
              <Button
                size="sm"
                variant="ghost"
                @click.stop="$emit('toggleEnabled', agent.id)"
                :title="agent.enabled ? 'Disable' : 'Enable'"
              >
                <Power class="h-4 w-4" :class="agent.enabled ? 'text-green-500' : ''" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                @click.stop="$emit('edit', agent.id)"
                title="Edit"
              >
                <Pencil class="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                @click.stop="$emit('delete', agent.id)"
                title="Delete"
                class="text-destructive hover:text-destructive"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bot, Plus, Power, Pencil, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { AgentTypeResponse } from '@/api/admin'

defineProps<{
  agents: AgentTypeResponse[]
  loading: boolean
  error: string | null
}>()

defineEmits<{
  create: []
  edit: [agentId: number]
  delete: [agentId: number]
  toggleEnabled: [agentId: number]
  retry: []
}>()
</script>

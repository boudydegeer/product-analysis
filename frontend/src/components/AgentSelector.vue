<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Bot } from 'lucide-vue-next'
import { listAgents } from '@/api/agents'
import type { AgentType } from '@/types/agent'

const emit = defineEmits<{
  select: [agent: AgentType]
}>()

const agents = ref<AgentType[]>([])
const loading = ref(false)
const selectedAgent = ref<string | null>(null)

async function loadAgents() {
  loading.value = true
  try {
    agents.value = await listAgents()

    // Auto-select default agent
    const defaultAgent = agents.value.find(a => a.name === 'brainstorm')
    if (defaultAgent) {
      selectedAgent.value = defaultAgent.name
    }
  } catch (error) {
    console.error('[AGENT_SELECTOR] Failed to load agents:', error)
  } finally {
    loading.value = false
  }
}

function selectAgent(agent: AgentType) {
  selectedAgent.value = agent.name
  emit('select', agent)
}

function isEmoji(str: string): boolean {
  return /\p{Emoji}/u.test(str)
}

onMounted(() => {
  loadAgents()
})
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold">Choose Your AI Assistant</h3>

    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading agents...</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="agent in agents"
        :key="agent.id"
        @click="selectAgent(agent)"
        :class="[
          'cursor-pointer transition-all hover:shadow-md',
          selectedAgent === agent.name ? 'border-primary ring-2 ring-primary' : ''
        ]"
      >
        <CardHeader>
          <div class="flex items-center gap-3">
            <Avatar class="h-12 w-12">
              <AvatarFallback :style="{ backgroundColor: agent.avatar_color }">
                <span v-if="agent.avatar_url && isEmoji(agent.avatar_url)" class="text-2xl">
                  {{ agent.avatar_url }}
                </span>
                <img
                  v-else-if="agent.avatar_url"
                  :src="agent.avatar_url"
                  alt="avatar"
                  class="w-full h-full object-cover"
                />
                <Bot v-else class="h-6 w-6" />
              </AvatarFallback>
            </Avatar>
            <div class="flex-1 min-w-0">
              <h4 class="font-semibold truncate">{{ agent.display_name }}</h4>
              <p v-if="agent.description" class="text-xs text-muted-foreground line-clamp-2">
                {{ agent.description }}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent v-if="agent.personality_traits.length > 0">
          <div class="flex flex-wrap gap-1">
            <Badge
              v-for="trait in agent.personality_traits"
              :key="trait"
              variant="secondary"
              class="text-xs"
            >
              {{ trait }}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

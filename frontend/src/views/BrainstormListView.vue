<template>
  <div class="container mx-auto py-6">
    <!-- Agent Selector Dialog -->
    <Card v-if="showAgentSelector" class="p-6 mb-6">
      <AgentSelector @select="handleAgentSelected" />
      <div class="flex justify-end mt-4">
        <Button variant="ghost" @click="cancelAgentSelection">
          Cancel
        </Button>
      </div>
    </Card>

    <!-- Sessions List -->
    <div v-if="!showAgentSelector">
      <BrainstormList
        @create-session="handleCreate"
        @select-session="navigateToSession"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import BrainstormList from '@/components/BrainstormList.vue'
import AgentSelector from '@/components/AgentSelector.vue'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { AgentType } from '@/types/agent'

const router = useRouter()
const store = useBrainstormStore()

const showAgentSelector = ref(false)
const selectedAgent = ref<AgentType | null>(null)

async function handleCreate() {
  showAgentSelector.value = true
}

async function handleAgentSelected(agent: AgentType) {
  selectedAgent.value = agent

  try {
    // Create session without title/description - they will be inferred later
    const session = await store.createSession({})

    // TODO: Store selected agent with session (future enhancement)

    router.push(`/brainstorm/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
  } finally {
    showAgentSelector.value = false
  }
}

function cancelAgentSelection() {
  showAgentSelector.value = false
  selectedAgent.value = null
}

function navigateToSession(id: string) {
  router.push(`/brainstorm/${id}`)
}
</script>

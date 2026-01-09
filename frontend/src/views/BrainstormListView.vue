<template>
  <div class="container mx-auto py-6">
    <BrainstormList
      @create-session="handleCreate"
      @select-session="navigateToSession"
    />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import BrainstormList from '@/components/BrainstormList.vue'

const router = useRouter()
const store = useBrainstormStore()

async function handleCreate() {
  try {
    // Create session without title/description - they will be inferred later
    const session = await store.createSession({})
    router.push(`/brainstorm/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
  }
}

function navigateToSession(id: string) {
  router.push(`/brainstorm/${id}`)
}
</script>

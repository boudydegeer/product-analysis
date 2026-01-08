<template>
  <div class="h-full flex flex-col">
    <div class="border-b p-4">
      <Button variant="ghost" size="sm" @click="router.back()">
        <ArrowLeft class="mr-2 h-4 w-4" />
        Back to Sessions
      </Button>
    </div>

    <div class="flex-1 overflow-hidden">
      <BrainstormChat :session-id="sessionId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import BrainstormChat from '@/components/BrainstormChat.vue'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const sessionId = route.params.id as string
</script>

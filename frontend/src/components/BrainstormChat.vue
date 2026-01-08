<template>
  <div class="flex flex-col h-full">
    <!-- Session Header -->
    <div v-if="currentSession" class="border-b p-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold">{{ currentSession.title }}</h2>
          <p class="text-sm text-muted-foreground">
            {{ currentSession.description }}
          </p>
        </div>
        <Badge :variant="getStatusVariant(currentSession.status)">
          {{ currentSession.status }}
        </Badge>
      </div>
    </div>

    <!-- Messages Container -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4"
    >
      <!-- Messages -->
      <div
        v-for="message in currentSession?.messages || []"
        :key="message.id"
        :class="[
          'flex',
          message.role === 'user' ? 'justify-end' : 'justify-start',
        ]"
      >
        <div
          :class="[
            'max-w-[80%] rounded-lg p-4',
            message.role === 'user'
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted',
          ]"
        >
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>
                {{ message.role === 'user' ? 'You' : 'AI' }}
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ message.role === 'user' ? 'You' : 'Claude' }}
            </span>
          </div>
          <p class="whitespace-pre-wrap">{{ message.content }}</p>
        </div>
      </div>

      <!-- Streaming Message -->
      <div v-if="streaming" class="flex justify-start">
        <div class="max-w-[80%] rounded-lg p-4 bg-muted">
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">Claude</span>
          </div>
          <p class="whitespace-pre-wrap">
            {{ streamingContent }}
            <span class="animate-pulse">▊</span>
          </p>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center py-8">
        <p class="text-muted-foreground">Loading session...</p>
      </div>
    </div>

    <!-- Input Form -->
    <div class="border-t p-4">
      <form @submit.prevent="handleSendMessage" class="flex gap-2">
        <Textarea
          v-model="userMessage"
          placeholder="Share your thoughts..."
          :disabled="streaming || loading || !isActive"
          @keydown.enter.exact.prevent="handleSendMessage"
          class="flex-1 resize-none"
          rows="3"
        />
        <Button
          type="submit"
          :disabled="streaming || loading || !userMessage.trim() || !isActive"
          size="icon"
          class="self-end"
        >
          <Send class="h-4 w-4" />
        </Button>
      </form>
      <p v-if="!isActive" class="text-xs text-muted-foreground mt-2">
        This session is not active
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useBrainstormStore } from '@/stores/brainstorm'
import { brainstormsApi } from '@/api/brainstorms'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send } from 'lucide-vue-next'
import type { StreamChunk } from '@/types/brainstorm'

const props = defineProps<{
  sessionId: string
}>()

const store = useBrainstormStore()
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()

const currentSession = computed(() => store.currentSession)
const loading = computed(() => store.loading)
const streaming = computed(() => store.streaming)
const streamingContent = computed(() => store.streamingContent)
const isActive = computed(() => store.isActive)

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

async function handleSendMessage() {
  if (!userMessage.value.trim() || !currentSession.value) return

  const message = userMessage.value
  userMessage.value = ''

  // Add user message to UI immediately
  store.addMessage({
    id: crypto.randomUUID(),
    session_id: currentSession.value.id,
    role: 'user',
    content: message,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })

  try {
    store.setStreaming(true)
    store.clearStreamingContent()

    const eventSource = brainstormsApi.streamBrainstorm(
      currentSession.value.id,
      message
    )

    eventSource.addEventListener('message', (event: MessageEvent) => {
      const data: StreamChunk = JSON.parse(event.data)

      if (data.type === 'chunk' && data.content) {
        store.appendStreamingContent(data.content)
        scrollToBottom()
      } else if (data.type === 'done') {
        eventSource.close()

        // Add assistant message
        if (streamingContent.value) {
          store.addMessage({
            id: crypto.randomUUID(),
            session_id: currentSession.value!.id,
            role: 'assistant',
            content: streamingContent.value,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          })
        }

        store.setStreaming(false)
        store.clearStreamingContent()
      } else if (data.type === 'error') {
        eventSource.close()
        store.setStreaming(false)
        console.error('Streaming error:', data.message)
      }
    })

    eventSource.addEventListener('error', () => {
      eventSource.close()
      store.setStreaming(false)
      console.error('EventSource connection failed')
    })
  } catch (error) {
    store.setStreaming(false)
    console.error('Failed to send message:', error)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(
  () => currentSession.value?.messages.length,
  () => {
    scrollToBottom()
  }
)

onMounted(async () => {
  await store.fetchSession(props.sessionId)
  scrollToBottom()
})
</script>

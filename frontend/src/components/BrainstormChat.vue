<template>
  <div class="h-full grid grid-rows-[auto_1fr_auto] overflow-hidden">
    <!-- Session Header - Fixed at top -->
    <div v-if="currentSession" class="border-b px-4 py-3 bg-background">
      <div class="flex items-start gap-3">
        <Button variant="ghost" size="icon" @click="router.back()" class="shrink-0">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div class="flex-1 min-w-0">
          <div class="flex flex-col items-baseline gap-2">
            <h2 class="text-lg font-semibold truncate">{{ currentSession.title }}</h2>
            <span class="text-sm text-muted-foreground truncate">{{ currentSession.description }}</span>
          </div>
        </div>
        <Badge :variant="getStatusVariant(currentSession.status)" class="shrink-0">
          {{ currentSession.status }}
        </Badge>
      </div>
    </div>

    <!-- Messages Container - Scrollable area -->
    <div
      ref="messagesContainer"
      class="overflow-y-auto overflow-x-hidden p-4 space-y-4"
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

    <!-- Input Form - Fixed at bottom -->
    <div class="border-t p-4 bg-background">
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
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import { brainstormsApi } from '@/api/brainstorms'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send, ArrowLeft } from 'lucide-vue-next'
import type { StreamChunk } from '@/types/brainstorm'

const props = defineProps<{
  sessionId: string
}>()

const router = useRouter()
const store = useBrainstormStore()
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()
const currentEventSource = ref<EventSource | null>(null)

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

function cleanupEventSource() {
  console.log('[FRONTEND] cleanupEventSource called')
  if (currentEventSource.value) {
    console.log('[FRONTEND] Closing EventSource')
    currentEventSource.value.close()
    currentEventSource.value = null
  }
  console.log('[FRONTEND] Setting streaming = false')
  store.setStreaming(false)
}

async function handleSendMessage() {
  console.log('[FRONTEND] handleSendMessage called')
  if (!userMessage.value.trim() || !currentSession.value) {
    console.log('[FRONTEND] Early return: empty message or no session')
    return
  }

  const message = userMessage.value
  console.log('[FRONTEND] Message:', message, 'Session:', currentSession.value.id)
  userMessage.value = ''

  // Add user message to UI immediately
  console.log('[FRONTEND] Adding user message to store')
  store.addMessage({
    id: crypto.randomUUID(),
    session_id: currentSession.value.id,
    role: 'user',
    content: message,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })

  // Cleanup any existing connection
  console.log('[FRONTEND] Cleaning up existing EventSource')
  cleanupEventSource()

  let eventSource: EventSource | null = null

  try {
    console.log('[FRONTEND] Setting streaming = true')
    store.setStreaming(true)
    store.clearStreamingContent()

    console.log('[FRONTEND] Creating EventSource...')
    eventSource = brainstormsApi.streamBrainstorm(
      currentSession.value.id,
      message
    )
    currentEventSource.value = eventSource
    console.log('[FRONTEND] EventSource created, URL:', eventSource.url)

    eventSource.addEventListener('message', (event: MessageEvent) => {
      console.log('[FRONTEND] Received SSE message:', event.data)
      try {
        const data: StreamChunk = JSON.parse(event.data)
        console.log('[FRONTEND] Parsed data:', data)

        if (data.type === 'chunk' && data.content) {
          console.log('[FRONTEND] Chunk received, length:', data.content.length)
          store.appendStreamingContent(data.content)
          scrollToBottom()
        } else if (data.type === 'done') {
          console.log('[FRONTEND] Stream completed, adding assistant message')

          // Add assistant message to UI
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

          // Clear streaming state and cleanup
          store.clearStreamingContent()
          cleanupEventSource()

          console.log('Assistant message added, input should be re-enabled')
        } else if (data.type === 'error') {
          console.error('[FRONTEND] Streaming error from server:', data.message)
          cleanupEventSource()
        }
      } catch (parseError) {
        console.error('[FRONTEND] Failed to parse SSE message:', parseError, 'Raw data:', event.data)
        cleanupEventSource()
      }
    })

    eventSource.addEventListener('error', (error) => {
      console.error('[FRONTEND] EventSource connection failed:', error)
      console.error('[FRONTEND] EventSource readyState:', eventSource?.readyState)
      cleanupEventSource()
    })

    eventSource.addEventListener('open', () => {
      console.log('[FRONTEND] EventSource connection opened successfully')
    })
  } catch (error) {
    console.error('[FRONTEND] Failed to send message (caught exception):', error)
    cleanupEventSource()
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

onBeforeUnmount(() => {
  // Cleanup EventSource when component is destroyed
  cleanupEventSource()
  store.clearStreamingContent()
})
</script>

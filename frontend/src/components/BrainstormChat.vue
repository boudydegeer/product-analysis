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
        v-for="(message, index) in currentSession?.messages || []"
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
              <AvatarFallback :class="message.role === 'assistant' ? 'bg-primary/40' : ''">
                <User v-if="message.role === 'user'" class="h-5 w-5" />
                <Bot v-else class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ message.role === 'user' ? 'You' : 'Claude' }}
            </span>
          </div>
          <div class="space-y-2">
            <template
              v-for="block in message.content.blocks"
              :key="block.id"
            >
              <component
                :is="getBlockComponent(block.type)"
                :block="block as any"
                :interactive="message.role === 'assistant' && index === (currentSession?.messages.length || 0) - 1"
                @interact="handleInteraction"
                @skip="handleSkip"
              />
            </template>
          </div>
        </div>
      </div>

      <!-- Streaming Message or Waiting for Response -->
      <div v-if="store.streamingMessageId || waitingForResponse" class="flex justify-start">
        <div class="max-w-[80%] rounded-lg p-4 bg-muted">
          <div class="flex items-center gap-2 mb-2">
            <Avatar class="h-6 w-6">
              <AvatarFallback class="bg-primary/40">
                <Bot class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">Claude</span>
          </div>
          <div class="space-y-2">
            <template
              v-for="block in store.pendingBlocks"
              :key="block.id"
            >
              <component
                :is="getBlockComponent(block.type)"
                :block="block as any"
                :interactive="interactiveElementsActive"
                @interact="handleInteraction"
                @skip="handleSkip"
              />
            </template>
            <div v-if="store.pendingBlocks.length === 0" class="flex items-center gap-2 text-sm text-muted-foreground">
              <div class="flex gap-1">
                <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.3s]"></div>
                <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.15s]"></div>
                <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce"></div>
              </div>
              <span>Thinking...</span>
            </div>
          </div>
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
          ref="messageInput"
          v-model="userMessage"
          placeholder="Share your thoughts..."
          :disabled="store.streamingMessageId !== null || loading || !isActive || interactiveElementsActive"
          @keydown.enter.exact.prevent="handleSendMessage"
          class="flex-1 resize-none"
          rows="3"
        />
        <Button
          type="submit"
          :disabled="store.streamingMessageId !== null || loading || !userMessage.trim() || !isActive || interactiveElementsActive"
          size="icon"
          class="self-end"
        >
          <Send class="h-4 w-4" />
        </Button>
      </form>
      <p v-if="!isActive" class="text-xs text-muted-foreground mt-2">
        This session is not active
      </p>
      <p v-if="interactiveElementsActive" class="text-xs text-muted-foreground mt-2">
        Please respond to the interactive element above
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useBrainstormStore } from '@/stores/brainstorm'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Send, ArrowLeft, Bot, User } from 'lucide-vue-next'
import type { Block, WSServerMessage, WSUserMessage, WSInteraction, MessageContent } from '@/types/brainstorm'
import TextBlock from '@/components/brainstorm/blocks/TextBlock.vue'
import ButtonGroupBlock from '@/components/brainstorm/blocks/ButtonGroupBlock.vue'
import MultiSelectBlock from '@/components/brainstorm/blocks/MultiSelectBlock.vue'
import InteractionResponseBlock from '@/components/brainstorm/blocks/InteractionResponseBlock.vue'

const props = defineProps<{
  sessionId: string
}>()

const router = useRouter()
const store = useBrainstormStore()
const userMessage = ref('')
const messagesContainer = ref<HTMLDivElement>()
const messageInput = ref<HTMLTextAreaElement>()
const ws = ref<WebSocket | null>(null)
const waitingForResponse = ref(false)

const currentSession = computed(() => store.currentSession)
const loading = computed(() => store.loading)
const isActive = computed(() => store.isActive)
const interactiveElementsActive = computed(() => store.interactiveElementsActive)

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

function getBlockComponent(type: string) {
  switch (type) {
    case 'text':
      return TextBlock
    case 'button_group':
      return ButtonGroupBlock
    case 'multi_select':
      return MultiSelectBlock
    case 'interaction_response':
      return InteractionResponseBlock
    default:
      return TextBlock
  }
}

function connectWebSocket() {
  if (!currentSession.value) {
    console.error('[WS] Cannot connect: no session')
    return
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8891'
  const wsUrl = `${protocol}//${host}/api/v1/brainstorms/ws/${currentSession.value.id}`

  console.log('[WS] Connecting to:', wsUrl)

  try {
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('[WS] Connected')
      store.setWsConnected(true)
    }

    ws.value.onmessage = (event) => {
      console.log('[WS] Received message:', event.data)
      try {
        const data: WSServerMessage = JSON.parse(event.data)
        handleServerMessage(data)
      } catch (error) {
        console.error('[WS] Failed to parse message:', error, 'Raw:', event.data)
      }
    }

    ws.value.onerror = (error) => {
      console.error('[WS] Error:', error)
      store.setWsConnected(false)
    }

    ws.value.onclose = () => {
      console.log('[WS] Disconnected')
      store.setWsConnected(false)
    }
  } catch (error) {
    console.error('[WS] Failed to create WebSocket:', error)
    store.setWsConnected(false)
  }
}

function handleServerMessage(data: WSServerMessage) {
  switch (data.type) {
    case 'stream_chunk':
      console.log('[WS] Stream chunk received for message:', data.message_id)

      // Clear waiting state when first block arrives
      waitingForResponse.value = false

      // Start streaming if not already started
      if (!store.streamingMessageId) {
        store.startStreamingMessage(data.message_id)
      }

      // Append block to pending blocks
      store.appendBlock(data.block)
      scrollToBottom()
      break

    case 'stream_complete':
      console.log('[WS] Stream complete for message:', data.message_id)
      waitingForResponse.value = false
      store.completeStreamingMessage()
      scrollToBottom()
      break

    case 'error':
      console.error('[WS] Server error:', data.message)
      waitingForResponse.value = false
      store.clearInteractiveState()
      break

    default:
      console.warn('[WS] Unknown message type:', (data as any).type)
  }
}

function handleSendMessage() {
  if (!userMessage.value.trim() || !ws.value || ws.value.readyState !== WebSocket.OPEN) {
    console.log('[WS] Cannot send: empty message or WebSocket not open')
    return
  }

  const message = userMessage.value.trim()
  console.log('[WS] Sending message:', message)

  // Add user message to UI immediately
  const userMessageObj: MessageContent = {
    blocks: [
      {
        id: crypto.randomUUID(),
        type: 'text',
        text: message,
      },
    ],
  }

  store.addMessage({
    id: crypto.randomUUID(),
    session_id: currentSession.value!.id,
    role: 'user',
    content: userMessageObj,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })

  // Send to WebSocket
  const wsMessage: WSUserMessage = {
    type: 'user_message',
    content: message,
  }

  ws.value.send(JSON.stringify(wsMessage))
  userMessage.value = ''

  // Set waiting state
  waitingForResponse.value = true

  // Clear interactive state since we're sending a new message
  store.clearInteractiveState()
  scrollToBottom()
}

function handleInteraction(blockId: string, value: string | string[]) {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    console.error('[WS] Cannot send interaction: WebSocket not open')
    return
  }

  console.log('[WS] Sending interaction:', blockId, value)

  const interaction: WSInteraction = {
    type: 'interaction',
    block_id: blockId,
    value,
  }

  ws.value.send(JSON.stringify(interaction))

  // Set waiting state
  waitingForResponse.value = true

  // Clear interactive state since we've responded
  store.clearInteractiveState()
}

function handleSkip() {
  console.log('[WS] Skipping interactive elements')
  store.clearInteractiveState()

  // Focus on input after clearing interactive state
  nextTick(() => {
    messageInput.value?.focus()
  })
}

function cleanup() {
  console.log('[WS] Cleanup called')
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  store.setWsConnected(false)
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

watch(
  () => store.pendingBlocks.length,
  () => {
    scrollToBottom()
  }
)

onMounted(async () => {
  await store.fetchSession(props.sessionId)
  connectWebSocket()
  scrollToBottom()
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

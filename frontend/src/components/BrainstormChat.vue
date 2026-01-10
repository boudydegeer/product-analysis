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
          </div>3
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
              <AvatarFallback
                :class="message.role === 'assistant' ? '' : ''"
                :style="message.role === 'assistant' && currentAgentConfig
                  ? { backgroundColor: currentAgentConfig.avatar_color }
                  : {}"
              >
                <!-- Agent avatar -->
                <template v-if="message.role === 'assistant' && currentAgentConfig">
                  <span v-if="isEmoji(currentAgentConfig.avatar_url || '')" class="text-base">
                    {{ currentAgentConfig.avatar_url }}
                  </span>
                  <img
                    v-else-if="currentAgentConfig.avatar_url"
                    :src="currentAgentConfig.avatar_url"
                    alt="avatar"
                    class="w-full h-full object-cover"
                  />
                  <Bot v-else class="h-5 w-5" />
                </template>
                <!-- User avatar -->
                <User v-if="message.role === 'user'" class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ message.role === 'user' ? 'You' : (currentAgentConfig?.display_name || 'Claude') }}
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
              <AvatarFallback
                :style="currentAgentConfig
                  ? { backgroundColor: currentAgentConfig.avatar_color }
                  : { backgroundColor: '#6366f1' }"
              >
                <span v-if="currentAgentConfig && isEmoji(currentAgentConfig.avatar_url || '')" class="text-base">
                  {{ currentAgentConfig.avatar_url }}
                </span>
                <img
                  v-else-if="currentAgentConfig?.avatar_url"
                  :src="currentAgentConfig.avatar_url"
                  alt="avatar"
                  class="w-full h-full object-cover"
                />
                <Bot v-else class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span class="text-xs font-semibold">
              {{ currentAgentConfig?.display_name || 'Claude' }}
            </span>
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
            <!-- Tool Execution Status -->
            <ToolExecutionStatus
              v-if="activeToolExecution"
              :execution="activeToolExecution"
            />
            <div v-if="store.pendingBlocks.length === 0 && !activeToolExecution" class="flex items-center gap-2 text-sm text-muted-foreground">
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
import type { Block, WSServerMessage, WSUserMessage, WSInteraction, MessageContent, WSUserMessageSaved } from '@/types/brainstorm'
import TextBlock from '@/components/brainstorm/blocks/TextBlock.vue'
import ButtonGroupBlock from '@/components/brainstorm/blocks/ButtonGroupBlock.vue'
import MultiSelectBlock from '@/components/brainstorm/blocks/MultiSelectBlock.vue'
import InteractionResponseBlock from '@/components/brainstorm/blocks/InteractionResponseBlock.vue'
import ToolExecutionStatus from '@/components/brainstorm/ToolExecutionStatus.vue'

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
const currentAgentConfig = computed(() => store.currentAgentConfig)
const activeToolExecution = computed(() => store.activeToolExecution)

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

function isEmoji(str: string): boolean {
  return /\p{Emoji}/u.test(str)
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
    case 'user_message_saved':
      console.log('[WS] User message saved:', (data as WSUserMessageSaved).message)
      // Add the saved user message to the store
      store.addMessage((data as WSUserMessageSaved).message)
      scrollToBottom()
      break

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
      store.clearToolExecution()
      break

    case 'tool_executing':
      console.log('[WS] Tool executing:', data)
      store.setToolExecuting({
        tool_name: (data as any).tool_name,
        exploration_id: (data as any).exploration_id,
        status: (data as any).status as 'pending' | 'executing' | 'completed' | 'failed',
        message: (data as any).message,
        started_at: new Date().toISOString()
      })
      // Clear tool execution when completed or failed
      if ((data as any).status === 'completed' || (data as any).status === 'failed') {
        setTimeout(() => {
          store.clearToolExecution()
        }, 2000) // Show completion status briefly before clearing
      }
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

  // Send to WebSocket (backend will send back the saved message)
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
    // Access the underlying textarea element - the ref is the component instance
    // which may expose $el or be the element directly
    const textareaRef = messageInput.value
    if (textareaRef) {
      // Try to get the native element - could be wrapped component or direct element
      const el = (textareaRef as any).$el || textareaRef
      if (el && typeof el.focus === 'function') {
        el.focus()
      }
    }
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

  // Load agent config (default to 'brainstorm')
  await store.fetchAgentConfig('brainstorm')

  connectWebSocket()
  scrollToBottom()
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

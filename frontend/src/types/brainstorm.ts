/**
 * Brainstorm session and message types
 */

// Base block types
export type BlockType = 'text' | 'button_group' | 'multi_select' | 'interaction_response'

export interface BaseBlock {
  id: string
  type: BlockType
}

export interface TextBlock extends BaseBlock {
  type: 'text'
  text: string
}

export interface ButtonOption {
  id: string
  label: string
  style?: 'primary' | 'secondary' | 'outline'
}

export interface ButtonGroupBlock extends BaseBlock {
  type: 'button_group'
  label?: string
  buttons: ButtonOption[]
  allow_multiple?: boolean
}

export interface SelectOption {
  id: string
  label: string
  description?: string
}

export interface MultiSelectBlock extends BaseBlock {
  type: 'multi_select'
  prompt: string
  options: SelectOption[]
  min?: number
  max?: number
}

export interface InteractionResponseBlock extends BaseBlock {
  type: 'interaction_response'
  block_id: string
  value: string | string[]
}

export type Block = TextBlock | ButtonGroupBlock | MultiSelectBlock | InteractionResponseBlock

// Message structure
export interface MessageContent {
  blocks: Block[]
  metadata?: {
    thinking?: string
    suggested_next?: string[]
  }
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: MessageContent
  created_at: string
  updated_at: string
}

// WebSocket message types
export interface WSUserMessage {
  type: 'user_message'
  content: string
}

export interface WSInteraction {
  type: 'interaction'
  block_id: string
  value: string | string[]
}

export interface WSStreamChunk {
  type: 'stream_chunk'
  message_id: string
  block: Block
}

export interface WSStreamComplete {
  type: 'stream_complete'
  message_id: string
}

export interface WSError {
  type: 'error'
  message: string
}

// Tool execution tracking
export interface ToolExecution {
  tool_name: string
  exploration_id?: string
  status: 'pending' | 'executing' | 'completed' | 'failed'
  message?: string
  started_at: string
  completed_at?: string
}

// WebSocket message for tool execution
export interface WSToolExecuting {
  type: 'tool_executing'
  tool_name: string
  exploration_id?: string
  status: string
  message?: string
}

// WebSocket message for user message saved confirmation
export interface WSUserMessageSaved {
  type: 'user_message_saved'
  message: Message
}

export type WSServerMessage = WSStreamChunk | WSStreamComplete | WSError | WSToolExecuting | WSUserMessageSaved
export type WSClientMessage = WSUserMessage | WSInteraction

// Session types
export type BrainstormSessionStatus = 'active' | 'paused' | 'completed' | 'archived'
export type MessageRole = 'user' | 'assistant'

export interface BrainstormSession {
  id: string
  title: string
  description: string
  status: BrainstormSessionStatus
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface BrainstormSessionCreate {
  title?: string
  description?: string
}

export interface BrainstormSessionUpdate {
  title?: string
  description?: string
  status?: BrainstormSessionStatus
}

// Legacy types (deprecated - for backward compatibility)
export interface BrainstormMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  created_at: string
  updated_at: string
}

export interface StreamChunk {
  type: 'chunk' | 'done' | 'error'
  content?: string
  message?: string
}

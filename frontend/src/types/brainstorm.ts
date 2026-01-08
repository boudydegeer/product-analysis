/**
 * Brainstorm session and message types
 */

export type BrainstormSessionStatus = 'active' | 'paused' | 'completed' | 'archived'
export type MessageRole = 'user' | 'assistant'

export interface BrainstormMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  created_at: string
  updated_at: string
}

export interface BrainstormSession {
  id: string
  title: string
  description: string
  status: BrainstormSessionStatus
  messages: BrainstormMessage[]
  created_at: string
  updated_at: string
}

export interface BrainstormSessionCreate {
  title: string
  description: string
}

export interface BrainstormSessionUpdate {
  title?: string
  description?: string
  status?: BrainstormSessionStatus
}

export interface StreamChunk {
  type: 'chunk' | 'done' | 'error'
  content?: string
  message?: string
}

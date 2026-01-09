/**
 * Agent type definition with personalization.
 */
export interface AgentType {
  id: number
  name: string
  display_name: string
  description?: string
  avatar_url?: string
  avatar_color: string
  personality_traits: string[]
  model: string
  temperature: number
}

/**
 * Tool definition.
 */
export interface Tool {
  name: string
  description: string
  category: string
}

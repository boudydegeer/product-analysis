/**
 * Idea management types
 */

export type IdeaStatus = 'backlog' | 'under_review' | 'approved' | 'rejected' | 'implemented'
export type IdeaPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Idea {
  id: string
  title: string
  description: string
  status: IdeaStatus
  priority: IdeaPriority
  business_value: number | null
  technical_complexity: number | null
  estimated_effort: string | null
  market_fit_analysis: string | null
  risk_assessment: string | null
  created_at: string
  updated_at: string
}

export interface IdeaCreate {
  title: string
  description: string
  priority?: IdeaPriority
}

export interface IdeaUpdate {
  title?: string
  description?: string
  status?: IdeaStatus
  priority?: IdeaPriority
  business_value?: number
  technical_complexity?: number
  estimated_effort?: string
  market_fit_analysis?: string
  risk_assessment?: string
}

export interface IdeaEvaluationRequest {
  title: string
  description: string
  context?: string
}

export interface IdeaEvaluationResponse {
  business_value: number
  technical_complexity: number
  estimated_effort: string
  market_fit_analysis: string
  risk_assessment: string
}

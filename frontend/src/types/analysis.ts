export type AnalysisStatus = 'completed' | 'no_analysis' | 'failed' | 'analyzing'

export interface AnalysisOverview {
  summary: string
  key_points: string[]
  metrics: {
    complexity?: string
    estimated_effort?: string
    confidence?: number
    [key: string]: any
  }
}

export interface ArchitectureInfo {
  pattern?: string
  components?: string[]
  [key: string]: any
}

export interface TechnicalDetail {
  category: string
  description: string
  code_locations?: string[]
}

export interface DataFlow {
  description?: string
  steps?: string[]
  [key: string]: any
}

export interface AnalysisImplementation {
  architecture: Record<string, any>
  technical_details: Array<Record<string, any>>
  data_flow: Record<string, any>
}

export interface Risk {
  severity: string
  category?: string
  description: string
  impact?: string
  cwe?: string
  recommendation?: string
}

export interface AnalysisRisks {
  technical_risks: Risk[]
  security_concerns: Risk[]
  scalability_issues: Risk[]
  mitigation_strategies: string[]
}

export interface Improvement {
  priority: string
  title: string
  description: string
  effort?: string
}

export interface AnalysisRecommendations {
  improvements: Improvement[]
  best_practices: string[]
  next_steps: string[]
}

export interface AnalysisDetail {
  feature_id: string
  feature_name: string
  analyzed_at: string | null
  status: AnalysisStatus
  overview: AnalysisOverview
  implementation: AnalysisImplementation
  risks: AnalysisRisks
  recommendations: AnalysisRecommendations
}

export interface AnalysisError {
  feature_id: string
  status: 'no_analysis' | 'failed' | 'analyzing'
  message: string
  failed_at?: string | null
  started_at?: string | null
}

export type AnalysisResponse = AnalysisDetail | AnalysisError

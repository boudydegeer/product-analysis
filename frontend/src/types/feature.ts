export enum FeatureStatus {
  DRAFT = 'draft',
  ANALYZING = 'analyzing',
  ANALYZED = 'analyzed',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
}

export interface Feature {
  id: string
  name: string
  description: string
  status: FeatureStatus
  github_workflow_run_id?: string
  created_at: string
  updated_at: string
}

export interface FeatureCreate {
  id: string
  name: string
  description: string
}

export interface FeatureUpdate {
  name?: string
  description?: string
  status?: FeatureStatus
}

export interface Analysis {
  id: number
  feature_id: string
  workflow_run_id: string
  workflow_run_number: number
  analyzed_at: string
  story_points: number
  estimated_hours: number
  prerequisite_hours: number
  total_hours: number
  complexity_level: string
  rationale: string
  repository_maturity: string
  warnings: unknown[]
  repository_state: unknown
  affected_modules: unknown[]
  implementation_tasks: unknown[]
  technical_risks: unknown[]
  recommendations: unknown
  created_at: string
  updated_at: string
}

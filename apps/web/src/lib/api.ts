import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

/* =========================================================
   HEALTH
========================================================= */

export type HealthStatus = {
  status: string
}

export async function fetchHealth(): Promise<HealthStatus> {
  const { data } = await apiClient.get<HealthStatus>('/health')
  return data
}

/* =========================================================
   REPOSITORY
========================================================= */

export type Repository = {
  project_id: string
  name: string
  original_filename: string
  created_at: string
  archive_size_bytes: number
  extracted_size_bytes: number
  file_count: number
  supported_languages: string[]
  status: string
}

/* =========================================================
   DASHBOARD
========================================================= */

export type Score = {
  score: number
  label: string
  description: string
}

export type LanguageItem = {
  language: string
  file_count: number
  percentage: number
}

export type GraphEdge = {
  source: string
  target: string
  relationship: string
}

export type DiagramNode = {
  id: string
  label: string
  kind: string
}

export type ArchitectureDiagram = {
  nodes: DiagramNode[]
  edges: GraphEdge[]
}

export type Insight = {
  title: string
  detail: string
  severity: string
}

export type TimelineEvent = {
  timestamp: string
  title: string
  detail: string
}

export type DashboardData = {
  project_id: string
  health_score: Score
  security_score: Score
  complexity_score: Score
  technical_debt_score: Score
  statistics: Record<string, number>
  language_distribution: LanguageItem[]
  dependency_graph: GraphEdge[]
  architecture_diagram: ArchitectureDiagram
  ai_insights: Insight[]
  timeline: TimelineEvent[]
}

/* =========================================================
   ONBOARDING / KNOWLEDGE
========================================================= */

export type OnboardingContext = {
  file_path: string
  chunk_id: string
  content: string
  relevance_score?: number
}

export type OnboardingGuide = {
  project_id: string
  guide: string
  context: OnboardingContext[]
}

/* =========================================================
   GENERAL AI ASSISTANT
========================================================= */

export type AssistantResponse = {
  project_id: string
  task: string
  answer: string
  context: OnboardingContext[]
}

/* =========================================================
   MULTI-AGENT SYSTEM
========================================================= */

export type AgentName =
  | 'repository_analysis'
  | 'architecture'
  | 'code_review'
  | 'security'
  | 'documentation'
  | 'testing'

export type AgentStatus = 'completed' | 'failed' | 'skipped'

export type AgentOutput = {
  agent: AgentName
  status: AgentStatus
  content: string
  error?: string | null
}

export type AgentExecutionResponse = {
  project_id: string
  request: string
  selected_agents: AgentName[]
  outputs: AgentOutput[]
  execution_log: string[]
}

/* =========================================================
   REPOSITORY API
========================================================= */

export async function fetchRepositories(): Promise<Repository[]> {
  const { data } = await apiClient.get<{
    repositories: Repository[]
  }>('/api/v1/repositories')

  return data.repositories
}

export async function uploadRepository(
  file: File,
  onProgress: (percent: number) => void,
): Promise<Repository> {
  const body = new FormData()

  body.append('file', file)

  const { data } = await apiClient.post<Repository>(
    '/api/v1/repositories/upload',
    body,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (event) => {
        if (event.total) {
          onProgress(
            Math.round((event.loaded / event.total) * 100),
          )
        }
      },
    },
  )

  return data
}

/* =========================================================
   REPOSITORY DASHBOARD API
========================================================= */

export async function fetchRepositoryDashboard(
  projectId: string,
): Promise<DashboardData> {
  const { data } = await apiClient.get<DashboardData>(
    `/api/v1/repositories/${projectId}/dashboard`,
  )

  return data
}

/* =========================================================
   ONBOARDING API
========================================================= */

export async function generateOnboarding(
  projectId: string,
  question: string,
): Promise<OnboardingGuide> {
  const { data } = await apiClient.post<OnboardingGuide>(
    `/api/v1/repositories/${projectId}/onboarding`,
    {
      question,
      context_limit: 8,
    },
  )

  return data
}

/* =========================================================
   GENERAL AI ASSISTANT API
========================================================= */

export async function askAssistant(
  projectId: string,
  task: string,
  question: string,
): Promise<AssistantResponse> {
  const { data } = await apiClient.post<AssistantResponse>(
    `/api/v1/repositories/${projectId}/assistant/${task}`,
    {
      question,
      context_limit: 8,
    },
  )

  return data
}

/* =========================================================
   MULTI-AGENT EXECUTION API
========================================================= */

export async function executeAgents(
  projectId: string,
  request: string,
): Promise<AgentExecutionResponse> {
  const { data } = await apiClient.post<AgentExecutionResponse>(
    '/api/v1/agents/execute',
    {
      project_id: projectId,
      request,
    },
  )

  return data
}
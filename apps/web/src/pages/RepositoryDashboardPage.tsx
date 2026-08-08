import { useQuery } from '@tanstack/react-query'
import { Activity, BarChart3, FileCode2, RefreshCw } from 'lucide-react'
import { useParams } from 'react-router-dom'

import {
  ArchitectureGraph,
  DependencyGraph,
} from '../components/repository-dashboard/GraphPanels'
import {
  Insights,
  Timeline,
} from '../components/repository-dashboard/InsightTimeline'
import { LanguageChart } from '../components/repository-dashboard/LanguageChart'
import { ScoreCard } from '../components/repository-dashboard/ScoreCard'
import {
  ErrorState,
  LoadingSkeletons,
} from '../components/states/StatusStates'
import { Card } from '../components/ui/Card'
import { fetchRepositoryDashboard } from '../lib/api'

const metricLabels: Record<string, string> = {
  files: 'Files',
  classes: 'Classes',
  interfaces: 'Interfaces',
  functions: 'Functions',
  methods: 'Methods',
  imports: 'Imports',
  comments: 'Comments',
  api_endpoints: 'API endpoints',
  configuration_files: 'Config files',
}

export function RepositoryDashboardPage() {
  const { projectId = '' } = useParams()

  const query = useQuery({
    queryKey: ['repository-dashboard', projectId],
    queryFn: () => fetchRepositoryDashboard(projectId),
    enabled: Boolean(projectId),
  })

  if (query.isLoading) {
    return <LoadingSkeletons />
  }

  if (query.isError || !query.data) {
    return (
      <ErrorState
        message="Could not load the repository dashboard. Generate repository intelligence and try again."
        retry={() => query.refetch()}
      />
    )
  }

  const data = query.data

  return (
    <>
      {/* Header */}
      <div className="mb-7 flex items-start gap-3">
        <div className="rounded-md bg-blue-500/10 p-2 text-blue-400">
          <Activity className="size-5" />
        </div>

        <div>
          <p className="text-sm text-blue-400">
            REPOSITORY INTELLIGENCE
          </p>

          <h1 className="mt-1 text-2xl font-semibold">
            Enterprise repository dashboard
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            Project {data.project_id}
          </p>
        </div>

        <button
          type="button"
          onClick={() => query.refetch()}
          disabled={query.isFetching}
          className="ml-auto inline-flex items-center gap-2 rounded-md border border-[#30363d] bg-[#161b22] px-3 py-2 text-sm text-slate-300 transition hover:border-blue-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`size-4 ${query.isFetching ? 'animate-spin' : ''}`}
          />
          Refresh
        </button>
      </div>

      {/* Score Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <ScoreCard
          score={data.health_score}
          accent="#58a6ff"
        />

        <ScoreCard
          score={data.security_score}
          accent="#3fb950"
        />

        <ScoreCard
          score={data.complexity_score}
          accent="#a371f7"
        />

        <ScoreCard
          score={data.technical_debt_score}
          accent="#d29922"
        />
      </div>

      {/* Languages + Statistics */}
      <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_.9fr]">
        <LanguageChart
          data={data.language_distribution}
        />

        <Card className="p-5">
          <div className="flex items-center gap-2">
            <BarChart3 className="size-4 text-emerald-400" />

            <h2 className="font-medium">
              Repository statistics
            </h2>
          </div>

          {Object.keys(data.statistics).length === 0 ? (
            <p className="mt-5 text-sm text-slate-500">
              No repository statistics available.
            </p>
          ) : (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(data.statistics).map(
                ([key, value]) => (
                  <div
                    key={key}
                    className="rounded-md bg-[#0d1117] p-3"
                  >
                    <p className="text-xl font-semibold">
                      {value}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {metricLabels[key] ?? key}
                    </p>
                  </div>
                ),
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Dependency + Architecture */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <DependencyGraph
          edges={data.dependency_graph}
        />

        <ArchitectureGraph
          diagram={data.architecture_diagram}
        />
      </div>

      {/* AI Insights + Timeline */}
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Insights
          insights={data.ai_insights}
        />

        <Timeline
          events={data.timeline}
        />
      </div>

      {/* Explanation */}
      <Card className="mt-6 flex items-start gap-3 p-5">
        <FileCode2 className="mt-0.5 size-5 shrink-0 text-slate-400" />

        <div>
          <p className="text-sm font-medium text-slate-300">
            About these scores
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-400">
            Scores are explainable heuristics generated from
            extracted repository structure. Use the multi-agent
            workflow for deeper, context-grounded analysis.
          </p>
        </div>
      </Card>
    </>
  )
}
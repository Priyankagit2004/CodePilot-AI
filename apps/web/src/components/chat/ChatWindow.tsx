import { useMutation, useQuery } from '@tanstack/react-query'
import { BookOpen, Send, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import {
  executeAgents,
  fetchRepositories,
  type AgentExecutionResponse,
} from '../../lib/api'
import { Button } from '../ui/Button'

type Message = {
  role: 'user' | 'assistant'
  content: string
  agents?: string[]
  executionLog?: string[]
}

const defaultQuestion = "I'm new to this repository."

export function ChatWindow() {
  const [message, setMessage] = useState('')
  const [projectId, setProjectId] = useState('')
  const [messages, setMessages] = useState<Message[]>([])

  const repositories = useQuery({
    queryKey: ['repositories'],
    queryFn: fetchRepositories,
  })

  useEffect(() => {
    if (!projectId && repositories.data?.[0]) {
      setProjectId(repositories.data[0].project_id)
    }
  }, [projectId, repositories.data])

  const agents = useMutation({
    mutationFn: ({
      id,
      request,
    }: {
      id: string
      request: string
    }) => executeAgents(id, request),

    onSuccess: (result: AgentExecutionResponse, variables) => {
      const completedOutputs = result.outputs.filter(
        (output) => output.status === 'completed',
      )

      const failedOutputs = result.outputs.filter(
        (output) => output.status === 'failed',
      )

      const assistantContent = completedOutputs.length
        ? completedOutputs
            .map(
              (output) =>
                `## ${formatAgentName(output.agent)}\n\n${output.content}`,
            )
            .join('\n\n---\n\n')
        : failedOutputs.length
          ? failedOutputs
              .map(
                (output) =>
                  `## ${formatAgentName(output.agent)}\n\nUnable to complete this analysis: ${
                    output.error ?? 'Unknown error'
                  }`,
              )
              .join('\n\n---\n\n')
          : 'No agent was able to produce an answer.'

      setMessages((current) => [
        ...current,
        {
          role: 'user',
          content: variables.request,
        },
        {
          role: 'assistant',
          content: assistantContent,
          agents: result.selected_agents,
          executionLog: result.execution_log,
        },
      ])

      setMessage('')
    },
  })

  const submit = () => {
    if (!projectId || !message.trim() || agents.isPending) {
      return
    }

    agents.mutate({
      id: projectId,
      request: message.trim(),
    })
  }

  const generateDefaultGuide = () => {
    if (!projectId || agents.isPending) {
      return
    }

    setMessage(defaultQuestion)

    agents.mutate({
      id: projectId,
      request: defaultQuestion,
    })
  }

  return (
    <div className="flex min-h-[560px] flex-col rounded-lg border border-[#30363d] bg-[#161b22]">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 border-b border-[#30363d] px-5 py-4">
        <Sparkles className="size-4 text-violet-400" />

        <span className="font-medium">
          CodePilot Assistant
        </span>

        <select
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
          className="ml-auto rounded-md border border-[#30363d] bg-[#0d1117] px-2 py-1.5 text-xs outline-none focus:border-blue-500"
        >
          <option value="">Select repository</option>

          {repositories.data?.map((repository) => (
            <option
              key={repository.project_id}
              value={repository.project_id}
            >
              {repository.name}
            </option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-5 overflow-auto p-5">
        {messages.length === 0 && (
          <div className="grid min-h-72 place-items-center text-center">
            <div>
              <BookOpen className="mx-auto size-8 text-violet-400" />

              <h3 className="mt-3 font-medium">
                Ask about your repository
              </h3>

              <p className="mt-1 max-w-md text-sm text-slate-400">
                Ask questions about the repository&apos;s
                architecture, files, functions, code, security,
                testing, or documentation.
              </p>

              <Button
                className="mt-4"
                variant="outline"
                disabled={!projectId || agents.isPending}
                onClick={generateDefaultGuide}
              >
                Generate onboarding guide
              </Button>
            </div>
          </div>
        )}

        {messages.map((item, index) => (
          <div
            key={index}
            className={
              item.role === 'user'
                ? 'ml-auto max-w-[80%] rounded-lg bg-blue-500 px-4 py-3 text-sm text-white'
                : 'max-w-[92%] rounded-lg border border-[#30363d] bg-[#0d1117] p-4 text-sm text-slate-200'
            }
          >
            <p className="whitespace-pre-wrap leading-6">
              {item.content}
            </p>

            {item.role === 'assistant' &&
              item.agents?.length ? (
              <div className="mt-4 border-t border-[#30363d] pt-3">
                <p className="text-xs font-medium text-slate-400">
                  Agents used
                </p>

                <div className="mt-2 flex flex-wrap gap-2">
                  {item.agents.map((agent) => (
                    <span
                      key={agent}
                      className="rounded-full border border-[#30363d] bg-[#161b22] px-2 py-1 text-xs text-slate-400"
                    >
                      {formatAgentName(agent)}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {item.role === 'assistant' &&
              item.executionLog?.length ? (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs text-slate-500">
                  View execution log
                </summary>

                <div className="mt-2 space-y-1 text-xs text-slate-500">
                  {item.executionLog.map((log, logIndex) => (
                    <p key={logIndex}>{log}</p>
                  ))}
                </div>
              </details>
            ) : null}
          </div>
        ))}

        {agents.isPending && (
          <div className="max-w-[70%] rounded-lg border border-[#30363d] bg-[#0d1117] p-4 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 animate-pulse text-violet-400" />

              <span>
                CodePilot is analyzing the repository...
              </span>
            </div>
          </div>
        )}

        {agents.isError && (
          <div className="rounded-md border border-red-900/70 bg-red-950/30 p-3 text-sm text-red-200">
            Could not generate the repository analysis.
            Check the backend terminal for the exact error.
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={(event) => {
          event.preventDefault()
          submit()
        }}
        className="flex gap-3 border-t border-[#30363d] p-4"
      >
        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask anything about this repository..."
          className="h-10 flex-1 rounded-md border border-[#30363d] bg-[#0d1117] px-3 text-sm outline-none placeholder:text-slate-500 focus:border-blue-500"
          disabled={agents.isPending}
        />

        <Button
          type="submit"
          disabled={
            !projectId ||
            !message.trim() ||
            agents.isPending
          }
          aria-label="Ask CodePilot"
        >
          <Send className="size-4" />
        </Button>
      </form>
    </div>
  )
}

function formatAgentName(agent: string): string {
  return agent
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}
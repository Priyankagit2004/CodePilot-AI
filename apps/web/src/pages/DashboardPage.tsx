import { useQuery } from '@tanstack/react-query'
import { Activity, ArrowUpRight, Database, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingSkeletons } from '../components/states/StatusStates'
import { Card } from '../components/ui/Card'
import { useHealth } from '../hooks/useHealth'
import { fetchRepositories } from '../lib/api'

export function DashboardPage() {
  const health = useHealth()
  const repositories = useQuery({ queryKey: ['repositories'], queryFn: fetchRepositories })
  if (health.isLoading || repositories.isLoading) return <LoadingSkeletons />
  if (health.isError || repositories.isError) return <ErrorState message="Could not load workspace data from the API." retry={() => { health.refetch(); repositories.refetch() }} />
  const latest = repositories.data?.[0]
  return <><div className="mb-8 flex items-start justify-between"><div><p className="text-sm text-blue-400">WORKSPACE</p><h1 className="mt-1 text-2xl font-semibold">Engineering overview</h1><p className="mt-2 text-sm text-slate-400">Your uploaded repositories and available intelligence.</p></div><Link to="/repositories/upload" className="inline-flex items-center gap-2 rounded-md bg-blue-500 px-3.5 py-2 text-sm font-medium text-white hover:bg-blue-400"><Upload className="size-4" />Upload repository</Link></div><div className="mb-6 flex items-center gap-2 text-sm text-emerald-400"><Activity className="size-4" />API status: {health.data?.status}</div><div className="grid gap-4 md:grid-cols-2"><Card className="p-5"><Database className="size-5 text-violet-400" /><p className="mt-4 text-sm text-slate-400">Repositories</p><p className="mt-2 text-3xl font-semibold">{repositories.data?.length ?? 0}</p><p className="mt-2 text-xs text-slate-500">Stored repositories ready for intelligence and retrieval.</p></Card><Card className="p-5"><p className="text-sm text-slate-400">Latest repository</p>{latest ? <><p className="mt-2 text-lg font-semibold">{latest.name}</p><p className="mt-1 text-sm text-slate-500">{latest.file_count} files · {latest.supported_languages.join(', ')}</p><Link to={`/repositories/${latest.project_id}/dashboard`} className="mt-4 inline-flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300">Open dashboard <ArrowUpRight className="size-4" /></Link></> : <><p className="mt-2 text-lg font-semibold">No repository uploaded</p><p className="mt-1 text-sm text-slate-500">Upload a ZIP archive to create a repository dashboard.</p></>}</Card></div><Card className="mt-6 p-5"><div className="flex items-center justify-between"><div><h2 className="font-medium">Next step</h2><p className="mt-1 text-sm text-slate-400">Use AI Chat to generate an onboarding guide from indexed repository context.</p></div><Link to="/chat" className="text-sm text-blue-400 hover:text-blue-300">Open AI Chat</Link></div></Card></>
}

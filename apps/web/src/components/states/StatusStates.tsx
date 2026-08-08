import { AlertCircle, Inbox } from 'lucide-react'
import { Button } from '../ui/Button'
import { Skeleton } from '../ui/Skeleton'
export function LoadingSkeletons() { return <div className="grid gap-4 md:grid-cols-3">{[1, 2, 3].map((item) => <Skeleton key={item} className="h-32" />)}</div> }
export function EmptyState({ title, description, action }: { title: string; description: string; action?: string }) { return <div className="flex min-h-64 flex-col items-center justify-center rounded-lg border border-dashed border-[#30363d] p-8 text-center"><Inbox className="mb-3 size-8 text-slate-500" /><h3 className="font-medium">{title}</h3><p className="mt-1 max-w-sm text-sm text-slate-400">{description}</p>{action && <Button className="mt-4">{action}</Button>}</div> }
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) { return <div className="flex items-center gap-3 rounded-lg border border-red-900/70 bg-red-950/30 p-4 text-sm text-red-200"><AlertCircle className="size-5 shrink-0" /><span>{message}</span>{retry && <Button variant="outline" size="sm" className="ml-auto" onClick={retry}>Retry</Button>}</div> }

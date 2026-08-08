import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <section className={cn('rounded-lg border border-[#30363d] bg-[#161b22]', className)} {...props} /> }

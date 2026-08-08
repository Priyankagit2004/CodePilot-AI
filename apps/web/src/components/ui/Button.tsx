import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'
const variants = cva('inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 disabled:pointer-events-none disabled:opacity-50', { variants: { variant: { default: 'bg-blue-500 text-white hover:bg-blue-400', secondary: 'bg-[#21262d] text-slate-100 hover:bg-[#30363d]', ghost: 'text-slate-300 hover:bg-[#21262d] hover:text-white', outline: 'border border-[#30363d] text-slate-200 hover:bg-[#21262d]' }, size: { default: 'h-9 px-3.5', sm: 'h-8 px-3 text-xs', lg: 'h-10 px-4' } }, defaultVariants: { variant: 'default', size: 'default' } })
export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof variants>
export function Button({ className, variant, size, ...props }: ButtonProps) { return <button className={cn(variants({ variant, size }), className)} {...props} /> }

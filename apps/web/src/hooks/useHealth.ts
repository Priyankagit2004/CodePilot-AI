import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../lib/api'
export function useHealth() { return useQuery({ queryKey: ['api-health'], queryFn: fetchHealth, staleTime: 30_000 }) }

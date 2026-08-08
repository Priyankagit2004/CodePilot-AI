import { RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts'
import { Card } from '../ui/Card'
import type { Score } from '../../lib/api'

export function ScoreCard({ score, accent }: { score: Score; accent: string }) { return <Card className="p-5"><div className="flex items-center justify-between"><div><p className="text-sm text-slate-400">{score.label}</p><p className="mt-2 text-2xl font-semibold">{score.score}<span className="text-sm text-slate-500">/100</span></p></div><div className="h-16 w-16"><ResponsiveContainer><RadialBarChart innerRadius="68%" outerRadius="100%" data={[{ value: score.score }]} startAngle={90} endAngle={-270}><RadialBar background dataKey="value" cornerRadius={6} fill={accent} /></RadialBarChart></ResponsiveContainer></div></div><p className="mt-3 text-xs leading-5 text-slate-500">{score.description}</p></Card> }

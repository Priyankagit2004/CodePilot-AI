import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { Card } from '../ui/Card'
import type { LanguageItem } from '../../lib/api'
const colors = ['#58a6ff', '#a371f7', '#3fb950', '#f85149', '#d29922', '#39c5cf']
export function LanguageChart({ data }: { data: LanguageItem[] }) { return <Card className="p-5"><h2 className="font-medium">Language distribution</h2><div className="mt-4 h-64">{data.length ? <ResponsiveContainer><PieChart><Pie data={data} dataKey="file_count" nameKey="language" innerRadius={55} outerRadius={85} paddingAngle={3}>{data.map((item, index) => <Cell key={item.language} fill={colors[index % colors.length]} />)}</Pie><Tooltip contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 6 }} /><Legend /></PieChart></ResponsiveContainer> : <p className="pt-20 text-center text-sm text-slate-500">No supported source languages found.</p>}</div></Card> }

import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
export function AppShell() { return <div className="flex min-h-screen bg-[#0d1117] text-slate-100"><Sidebar /><div className="min-w-0 flex-1"><Navbar /><main className="mx-auto max-w-7xl p-5 lg:p-8"><Outlet /></main></div></div> }

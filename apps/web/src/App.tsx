import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ChatPage } from './pages/ChatPage'
import { DashboardPage } from './pages/DashboardPage'
import { RepositoryOverviewPage } from './pages/RepositoryOverviewPage'
import { RepositoryDashboardPage } from './pages/RepositoryDashboardPage'
import { UploadPage } from './pages/UploadPage'

export default function App() {
  return <Routes><Route element={<AppShell />}><Route path="/dashboard" element={<DashboardPage />} /><Route path="/repositories/upload" element={<UploadPage />} /><Route path="/repositories" element={<RepositoryOverviewPage />} /><Route path="/repositories/:projectId/dashboard" element={<RepositoryDashboardPage />} /><Route path="/chat" element={<ChatPage />} /></Route><Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes>
}

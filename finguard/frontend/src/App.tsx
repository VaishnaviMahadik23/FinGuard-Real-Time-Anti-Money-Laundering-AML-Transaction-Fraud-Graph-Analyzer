import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import DashboardPage from '@/pages/DashboardPage'
import GraphPage from '@/pages/GraphPage'
import TransactionsPage from '@/pages/TransactionsPage'
import AIAnalystPage from '@/pages/AIAnalystPage'
import { useTransactionStream } from '@/hooks/useTransactionStream'

export default function App() {
  // Global WebSocket subscription — feeds Zustand store
  useTransactionStream()

  return (
    <Layout>
      <Routes>
        <Route path="/"             element={<DashboardPage />} />
        <Route path="/graph"        element={<GraphPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/ai"           element={<AIAnalystPage />} />
      </Routes>
    </Layout>
  )
}

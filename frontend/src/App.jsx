import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import NewReportPage from './pages/NewReportPage'
import ReportDetailPage from './pages/ReportDetailPage'
import MyReportsPage from './pages/MyReportsPage'
import AuthorityDashboard from './pages/AuthorityDashboard'
import AdminDashboard from './pages/AdminDashboard'
import PageTransition from './components/PageTransition'

function Layout({ children }) {
  const location = useLocation()
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      {/* key forces PageTransition to remount (re-animate) on route change */}
      <main>
        <PageTransition key={location.pathname}>
          {children}
        </PageTransition>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Protected — all logged-in users */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout><HomePage /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/report/new" element={
          <ProtectedRoute>
            <Layout><NewReportPage /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/reports/:id" element={
          <ProtectedRoute>
            <Layout><ReportDetailPage /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/my-reports" element={
          <ProtectedRoute>
            <Layout><MyReportsPage /></Layout>
          </ProtectedRoute>
        } />

        {/* Authority only */}
        <Route path="/authority" element={
          <ProtectedRoute roles={['authority', 'admin']}>
            <Layout><AuthorityDashboard /></Layout>
          </ProtectedRoute>
        } />

        {/* Admin only */}
        <Route path="/admin" element={
          <ProtectedRoute roles={['admin']}>
            <Layout><AdminDashboard /></Layout>
          </ProtectedRoute>
        } />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

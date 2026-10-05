import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Spinner } from './UI'

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return children
}

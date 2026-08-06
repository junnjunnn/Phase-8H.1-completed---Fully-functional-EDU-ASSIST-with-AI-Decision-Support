import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <LoadingSpinner label="Checking access..." />
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

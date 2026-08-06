import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RoleRoute({ allowedRoles }) {
  const { user } = useAuth()
  const role = user?.role || 'NONE'

  if (!allowedRoles.includes(role)) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}

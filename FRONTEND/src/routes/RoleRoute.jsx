import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AccessDeniedPage } from '../pages/errors/AccessDeniedPage'

export function RoleRoute({ allowedRoles }) {
  const { user } = useAuth()
  const role = (user?.role_name || user?.role || user?.profile?.role_name || 'NONE').toUpperCase()

  if (!allowedRoles.includes(role)) {
    return <AccessDeniedPage />
  }

  return <Outlet />
}

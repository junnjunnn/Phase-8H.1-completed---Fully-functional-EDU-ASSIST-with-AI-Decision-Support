import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { getTeacherContext } from '../../services/academicsService'
import { AdviserDashboard } from './AdviserDashboard'
import { Dashboard } from './Dashboard'
import { RegistrarDashboard } from './RegistrarDashboard'

export function DashboardResolver() {
  const { user } = useAuth()
  const [adviser, setAdviser] = useState(null)
  const role = (user?.role_name || user?.role || '').toUpperCase()

  useEffect(() => {
    let active = true

    if (role !== 'TEACHER') {
      return () => { active = false }
    }

    getTeacherContext()
      .then((context) => {
        if (active) setAdviser((context.advisory_classes || []).length > 0)
      })
      .catch(() => {
        if (active) setAdviser(false)
      })

    return () => { active = false }
  }, [role])

  if (role === 'REGISTRAR') return <RegistrarDashboard />
  if (role !== 'TEACHER') return <Dashboard />
  if (adviser === true) return <AdviserDashboard />
  if (adviser === false) return <Dashboard />
  return <div className="dashboard-page"><div className="dashboard-skeleton-grid">{Array.from({ length: 4 }).map((_, index) => <div key={index} className="skeleton-card" />)}</div></div>
}
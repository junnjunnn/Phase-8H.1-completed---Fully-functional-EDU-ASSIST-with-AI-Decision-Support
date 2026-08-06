import { useEffect, useMemo, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { SidebarNav } from './SidebarNav'
import { TopBar } from './TopBar'

const sectionMap = {
  dashboard: 'Dashboard',
  students: 'Students',
  academics: 'Academics',
  attendance: 'Attendance',
  behavior: 'Behavior',
  interventions: 'Interventions',
  predictions: 'Predictions',
  reports: 'Reports',
  users: 'User Management',
  admin: 'Administrator Tools',
  profile: 'My Profile',
}

export function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(() => typeof window !== 'undefined' ? window.localStorage.getItem('edu-sidebar-collapsed') === 'true' : false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('edu-sidebar-collapsed', String(collapsed))
    }
  }, [collapsed])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 1024px)')
    const handleChange = (event) => {
      setCollapsed(event.matches)
    }

    handleChange(mediaQuery)
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const pathParts = location.pathname.split('/').filter(Boolean)
  const sectionKey = pathParts[0] || 'dashboard'
  const pageTitle = useMemo(() => {
    if (sectionKey === 'students' && pathParts[1]) return 'Student details'
    if (sectionKey === 'profile') return 'My Profile'
    return sectionMap[sectionKey] || 'Dashboard'
  }, [pathParts, sectionKey])

  const handleOpenProfile = () => {
    setShowProfile(false)
    navigate('/profile')
  }

  const handleOpenNotifications = () => {
    setShowNotifications(true)
  }

  return (
    <div className={`app-shell ${collapsed ? 'app-shell--collapsed' : ''}`}>
      <SidebarNav collapsed={collapsed} onToggleCollapse={() => setCollapsed((value) => !value)} onOpenProfile={handleOpenProfile} onOpenNotifications={handleOpenNotifications} />
      <main className="content-area">
        <TopBar onToggleSidebar={() => setCollapsed((value) => !value)} pageTitle={pageTitle} onOpenProfile={handleOpenProfile} onOpenNotifications={handleOpenNotifications} />
        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}

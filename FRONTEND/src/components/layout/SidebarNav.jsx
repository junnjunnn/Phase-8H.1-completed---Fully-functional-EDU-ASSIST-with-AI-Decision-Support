import {
  BellIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  HomeIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'
import { NavLink, useLocation } from 'react-router-dom'
import { useMemo } from 'react'
import { useAuth } from '../../context/AuthContext'
import { navigationItems } from '../../config/navigation'

const sectionConfig = [
  { key: 'main', label: 'Main', items: ['Dashboard'] },
  { key: 'records', label: 'Academic Records', items: ['Students', 'Attendance', 'Behavior', 'Interventions'] },
  { key: 'ai', label: 'AI Decision Support', items: ['Predictions', 'Reports'] },
  { key: 'admin', label: 'Administration', items: ['User Management'] },
]

const iconMap = {
  Dashboard: HomeIcon,
  Students: UserGroupIcon,
  Attendance: CalendarDaysIcon,
  Behavior: ClipboardDocumentListIcon,
  Interventions: ShieldCheckIcon,
  Predictions: SparklesIcon,
  Reports: ChartBarIcon,
  'User Management': UserGroupIcon,
  Settings: Cog6ToothIcon,
}

function getRoleLabel(role) {
  switch (role) {
    case 'SUPER_ADMIN':
      return 'Administrator'
    case 'SCHOOL_ADMIN':
      return 'Administrator'
    case 'GUIDANCE':
      return 'Guidance'
    case 'TEACHER':
      return 'Teacher'
    default:
      return 'User'
  }
}

export function SidebarNav({ collapsed, onToggleCollapse, onOpenProfile, onOpenNotifications }) {
  const { user } = useAuth()
  const location = useLocation()

  const visibleItems = useMemo(() => navigationItems.filter((item) => {
    const role = user?.role || 'NONE'
    return item.roles.includes(role)
  }), [user?.role])

  const groupedItems = useMemo(() => {
    const groups = sectionConfig.map((section) => ({
      ...section,
      items: section.items
        .map((label) => {
          const item = visibleItems.find((entry) => entry.label === label)
          return item ? { ...item, isAction: false } : null
        })
        .filter(Boolean),
    }))

    return groups.filter((group) => group.items.length > 0)
  }, [visibleItems])

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`} aria-label="Application sidebar">
      <div className="sidebar-branding">
        <button type="button" className="sidebar-collapse-button" onClick={onToggleCollapse} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          {collapsed ? <ChevronRightIcon className="icon" /> : <ChevronLeftIcon className="icon" />}
        </button>
        <div className={`brand-card ${collapsed ? 'brand-card--collapsed' : ''}`}>
          <img src="/amigo-logo.png" alt="EDU ASSIST / Amigo School of Calinan logo" className="brand-logo" />
          {!collapsed ? (
            <div className="brand-info">
              <h2>EDU ASSIST</h2>
              <p>Amigo School of Calinan</p>
              <p className="brand-subtitle">Educational analytics for student success</p>
            </div>
          ) : null}
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Primary navigation">
        {groupedItems.map((group) => (
          <div key={group.key} className="nav-section">
            {!collapsed ? <p className="nav-section-title">{group.label}</p> : null}
            <ul>
              {group.items.map((item) => {
                const Icon = iconMap[item.label]
                return (
                  <li key={item.label}>
                    <NavLink to={item.path} className={({ isActive: active }) => (active ? 'nav-link active' : 'nav-link')} end={item.path === '/dashboard'}>
                      <span className="nav-link-icon" aria-hidden="true"><Icon className="icon" /></span>
                      {!collapsed ? <span>{item.label}</span> : null}
                    </NavLink>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

    </aside>
  )
}

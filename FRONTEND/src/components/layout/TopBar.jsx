import {
  ArrowLeftOnRectangleIcon,
  BellIcon,
  ChevronDownIcon,
  KeyIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

function SearchBox({ onOpenSearch }) {
  return (
    <div className="topbar-search">
      <MagnifyingGlassIcon className="icon icon--search" aria-hidden="true" />
      <input
        aria-label="Search the platform"
        placeholder="Search students, reports, records..."
        className="topbar-search-input"
        onFocus={onOpenSearch}
        onClick={onOpenSearch}
      />
    </div>
  )
}

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

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good Morning'
  if (hour < 18) return 'Good Afternoon'
  return 'Good Evening'
}

function getRoleLabel(role) {
  switch (role) {
    case 'SUPER_ADMIN':
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

export function TopBar({ pageTitle, onOpenProfile, onOpenNotifications, onOpenSearch }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const breadcrumbs = useMemo(() => {
    const pathParts = location.pathname.split('/').filter(Boolean)
    const items = [{ label: 'Home', path: '/dashboard' }]
    pathParts.forEach((part) => {
      if (part === 'dashboard') return
      const label = sectionMap[part] || part
      items.push({ label, path: `/${part}` })
    })
    return items
  }, [location.pathname])

  const initials = (user?.username || 'U').slice(0, 1).toUpperCase()
  const now = new Date()

  async function handleLogout() {
    setDropdownOpen(false)
    await logout()
    window.location.replace('/login')
  }
  const currentDate = new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(now)
  const currentTime = new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(now)

  return (
    <header className="topbar">
      <div className="topbar-main">
        <div className="topbar-copy">
          <h1>{pageTitle}</h1>
          <div className="breadcrumbs" aria-label="Breadcrumb">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.path} className="breadcrumb-item">
                {index > 0 ? <span className="breadcrumb-separator">/</span> : null}
                {index < breadcrumbs.length - 1 ? (
                  <button type="button" className="breadcrumb-link" onClick={() => navigate(crumb.path)}>{crumb.label}</button>
                ) : (
                  <span aria-current="page">{crumb.label}</span>
                )}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="topbar-actions">
        <SearchBox onOpenSearch={onOpenSearch} />
        <div className="topbar-clock" aria-label="Current date and time">
          <p>{currentDate}</p>
          <strong>{currentTime}</strong>
        </div>
        <button type="button" className="icon-button icon-button--notification" aria-label="Notifications" onClick={onOpenNotifications}>
          <BellIcon className="icon" />
          <span className="notification-badge">0</span>
        </button>
        <div className="profile-menu-wrapper">
          <button type="button" className="profile-chip" onClick={() => setDropdownOpen((value) => !value)} aria-expanded={dropdownOpen} aria-haspopup="menu">
            <span className="profile-avatar">{initials}</span>
            <span className="profile-meta">
              <strong>{user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username || 'User'}</strong>
              <small>{getRoleLabel(user?.role)}</small>
            </span>
            <ChevronDownIcon className="icon icon--small" />
          </button>

          {dropdownOpen ? (
            <div className="profile-dropdown" role="menu">
              <div className="profile-dropdown-header">
                <div className="profile-avatar profile-avatar--large">{initials}</div>
                <div>
                  <strong>{user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : user?.username || 'User'}</strong>
                  <p className="profile-dropdown-greeting">{getGreeting()}, {user?.first_name || user?.username || 'there'}</p>
                  <span className="badge badge--info">{getRoleLabel(user?.role)}</span>
                </div>
              </div>
              <button type="button" className="profile-dropdown-item" role="menuitem" onClick={() => { setDropdownOpen(false); onOpenProfile(); }}>
                <UserCircleIcon className="icon" /> My Profile
              </button>
              <button type="button" className="profile-dropdown-item" role="menuitem" onClick={() => { setDropdownOpen(false); navigate('/profile?section=security') }}>
                <KeyIcon className="icon" /> Change Password
              </button>
              <button type="button" className="profile-dropdown-item" role="menuitem" onClick={handleLogout}>
                <ArrowLeftOnRectangleIcon className="icon" /> Logout
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  )
}

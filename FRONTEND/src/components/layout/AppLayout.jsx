import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { navigationItems } from '../../config/navigation'

const iconMap = {
  Dashboard: '🏠',
  Students: '👥',
  Academics: '📚',
  Attendance: '📅',
  Behavior: '⚠️',
  Interventions: '🛟',
  Predictions: '📈',
  Reports: '📄',
  Administration: '🛡️',
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
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const visibleItems = navigationItems.filter((item) => {
    const role = user?.role || 'NONE'
    return item.roles.includes(role)
  })

  const primaryItems = visibleItems.filter((item) => item.path !== '/reports' && item.path !== '/admin')
  const secondaryItems = visibleItems.filter((item) => item.path === '/reports' || item.path === '/admin')

  const pathParts = location.pathname.split('/').filter(Boolean)
  const sectionKey = pathParts[0] || 'dashboard'
  const pageTitle = sectionKey === 'students' && pathParts[1] ? 'Student details' : sectionMap[sectionKey] || 'Dashboard'

  const breadcrumbs = [
    { label: 'Dashboard', path: '/dashboard' },
    ...(sectionKey !== 'dashboard' ? [{ label: sectionMap[sectionKey] || sectionKey, path: `/${sectionKey}` }] : []),
    ...(sectionKey === 'students' && pathParts[1] ? [{ label: 'Detail', path: location.pathname }] : []),
  ]

  const initials = (user?.username || 'U').slice(0, 1).toUpperCase()

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Application sidebar">
        <div className="sidebar-branding">
          <img src="/amigo-logo.jpg" alt="Amigo School of Calinan logo" className="brand-logo" />
          <div className="brand-info">
            <h2>EDU ASSIST</h2>
            <p>Amigo School of Calinan</p>
            <p className="brand-subtitle">Educational analytics for student success</p>
          </div>
        </div>

        <nav className="nav-section" aria-label="Primary navigation">
          <p className="nav-section-title">Main</p>
          <ul>
            {primaryItems.map((item) => (
              <li key={item.path}>
                <NavLink to={item.path} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
                  <span className="nav-link-icon" aria-hidden="true">
                    {iconMap[item.label] || '•'}
                  </span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {secondaryItems.length > 0 ? (
          <nav className="nav-section" aria-label="Secondary navigation">
            <p className="nav-section-title">Insights</p>
            <ul>
              {secondaryItems.map((item) => (
                <li key={item.path}>
                  <NavLink to={item.path} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
                    <span className="nav-link-icon" aria-hidden="true">
                      {iconMap[item.label] || '•'}
                    </span>
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        ) : null}

        <div className="sidebar-footer">
          <div>
            <strong>{user?.username || 'User'}</strong>
            <p>{user?.role || 'No role'}</p>
          </div>
          <button type="button" className="icon-button sidebar-logout" onClick={logout} aria-label="Logout">
            →
          </button>
        </div>
      </aside>

      <main className="content-area">
        <header className="topbar">
          <div className="topbar-meta">
            <div className="page-title">
              <p className="eyebrow">Current page</p>
              <h1>{pageTitle}</h1>
            </div>
            <div className="breadcrumbs" aria-label="Breadcrumb">
              {breadcrumbs.map((crumb, index) => (
                <span key={crumb.path} className="breadcrumb-item">
                  {index > 0 && <span className="breadcrumb-separator">/</span>}
                  {index < breadcrumbs.length - 1 ? (
                    <NavLink to={crumb.path} className="breadcrumb-link">
                      {crumb.label}
                    </NavLink>
                  ) : (
                    <span aria-current="page">{crumb.label}</span>
                  )}
                </span>
              ))}
            </div>
          </div>

          <div className="topbar-actions">
            <button type="button" className="icon-button" aria-label="Notifications">
              🔔
            </button>
            <div className="profile-chip" aria-label="Profile information">
              <span className="profile-avatar">{initials}</span>
              <span>
                <strong>{user?.username || 'Guest'}</strong>
                <small>{user?.role || 'User'}</small>
              </span>
            </div>
            <button className="secondary-button" type="button" onClick={logout}>
              Logout
            </button>
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}

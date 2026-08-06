import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { navigationItems } from '../../config/navigation'

export function AppLayout() {
  const { user, logout } = useAuth()

  const visibleItems = navigationItems.filter((item) => {
    const role = user?.role || 'NONE'
    return item.roles.includes(role)
  })

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <img src="/amigo-logo.jpg" alt="Amigo School of Calinan logo" className="brand-logo" />
          <div className="brand-text">
            <p className="eyebrow">Amigo School</p>
            <h2>EDU ASSIST</h2>
          </div>
        </div>

        <nav aria-label="Primary navigation">
          <ul>
            {visibleItems.map((item) => (
              <li key={item.path}>
                <NavLink to={item.path} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div>
            <strong>{user?.username || 'User'}</strong>
            <p>{user?.role || 'No role'}</p>
          </div>
          <button type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>

      <main className="content-area">
        <header className="topbar">
          <div className="topbar-brand">
            <img src="/amigo-logo.jpg" alt="Amigo School logo" className="topbar-logo" />
            <div>
              <p className="eyebrow">School management dashboard</p>
              <h1>EDU ASSIST</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <div className="topbar-user">
              <span>{user?.username || 'Guest'}</span>
              <span className="pill">{user?.role || 'NONE'}</span>
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

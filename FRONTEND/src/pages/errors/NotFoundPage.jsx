import { Link } from 'react-router-dom'

function InlineIcon({ children, className = 'state-icon' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  )
}

export function NotFoundPage() {
  return (
    <div className="state-page" role="status">
      <div className="state-card state-card--large">
        <div className="coming-soon-illustration" aria-hidden="true">
          <InlineIcon>
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
          </InlineIcon>
        </div>
        <p className="eyebrow">404</p>
        <h1>Page not found</h1>
        <p>The page you requested could not be found. Please check the address or return to the dashboard.</p>
        <div className="modal-actions">
          <Link className="btn btn-primary" to="/dashboard">
            Return home
          </Link>
        </div>
      </div>
    </div>
  )
}

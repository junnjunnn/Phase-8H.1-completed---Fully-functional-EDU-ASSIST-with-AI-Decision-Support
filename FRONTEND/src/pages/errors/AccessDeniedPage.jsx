import { Link } from 'react-router-dom'

function InlineIcon({ children, className = 'state-icon' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  )
}

export function AccessDeniedPage() {
  return (
    <div className="state-page" role="alert">
      <div className="state-card state-card--large">
        <div className="coming-soon-illustration" aria-hidden="true">
          <InlineIcon>
            <path d="M12 3l7 4v5c0 4.7-2.8 8.2-7 10-4.2-1.8-7-5.3-7-10V7l7-4Z" />
            <path d="M12 8v5" />
            <path d="M12 16h.01" />
          </InlineIcon>
        </div>
        <p className="eyebrow">403</p>
        <h1>Access denied</h1>
        <p>You do not have permission to access this page. Please contact an administrator or return to the dashboard.</p>
        <div className="modal-actions">
          <button className="btn btn-outline" type="button" onClick={() => window.history.back()}>
            Go back
          </button>
          <Link className="btn btn-primary" to="/dashboard">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}

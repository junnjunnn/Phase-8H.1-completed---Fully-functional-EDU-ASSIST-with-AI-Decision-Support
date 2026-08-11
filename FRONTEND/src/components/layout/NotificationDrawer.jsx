import { XMarkIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboardSummary } from '../../services/predictionService'

export function NotificationDrawer({ open, onClose }) {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function loadNotifications() {
      setError('')
      setLoading(true)
      try {
        const summary = await getDashboardSummary()
        if (!active) return
        const predictionAlerts = (summary.attention_students || []).map((item) => ({
          id: `alert-${item.id}`,
          type: item.risk_level || 'Risk Alert',
          message: `${item.enrollment__student__first_name || item.enrollment__student__last_name ? `${item.enrollment__student__first_name || ''} ${item.enrollment__student__last_name || ''}`.trim() : 'Student'} is at ${item.risk_level || 'risk'}`,
          meta: `${item.probability != null ? `${Math.round(item.probability * 100)}%` : 'Unknown'} • ${item.prediction_date || 'Unknown date'}`,
          link: '/predictions',
        }))

        const recentActivity = (summary.recent_prediction_activity || []).map((item) => ({
          id: `recent-${item.id}`,
          type: item.risk_level || 'Prediction',
          message: `${item.enrollment__student__first_name || ''} ${item.enrollment__student__last_name || ''}`.trim() + ` has a new ${item.risk_level || 'prediction'}`,
          meta: `${item.probability != null ? `${Math.round(item.probability * 100)}%` : 'Unknown'} • ${item.prediction_date || 'Unknown date'}`,
          link: '/predictions',
        }))

        setNotifications([...predictionAlerts, ...recentActivity].slice(0, 10))
      } catch {
        setError('Unable to load notifications at this time.')
      } finally {
        if (active) setLoading(false)
      }
    }

    if (open) {
      loadNotifications()
    }

    return () => {
      active = false
    }
  }, [open])

  const notificationCount = notifications.length

  return (
    <div className={`notification-drawer ${open ? 'notification-drawer--open' : ''}`} role="dialog" aria-modal="true" aria-label="Notifications panel">
      <div className="drawer-panel">
        <div className="drawer-header">
          <div>
            <p className="eyebrow">Notifications</p>
            <h2>Recent alerts</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close notifications">
            <XMarkIcon className="icon" />
          </button>
        </div>
        <div className="drawer-section">
          <p className="section-description">You have {notificationCount} active notification{notificationCount === 1 ? '' : 's'}.</p>
          {loading ? (
            <div className="search-suggestions">
              <p>Loading notifications…</p>
            </div>
          ) : error ? (
            <p className="error-text">{error}</p>
          ) : notifications.length === 0 ? (
            <div className="search-suggestions">
              <p>No notifications are available right now.</p>
            </div>
          ) : (
            <ul className="notification-list">
              {notifications.map((item) => (
                <li key={item.id}>
                  <Link to={item.link} className="notification-item" onClick={onClose}>
                    <strong>{item.type}</strong>
                    <span>{item.message}</span>
                    <small>{item.meta}</small>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

import { XMarkIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getNotifications, markNotificationRead } from '../../services/attendanceService'

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
        const notificationData = await getNotifications({ ordering: '-scheduled_for' })
        const calendarNotifications = (notificationData.results || notificationData || []).map((item) => ({
          id: item.id,
          type: item.title,
          message: item.message,
          meta: item.read_at ? 'Read' : 'Unread',
          link: item.calendar_entry ? '/attendance/calendar' : '/dashboard',
          read: Boolean(item.read_at),
        }))
        if (!active) return
        setNotifications(calendarNotifications.slice(0, 20))
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
    <div className={`notification-drawer no-print ${open ? 'notification-drawer--open' : ''}`} role="dialog" aria-modal="true" aria-label="Notifications panel">
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
                  <Link to={item.link} className={`notification-item ${item.read ? 'notification-item--read' : ''}`} onClick={async () => { if (!item.read) await markNotificationRead(item.id); onClose() }}>
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

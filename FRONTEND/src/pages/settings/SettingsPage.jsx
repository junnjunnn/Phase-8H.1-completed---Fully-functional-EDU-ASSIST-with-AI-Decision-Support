import { useEffect, useState } from 'react'
import { PageHeader } from '../../components/common/PageHeader'

const STORAGE_KEYS = {
  theme: 'edu_assist_theme',
  notifications: 'edu_assist_notifications',
}

const themeOptions = [
  { value: 'system', label: 'System default' },
  { value: 'light', label: 'Light mode' },
  { value: 'dark', label: 'Dark mode' },
]

export function SettingsPage() {
  const [theme, setTheme] = useState(() => window.localStorage.getItem(STORAGE_KEYS.theme) || 'system')
  const [notificationsEnabled, setNotificationsEnabled] = useState(() => {
    const storedNotifications = window.localStorage.getItem(STORAGE_KEYS.notifications)
    return storedNotifications !== null ? storedNotifications === 'true' : true
  })

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEYS.theme, theme)
    document.documentElement.dataset.theme = theme === 'system' ? '' : theme
  }, [theme])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEYS.notifications, String(notificationsEnabled))
  }, [notificationsEnabled])

  return (
    <div className="page-stack settings-page">
      <PageHeader
        eyebrow="Account"
        title="System settings"
        description="Adjust display preferences and notification behavior for your EDU ASSIST workspace."
      />

      <div className="settings-grid">
        <section className="panel-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Display</p>
              <h3>Theme preference</h3>
            </div>
          </div>
          <div className="form-grid">
            {themeOptions.map((option) => (
              <label key={option.value} className="radio-option">
                <input
                  type="radio"
                  name="theme"
                  value={option.value}
                  checked={theme === option.value}
                  onChange={() => setTheme(option.value)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="panel-card">
          <div className="section-header">
            <div>
              <p className="eyebrow">Notifications</p>
              <h3>Alert preferences</h3>
            </div>
          </div>
          <div className="form-grid">
            <label className="checkbox-option">
              <input
                type="checkbox"
                checked={notificationsEnabled}
                onChange={(event) => setNotificationsEnabled(event.target.checked)}
              />
              <span>Enable in-app notifications</span>
            </label>
            <p className="section-description">These preferences are saved in your browser and help personalize your EDU ASSIST experience.</p>
          </div>
        </section>
      </div>
    </div>
  )
}

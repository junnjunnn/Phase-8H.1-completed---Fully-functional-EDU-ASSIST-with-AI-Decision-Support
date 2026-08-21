import { BellIcon, KeyIcon, PaintBrushIcon, UserCircleIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { PageHeader } from '../../components/common/PageHeader'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { getApiErrorMessage } from '../../services/api'
import { getCurrentUserProfile, updateCurrentUserProfile } from '../../services/profileService'

const STORAGE_KEYS = {
  theme: 'edu_assist_theme',
  notifications: 'edu_assist_notifications',
}

const themeOptions = [
  { value: 'system', label: 'System default' },
  { value: 'light', label: 'Light mode' },
  { value: 'dark', label: 'Dark mode' },
]

const settingsSections = [
  { key: 'account', label: 'Account', description: 'Account information.', icon: UserCircleIcon },
  { key: 'security', label: 'Security', description: 'Password and access.', icon: KeyIcon },
  { key: 'notifications', label: 'Notifications', description: 'In-app alert preferences.', icon: BellIcon },
  { key: 'appearance', label: 'Appearance', description: 'Theme and display preferences.', icon: PaintBrushIcon },
]

export function SettingsPage() {
  const [activeSection, setActiveSection] = useState('account')
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', username: '', employee_id: '', department: '', phone_number: '' })
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [profileNotice, setProfileNotice] = useState('')
  const [theme, setTheme] = useState(() => window.localStorage.getItem(STORAGE_KEYS.theme) || 'system')
  const [notificationsEnabled, setNotificationsEnabled] = useState(() => {
    const storedNotifications = window.localStorage.getItem(STORAGE_KEYS.notifications)
    return storedNotifications !== null ? storedNotifications === 'true' : true
  })

  useEffect(() => {
    let active = true
    getCurrentUserProfile().then((data) => {
      if (!active) return
      setForm({
        first_name: data.first_name || '', last_name: data.last_name || '', email: data.email || '',
        username: data.username || '', employee_id: data.employee_id || '', department: data.department || '', phone_number: data.phone_number || '',
      })
    }).catch((err) => {
      if (active) setProfileError(getApiErrorMessage(err))
    }).finally(() => {
      if (active) setLoadingProfile(false)
    })
    return () => { active = false }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEYS.theme, theme)
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.dataset.theme = theme === 'dark' || (theme === 'system' && prefersDark) ? 'dark' : 'light'
  }, [theme])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEYS.notifications, String(notificationsEnabled))
  }, [notificationsEnabled])

  async function handleProfileSave(event) {
    event.preventDefault()
    setSavingProfile(true)
    setProfileError('')
    setProfileNotice('')
    try {
      await updateCurrentUserProfile(Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value.trim()])))
      setProfileNotice('Account settings saved successfully.')
    } catch (err) {
      setProfileError(getApiErrorMessage(err))
    } finally {
      setSavingProfile(false)
    }
  }

  return (
    <div className="page-stack settings-page">
      <PageHeader
        eyebrow="Account"
        title="System settings"
        description="Adjust display preferences and notification behavior for your EDU ASSIST workspace."
      />

      <div className="settings-layout">
        <nav className="panel-card settings-navigation" aria-label="Settings sections">
          <p className="eyebrow">Settings</p>
          <div className="settings-navigation-list">
            {settingsSections.map(({ key, label, description, icon: Icon }) => (
              <button
                key={key}
                type="button"
                className={`settings-navigation-item ${activeSection === key ? 'settings-navigation-item--active' : ''}`}
                onClick={() => setActiveSection(key)}
                aria-current={activeSection === key ? 'page' : undefined}
              >
                <Icon className="icon" aria-hidden="true" />
                <span><strong>{label}</strong><small>{description}</small></span>
              </button>
            ))}
          </div>
        </nav>

        <section className="settings-content" aria-live="polite">
          {profileError ? <ErrorBanner message={profileError} /> : null}
          {profileNotice ? <div className="success-banner" role="status">{profileNotice}</div> : null}
          {activeSection === 'account' ? (
            <section className="panel-card settings-account-card">
              <div className="section-header">
                <div><p className="eyebrow">Account</p><h3>Account settings</h3><p className="section-description">Manage the account information used across EDU ASSIST.</p></div>
              </div>
              {loadingProfile ? <div className="profile-skeleton" /> : <form className="settings-account-form" onSubmit={handleProfileSave}>
                <label><span>First name</span><input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} /></label>
                <label><span>Last name</span><input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} /></label>
                <label><span>Email address</span><input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
                <label><span>Phone number</span><input value={form.phone_number} onChange={(event) => setForm({ ...form, phone_number: event.target.value })} /></label>
                <label><span>Employee ID</span><input value={form.employee_id} onChange={(event) => setForm({ ...form, employee_id: event.target.value })} /></label>
                <label><span>Department</span><input value={form.department} onChange={(event) => setForm({ ...form, department: event.target.value })} /></label>
                <label><span>Username</span><input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label>
                <div className="settings-form-actions"><button className="action-button action-button--primary" type="submit" disabled={savingProfile}>{savingProfile ? 'Saving...' : 'Save changes'}</button></div>
              </form>}
            </section>
          ) : activeSection === 'security' ? (
            <section className="panel-card settings-secondary-card">
              <p className="eyebrow">Security</p><h3>Change password</h3><p className="section-description">Update your password securely from the Profile page.</p>
              <button type="button" className="action-button action-button--outline" onClick={() => window.location.assign('/profile?section=security')}>Change password</button>
            </section>
          ) : activeSection === 'appearance' ? (
            <section className="panel-card settings-panel-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Appearance</p>
                  <h3>Theme preference</h3>
                  <p className="section-description">Choose how EDU ASSIST appears on this device.</p>
                </div>
              </div>
              <div className="settings-choice-list">
                {themeOptions.map((option) => (
                  <label key={option.value} className={`settings-choice ${theme === option.value ? 'settings-choice--selected' : ''}`}>
                    <input
                      type="radio"
                      name="theme"
                      value={option.value}
                      checked={theme === option.value}
                      onChange={() => setTheme(option.value)}
                    />
                    <span><strong>{option.label}</strong><small>{option.value === 'system' ? 'Follow your device preference.' : `Use ${option.label.toLowerCase()} across the workspace.`}</small></span>
                  </label>
                ))}
              </div>
            </section>
          ) : (
            <section className="panel-card settings-panel-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Notifications</p>
                  <h3>Alert preferences</h3>
                  <p className="section-description">Control whether in-app notification indicators are enabled.</p>
                </div>
              </div>
              <label className="settings-toggle-row">
                <span><strong>Enable in-app notifications</strong><small>These preferences are saved in your browser.</small></span>
                <input
                  type="checkbox"
                  checked={notificationsEnabled}
                  onChange={(event) => setNotificationsEnabled(event.target.checked)}
                />
              </label>
            </section>
          )}
        </section>
      </div>
    </div>
  )
}

import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { changePassword, getCurrentUserProfile, updateCurrentUserProfile } from '../../services/profileService'

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

export function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const passwordSectionRef = useRef(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', username: '', employee_id: '', department: '', phone_number: '' })
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [busy, setBusy] = useState(false)
  const [passwordBusy, setPasswordBusy] = useState(false)

  const initials = useMemo(() => {
    const first = profile?.first_name?.trim() || profile?.username?.trim() || ''
    const last = profile?.last_name?.trim() || ''
    if (first && last) return `${first[0]}${last[0]}`.toUpperCase()
    return first.slice(0, 2).toUpperCase() || 'U'
  }, [profile])

  useEffect(() => {
    const section = new URLSearchParams(location.search).get('section')
    if (section === 'security' && passwordSectionRef.current) {
      passwordSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [location.search])

  useEffect(() => {
    let active = true

    async function loadProfile() {
      setLoading(true)
      setError('')
      try {
        const data = await getCurrentUserProfile()
        if (!active) return
        setProfile(data)
        setForm({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          email: data.email || '',
          username: data.username || '',
          employee_id: data.employee_id || '',
          department: data.department || '',
          phone_number: data.phone_number || '',
        })
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadProfile()

    return () => {
      active = false
    }
  }, [])

  async function handleSave(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')

    try {
      const payload = {
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        username: form.username.trim(),
        employee_id: form.employee_id.trim(),
        department: form.department.trim(),
        phone_number: form.phone_number.trim(),
      }
      const nextProfile = await updateCurrentUserProfile(payload)
      setProfile(nextProfile)
      await refreshUser()
      setNotice('Profile updated successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function handlePasswordChange(event) {
    event.preventDefault()
    setPasswordBusy(true)
    setError('')
    setNotice('')

    try {
      await changePassword(passwordForm)
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
      setNotice('Password updated successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setPasswordBusy(false)
    }
  }

  return (
    <div className="page-stack profile-page">
      <PageHeader
        eyebrow="Account"
        title="My profile"
        description="Review and update your account details securely."
        actions={
          <button className="btn btn-outline" type="button" onClick={() => navigate('/dashboard')}>
            Back to dashboard
          </button>
        }
      />

      {notice ? <div className="success-banner" role="status">{notice}</div> : null}
      {error ? <ErrorBanner message={error} /> : null}

      {loading ? (
        <div className="profile-skeleton" />
      ) : (
        <div className="profile-grid">
          <section className="panel-card profile-card" aria-label="Profile overview">
            <div className="profile-hero">
              <div className="profile-avatar profile-avatar--large">{initials}</div>
              <div>
                <p className="eyebrow">Account overview</p>
                <h2>{profile?.first_name && profile?.last_name ? `${profile.first_name} ${profile.last_name}` : profile?.username || 'User'}</h2>
                <p className="section-description">{profile?.email || 'No email provided'}</p>
              </div>
            </div>
            <div className="profile-details-grid">
              <div>
                <p className="stat-label">Username</p>
                <p className="stat-value">{profile?.username || '—'}</p>
              </div>
              <div>
                <p className="stat-label">Role</p>
                <p className="stat-value">{getRoleLabel(user?.role)}</p>
              </div>
              <div>
                <p className="stat-label">Account status</p>
                <p className="stat-value">{profile?.is_active ? 'Active' : 'Inactive'}</p>
              </div>
              <div>
                <p className="stat-label">Joined</p>
                <p className="stat-value">{profile?.date_joined ? new Date(profile.date_joined).toLocaleDateString() : '—'}</p>
              </div>
            </div>
          </section>

          <section className="panel-card" aria-label="Edit profile">
            <div className="section-header">
              <div>
                <p className="eyebrow">Profile details</p>
                <h3>Update your information</h3>
              </div>
            </div>
            <form className="profile-form" onSubmit={handleSave}>
              <div className="form-grid">
                <label>
                  <span>First name</span>
                  <input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} />
                </label>
                <label>
                  <span>Last name</span>
                  <input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} />
                </label>
              </div>
              <div className="form-grid">
                <label>
                  <span>Username</span>
                  <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
                </label>
                <label>
                  <span>Email</span>
                  <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
                </label>
              </div>
              <div className="form-grid">
                <label>
                  <span>Employee ID</span>
                  <input value={form.employee_id} onChange={(event) => setForm({ ...form, employee_id: event.target.value })} />
                </label>
                <label>
                  <span>Department</span>
                  <input value={form.department} onChange={(event) => setForm({ ...form, department: event.target.value })} />
                </label>
              </div>
              <label>
                <span>Phone number</span>
                <input value={form.phone_number} onChange={(event) => setForm({ ...form, phone_number: event.target.value })} />
              </label>
              <div className="modal-actions">
                <button className="btn btn-primary" type="submit" disabled={busy}>
                  {busy ? 'Saving…' : 'Save changes'}
                </button>
              </div>
            </form>
          </section>

          <section className="panel-card" aria-label="Change password" ref={passwordSectionRef}>
            <div className="section-header">
              <div>
                <p className="eyebrow">Security</p>
                <h3>Change password</h3>
              </div>
            </div>
            <form className="profile-form" onSubmit={handlePasswordChange}>
              <label>
                <span>Current password</span>
                <input type="password" value={passwordForm.current_password} onChange={(event) => setPasswordForm({ ...passwordForm, current_password: event.target.value })} />
              </label>
              <div className="form-grid">
                <label>
                  <span>New password</span>
                  <input type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} />
                </label>
                <label>
                  <span>Confirm password</span>
                  <input type="password" value={passwordForm.confirm_password} onChange={(event) => setPasswordForm({ ...passwordForm, confirm_password: event.target.value })} />
                </label>
              </div>
              <div className="modal-actions">
                <button className="btn btn-secondary" type="submit" disabled={passwordBusy}>
                  {passwordBusy ? 'Updating…' : 'Change password'}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  )
}

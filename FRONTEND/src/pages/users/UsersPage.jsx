import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

function InlineIcon({ children, className = 'icon' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {children}
    </svg>
  )
}
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { activateUser, createUser, deactivateUser, getUsers, resetUserPassword, updateUser } from '../../services/userService'

const roleOptions = [
  { value: 'SUPER_ADMIN', label: 'Administrator' },
  { value: 'SCHOOL_ADMIN', label: 'Administrator' },
  { value: 'REGISTRAR', label: 'Registrar' },
  { value: 'TEACHER', label: 'Teacher' },
  { value: 'GUIDANCE', label: 'Guidance' },
]

function getRoleBadgeClass(role) {
  const value = String(role || '').toUpperCase()
  if (value === 'SUPER_ADMIN' || value === 'SCHOOL_ADMIN') {
    return 'badge badge--info'
  }
  if (value === 'REGISTRAR') {
    return 'badge badge--primary'
  }
  if (value === 'TEACHER') {
    return 'badge badge--success'
  }
  return 'badge badge--warning'
}

function getStatusBadgeClass(isActive) {
  return isActive ? 'badge badge--success' : 'badge badge--warning'
}

function initialsFromUser(user) {
  const first = user?.first_name?.trim() || user?.username?.trim() || ''
  const last = user?.last_name?.trim() || ''
  if (first && last) {
    return `${first[0]}${last[0]}`.toUpperCase()
  }
  if (first) {
    return first.slice(0, 2).toUpperCase()
  }
  return 'U'
}

export function UsersPage() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [showReset, setShowReset] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    role_name: 'TEACHER',
    is_active: true,
  })
  const [validation, setValidation] = useState({})
  const [notice, setNotice] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadUsers = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getUsers()
      setUsers(Array.isArray(data) ? data : data?.results || [])
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Defer initial load to allow mount to settle and avoid potential synchronous state updates
    const t = setTimeout(() => {
      loadUsers()
    }, 0)
    return () => clearTimeout(t)
  }, [])

  const filteredUsers = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) {
      return users
    }
    return users.filter((entry) => {
      const fullName = `${entry.first_name || ''} ${entry.last_name || ''}`.trim().toLowerCase()
      return [entry.username, entry.email, fullName, entry.profile?.role_name, entry.is_active ? 'active' : 'inactive'].some((value) => value?.toString().toLowerCase().includes(term))
    })
  }, [users, search])

  const resetForm = () => {
    setForm({
      first_name: '',
      last_name: '',
      username: '',
      email: '',
      password: '',
      confirm_password: '',
      role_name: 'TEACHER',
      is_active: true,
    })
    setValidation({})
  }

  const openCreate = () => {
    resetForm()
    setSelectedUser(null)
    setShowCreate(true)
  }

  const openEdit = (user) => {
    setSelectedUser(user)
    setForm({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      username: user.username || '',
      email: user.email || '',
      password: '',
      confirm_password: '',
      role_name: user.role_name || user.profile?.role_name || 'TEACHER',
      is_active: Boolean(user.is_active),
    })
    setValidation({})
    setShowCreate(true)
  }

  const openReset = (user) => {
    setSelectedUser(user)
    setForm((prev) => ({ ...prev, password: '', confirm_password: '' }))
    setValidation({})
    setShowReset(true)
  }

  const closeModal = () => {
    setShowCreate(false)
    setShowReset(false)
    setSelectedUser(null)
    resetForm()
  }

  const validateCreate = () => {
    const nextValidation = {}
    if (!form.first_name.trim()) nextValidation.first_name = 'First name is required.'
    if (!form.last_name.trim()) nextValidation.last_name = 'Last name is required.'
    if (!form.username.trim()) nextValidation.username = 'Username is required.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) nextValidation.email = 'Enter a valid email address.'
    if (!form.password || form.password.length < 8) nextValidation.password = 'Password must be at least 8 characters long.'
    if (form.password !== form.confirm_password) nextValidation.confirm_password = 'Passwords do not match.'
    setValidation(nextValidation)
    return Object.keys(nextValidation).length === 0
  }

  const handleCreateOrUpdate = async (event) => {
    event.preventDefault()
    if (!selectedUser ? validateCreate() : true) {
      setIsSubmitting(true)
      try {
        const payload = {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          username: form.username.trim(),
          email: form.email.trim(),
          role_name: form.role_name,
          is_active: form.is_active,
        }

        if (!selectedUser) {
          payload.password = form.password
          await createUser(payload)
          setNotice('User created successfully.')
        } else {
          await updateUser(selectedUser.id, payload)
          setNotice('User updated successfully.')
        }

        closeModal()
        await loadUsers()
      } catch (error) {
        const apiMessage = getApiErrorMessage(error)
        const fieldErrors = error?.response?.data || {}
        const nextValidation = {}
        if (fieldErrors.username) nextValidation.username = apiMessage
        if (fieldErrors.email) nextValidation.email = apiMessage
        if (fieldErrors.password) nextValidation.password = apiMessage
        if (fieldErrors.confirm_password) nextValidation.confirm_password = apiMessage
        if (Object.keys(nextValidation).length === 0) {
          nextValidation.form = apiMessage
        }
        setValidation(nextValidation)
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const handlePasswordReset = async (event) => {
    event.preventDefault()
    const nextValidation = {}
    if (!form.password || form.password.length < 8) nextValidation.password = 'Password must be at least 8 characters long.'
    if (form.password !== form.confirm_password) nextValidation.confirm_password = 'Passwords do not match.'
    setValidation(nextValidation)
    if (Object.keys(nextValidation).length > 0) {
      return
    }

    setIsSubmitting(true)
    try {
      await resetUserPassword(selectedUser.id, { password: form.password, confirm_password: form.confirm_password })
      setNotice('Password reset successfully.')
      closeModal()
      await loadUsers()
    } catch (error) {
      const apiMessage = getApiErrorMessage(error)
      setValidation({ form: apiMessage })
    } finally {
      setIsSubmitting(false)
    }
  }

  const toggleActivation = async (user) => {
    if (user.id === currentUser?.id) {
      setError('You cannot deactivate your own account.')
      return
    }
    const shouldActivate = !user.is_active
    const confirmed = window.confirm(`Are you sure you want to ${shouldActivate ? 'activate' : 'deactivate'} this user?`)
    if (!confirmed) return
    setBusyId(user.id)
    try {
      if (shouldActivate) {
        await activateUser(user.id)
      } else {
        await deactivateUser(user.id)
      }
      await loadUsers()
      setNotice(`User ${shouldActivate ? 'activated' : 'deactivated'} successfully.`)
    } catch (error) {
      setError(getApiErrorMessage(error))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="page-stack users-page">
      <PageHeader
        eyebrow="Administration"
        title="User management"
        description="Create, update, and manage staff accounts across the school."
        actions={
          <button className="btn btn-primary" type="button" onClick={openCreate}>
            Create user
          </button>
        }
      />

      {notice ? <div className="success-banner" role="status">{notice}</div> : null}
      {error ? <ErrorBanner message={error} /> : null}

      <section className="panel-card users-panel" aria-label="User management panel">
        <div className="users-toolbar">
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true"><InlineIcon><circle cx="11" cy="11" r="6" /><path d="m20 20-4.2-4.2" /></InlineIcon></span>
            <input
              aria-label="Search users"
              placeholder="Search by name, username, role, or status"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="users-meta">
            <p>{filteredUsers.length} user{filteredUsers.length === 1 ? '' : 's'} found</p>
          </div>
        </div>

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 4 }).map((_, index) => <div key={index} className="table-skeleton-card" />)}
          </div>
        ) : null}

        {!loading && !error && filteredUsers.length === 0 ? (
          <EmptyState title="No users found" message="Create your first staff account or change your search filter." />
        ) : null}

        {!loading && !error && filteredUsers.length > 0 ? (
          <div className="table-card users-table-card">
            <table className="users-table">
              <thead>
                <tr>
                  <th scope="col">User</th>
                  <th scope="col">Username</th>
                  <th scope="col">Email</th>
                  <th scope="col">Role</th>
                  <th scope="col">Status</th>
                  <th scope="col">Date created</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((entry) => (
                  <tr key={entry.id}>
                    <td data-label="User">
                      <div className="user-row">
                        <div className="user-avatar" aria-hidden="true">{initialsFromUser(entry)}</div>
                        <div>
                          <p className="user-name">{`${entry.first_name || ''} ${entry.last_name || ''}`.trim() || entry.username}</p>
                          <p className="user-subtitle">{entry.email || 'No email provided'}</p>
                        </div>
                      </div>
                    </td>
                    <td data-label="Username">{entry.username}</td>
                    <td data-label="Email">{entry.email || '—'}</td>
                    <td data-label="Role"><span className={getRoleBadgeClass(entry.role_name || entry.profile?.role_name)}>{entry.role_name || entry.profile?.role_name || 'Teacher'}</span></td>
                    <td data-label="Status"><span className={getStatusBadgeClass(entry.is_active)}>{entry.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td data-label="Date created">{entry.date_joined ? new Date(entry.date_joined).toLocaleDateString() : '—'}</td>
                    <td data-label="Actions">
                      <div className="user-actions">
                        <button className="btn btn-outline" type="button" onClick={() => openEdit(entry)}>
                          Edit
                        </button>
                        <button className="btn btn-outline" type="button" onClick={() => openReset(entry)}>
                          Reset password
                        </button>
                        <button className="btn btn-secondary" type="button" disabled={busyId === entry.id} onClick={() => toggleActivation(entry)}>
                          {entry.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {(showCreate || showReset) && (
        <div className="modal-backdrop" role="presentation" onClick={closeModal}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="user-modal-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">{selectedUser ? 'Update user' : 'Create user'}</p>
                <h3 id="user-modal-title">{selectedUser ? 'Edit account' : 'Add a new staff account'}</h3>
              </div>
              <button className="icon-button" type="button" onClick={closeModal} aria-label="Close dialog">✕</button>
            </div>

            <form onSubmit={selectedUser ? handleCreateOrUpdate : handleCreateOrUpdate}>
              {!selectedUser ? (
                <>
                  <div className="form-grid">
                    <label>
                      <span>First name</span>
                      <input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} required />
                      {validation.first_name ? <p className="validation-message">{validation.first_name}</p> : null}
                    </label>
                    <label>
                      <span>Last name</span>
                      <input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} required />
                      {validation.last_name ? <p className="validation-message">{validation.last_name}</p> : null}
                    </label>
                  </div>

                  <div className="form-grid">
                    <label>
                      <span>Username</span>
                      <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required />
                      {validation.username ? <p className="validation-message">{validation.username}</p> : null}
                    </label>
                    <label>
                      <span>Email</span>
                      <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
                      {validation.email ? <p className="validation-message">{validation.email}</p> : null}
                    </label>
                  </div>

                  <div className="form-grid">
                    <label>
                      <span>Password</span>
                      <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
                      {validation.password ? <p className="validation-message">{validation.password}</p> : null}
                    </label>
                    <label>
                      <span>Confirm password</span>
                      <input type="password" value={form.confirm_password} onChange={(event) => setForm({ ...form, confirm_password: event.target.value })} required />
                      {validation.confirm_password ? <p className="validation-message">{validation.confirm_password}</p> : null}
                    </label>
                  </div>
                </>
              ) : (
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
              )}

              {selectedUser ? (
                <div className="form-grid">
                  <label>
                    <span>Username</span>
                    <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
                    {validation.username ? <p className="validation-message">{validation.username}</p> : null}
                  </label>
                  <label>
                    <span>Email</span>
                    <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
                    {validation.email ? <p className="validation-message">{validation.email}</p> : null}
                  </label>
                </div>
              ) : null}

              <div className="form-grid">
                <label>
                  <span>Role</span>
                  <select value={form.role_name} onChange={(event) => setForm({ ...form, role_name: event.target.value })}>
                    {roleOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Status</span>
                  <select value={form.is_active ? 'active' : 'inactive'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'active' })}>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </label>
              </div>

              {validation.form ? <p className="validation-message">{validation.form}</p> : null}

              <div className="modal-actions">
                <button className="btn btn-outline" type="button" onClick={closeModal}>Cancel</button>
                <button className="btn btn-primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving…' : selectedUser ? 'Save changes' : 'Create user'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showReset && selectedUser ? (
        <div className="modal-backdrop" role="presentation" onClick={closeModal}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="reset-password-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Security</p>
                <h3 id="reset-password-title">Reset password</h3>
              </div>
              <button className="icon-button" type="button" onClick={closeModal} aria-label="Close dialog">✕</button>
            </div>
            <form onSubmit={handlePasswordReset}>
              <div className="form-grid">
                <label>
                  <span>New password</span>
                  <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
                  {validation.password ? <p className="validation-message">{validation.password}</p> : null}
                </label>
                <label>
                  <span>Confirm password</span>
                  <input type="password" value={form.confirm_password} onChange={(event) => setForm({ ...form, confirm_password: event.target.value })} required />
                  {validation.confirm_password ? <p className="validation-message">{validation.confirm_password}</p> : null}
                </label>
              </div>
              {validation.form ? <p className="validation-message">{validation.form}</p> : null}
              <div className="modal-actions">
                <button className="btn btn-outline" type="button" onClick={closeModal}>Cancel</button>
                <button className="btn btn-primary" type="submit" disabled={isSubmitting}>Reset password</button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  )
}

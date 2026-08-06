import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'

export function Login() {
  const { isAuthenticated, loading, login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  if (loading) {
    return null
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      await login(username, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to sign in. Please review your credentials.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-branding">
          <img src="/amigo-logo.jpg" alt="Amigo School of Calinan logo" className="auth-logo" />
          <div>
            <p className="eyebrow">Amigo School of Calinan</p>
            <h2>EDU ASSIST</h2>
          </div>
          <p>Sign in to access the school performance dashboard.</p>
        </div>

        {error ? <ErrorBanner message={error} /> : null}

        <label htmlFor="username">Username</label>
        <input
          id="username"
          name="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        <button type="submit" disabled={submitting}>
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}

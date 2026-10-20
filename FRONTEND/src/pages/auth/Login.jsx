import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PasswordInput } from '../../components/common/PasswordInput'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'

export function Login() {
  const { isAuthenticated, loading, login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  if (loading && !submitting) {
    return <div className="auth-page"><LoadingSpinner label="Checking your session..." /></div>
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
    } catch (error) {
      const isCurrentUserFailure = error?.authStage === 'current-user'
      const requestError = isCurrentUserFailure ? error.originalError : error
      const status = requestError?.response?.status

      if (isCurrentUserFailure) {
        if (requestError?.isAxiosError && !requestError.response) {
          setError("We couldn't reach EDU ASSIST to load your account. Check your connection and try again.")
        } else if (status >= 500) {
          setError("EDU ASSIST couldn't load your account right now. Please try again shortly.")
        } else {
          setError("We couldn't load your account details after sign-in. Please try again.")
        }
      } else if (status === 401) {
        setError('The username or password is incorrect.')
      } else if (requestError?.isAxiosError && !requestError.response) {
        setError("Couldn't connect to EDU ASSIST. Check your connection and try again.")
      } else if (status >= 500) {
        setError('EDU ASSIST is temporarily unavailable. Please try again shortly.')
      } else {
        setError("We couldn't complete sign-in. Please try again.")
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit} aria-busy={submitting}>
        <div className="auth-branding">
          <img src="/amigo-logo.png" alt="EDU ASSIST / Amigo School of Calinan logo" className="auth-logo" />
          <div>
            <p className="eyebrow">Amigo School of Calinan</p>
            <h2>EDU ASSIST</h2>
          </div>
          <p>Sign in to access the EDU ASSIST dashboard.</p>
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
        <PasswordInput
          id="password"
          name="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}

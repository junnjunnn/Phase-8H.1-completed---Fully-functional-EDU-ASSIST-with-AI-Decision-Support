import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/feedback/ErrorBoundary'
import { AppRoutes } from './routes/AppRoutes'
import './App.css'
import './styles/professional-polish.css'

function getStoredTheme() {
  try {
    return window.localStorage.getItem('edu_assist_theme') || 'system'
  } catch {
    return 'system'
  }
}

function prefersDarkTheme() {
  try {
    return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches
  } catch {
    return false
  }
}

function applyStoredTheme() {
  const preference = getStoredTheme()
  document.documentElement.dataset.theme = preference === 'dark' || (preference === 'system' && prefersDarkTheme()) ? 'dark' : 'light'
}

function App() {
  useEffect(() => {
    applyStoredTheme()
    if (typeof window.matchMedia !== 'function') return undefined
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handlePreferenceChange = () => {
      if (getStoredTheme() === 'system') applyStoredTheme()
    }
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handlePreferenceChange)
      return () => mediaQuery.removeEventListener('change', handlePreferenceChange)
    }
    if (typeof mediaQuery.addListener === 'function') {
      mediaQuery.addListener(handlePreferenceChange)
      return () => mediaQuery.removeListener(handlePreferenceChange)
    }
    return undefined
  }, [])

  return (
    <AuthProvider>
      <BrowserRouter>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App

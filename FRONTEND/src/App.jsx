import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/feedback/ErrorBoundary'
import { AppRoutes } from './routes/AppRoutes'
import './App.css'

function applyStoredTheme() {
  const preference = window.localStorage.getItem('edu_assist_theme') || 'system'
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.dataset.theme = preference === 'dark' || (preference === 'system' && prefersDark) ? 'dark' : 'light'
}

function App() {
  useEffect(() => {
    applyStoredTheme()
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handlePreferenceChange = () => {
      if ((window.localStorage.getItem('edu_assist_theme') || 'system') === 'system') applyStoredTheme()
    }
    mediaQuery.addEventListener('change', handlePreferenceChange)
    return () => mediaQuery.removeEventListener('change', handlePreferenceChange)
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

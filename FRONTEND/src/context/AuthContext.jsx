import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getCurrentUser, login as loginRequest, logout as logoutRequest } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const refreshUser = useCallback(async () => {
    try {
      const profile = await getCurrentUser()
      setUser(profile)
      setIsAuthenticated(true)
      return profile
    } catch (error) {
      setUser(null)
      setIsAuthenticated(false)
      throw error
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    async function initializeAuth() {
      try {
        const profile = await refreshUser()
        if (isMounted) {
          setUser(profile)
          setIsAuthenticated(true)
        }
      } catch (error) {
        if (isMounted) {
          setUser(null)
          setIsAuthenticated(false)
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    initializeAuth()

    const handleLogout = () => {
      setUser(null)
      setIsAuthenticated(false)
      setLoading(false)
    }

    window.addEventListener('auth:logout', handleLogout)

    return () => {
      isMounted = false
      window.removeEventListener('auth:logout', handleLogout)
    }
  }, [refreshUser])

  const login = useCallback(async (username, password) => {
    setLoading(true)
    try {
      const result = await loginRequest(username, password)
      const profile = await refreshUser()
      setUser(profile)
      setIsAuthenticated(true)
      return result
    } finally {
      setLoading(false)
    }
  }, [refreshUser])

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      setUser(null)
      setIsAuthenticated(false)
      setLoading(false)
      window.dispatchEvent(new Event('auth:logout'))
    }
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
  }), [user, loading, isAuthenticated, login, logout, refreshUser])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }
  return context
}

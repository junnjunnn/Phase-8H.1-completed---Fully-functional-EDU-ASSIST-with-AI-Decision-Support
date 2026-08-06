import apiClient, { clearStoredTokens, setStoredTokens } from './api'

export async function login(username, password) {
  const response = await apiClient.post('/auth/login/', { username, password })
  const { access, refresh, user } = response.data || {}
  setStoredTokens(access, refresh)
  return { user, access, refresh }
}

export async function logout() {
  try {
    const refreshToken = window.localStorage.getItem('edu_assist_refresh_token')
    if (refreshToken) {
      await apiClient.post('/auth/logout/', { refresh: refreshToken })
    }
  } catch (error) {
    console.warn('Logout request failed.', error)
  } finally {
    clearStoredTokens()
  }
}

export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me/')
  return response.data
}

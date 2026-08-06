import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const TOKEN_STORAGE_KEYS = {
  access: 'edu_assist_access_token',
  refresh: 'edu_assist_refresh_token',
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let refreshPromise = null

function getStoredToken(key) {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem(key)
}

export function getStoredTokens() {
  return {
    access: getStoredToken(TOKEN_STORAGE_KEYS.access),
    refresh: getStoredToken(TOKEN_STORAGE_KEYS.refresh),
  }
}

export function setStoredTokens(accessToken, refreshToken) {
  if (typeof window === 'undefined') {
    return
  }
  if (accessToken) {
    window.localStorage.setItem(TOKEN_STORAGE_KEYS.access, accessToken)
  } else {
    window.localStorage.removeItem(TOKEN_STORAGE_KEYS.access)
  }

  if (refreshToken) {
    window.localStorage.setItem(TOKEN_STORAGE_KEYS.refresh, refreshToken)
  } else {
    window.localStorage.removeItem(TOKEN_STORAGE_KEYS.refresh)
  }
}

export function clearStoredTokens() {
  setStoredTokens(null, null)
}

apiClient.interceptors.request.use((config) => {
  const accessToken = getStoredToken(TOKEN_STORAGE_KEYS.access)
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return refreshPromise.then(() => apiClient(originalRequest))
      }

      originalRequest._retry = true
      isRefreshing = true
      const refreshToken = getStoredToken(TOKEN_STORAGE_KEYS.refresh)

      if (!refreshToken) {
        clearStoredTokens()
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('auth:logout'))
        }
        return Promise.reject(error)
      }

      refreshPromise = apiClient
        .post('/auth/token/refresh/', { refresh: refreshToken })
        .then((response) => {
          const nextAccessToken = response.data?.access
          if (nextAccessToken) {
            setStoredTokens(nextAccessToken, refreshToken)
            return nextAccessToken
          }
          clearStoredTokens()
          throw new Error('Refresh token missing access token')
        })
        .catch(() => {
          clearStoredTokens()
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('auth:logout'))
          }
          throw error
        })
        .finally(() => {
          isRefreshing = false
          refreshPromise = null
        })

      return refreshPromise.then(() => apiClient(originalRequest))
    }

    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error) {
  const data = error?.response?.data

  if (typeof data === 'string') {
    return data
  }

  if (data && typeof data === 'object') {
    if (data.detail) {
      return data.detail
    }

    const firstMessage = Object.values(data).find((value) => Array.isArray(value) && value.length > 0)
    if (firstMessage) {
      return firstMessage[0]
    }

    const fieldMessage = Object.values(data).find((value) => typeof value === 'string' && value.length > 0)
    if (fieldMessage) {
      return fieldMessage
    }
  }

  if (error?.message) {
    return error.message
  }

  return 'The server could not be reached. Please try again.'
}

export default apiClient

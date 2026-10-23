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
  const requestUrl = config.url || ''
  if (requestUrl.endsWith('/auth/login/') || requestUrl.endsWith('/auth/token/refresh/')) {
    return config
  }

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
    const requestUrl = originalRequest?.url || ''
    const isAuthenticationRequest = requestUrl.endsWith('/auth/login/') || requestUrl.endsWith('/auth/token/refresh/')

    if (status === 401 && originalRequest && !originalRequest._retry && !isAuthenticationRequest) {
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
            const nextRefreshToken = response.data?.refresh || refreshToken
            setStoredTokens(nextAccessToken, nextRefreshToken)
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

  function formatValidationError(value, fieldPath = []) {
    if (typeof value === 'string') {
      const message = value.trim()
      const label = fieldPath
        .map((field) => field.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()))
        .join(' > ')
      return message && label
        ? `${label}: ${message}`
        : message
    }

    if (Array.isArray(value)) {
      return value
        .map((item) => formatValidationError(item, fieldPath))
        .filter(Boolean)
        .join(' ')
    }

    if (!value || typeof value !== 'object') {
      return ''
    }

    return Object.entries(value)
      .map(([key, nestedValue]) => {
        if (key === 'detail' || key === 'error' || key === 'message') {
          return formatValidationError(nestedValue, fieldPath)
        }
        if (key === 'non_field_errors' || key === 'non_field_error') {
          return formatValidationError(nestedValue, fieldPath)
        }
        return formatValidationError(nestedValue, [...fieldPath, key])
      })
      .filter(Boolean)
      .join(' ')
  }

  if (data && typeof data === 'object') {
    if (data.detail) {
      return formatValidationError(data.detail)
    }

    if (data.error) {
      return formatValidationError(data.error)
    }

    const validationMessage = formatValidationError(data)
    if (validationMessage) {
      return validationMessage
    }
  }

  if (error?.message) {
    return error.message
  }

  return 'The server could not be reached. Please try again.'
}

export default apiClient

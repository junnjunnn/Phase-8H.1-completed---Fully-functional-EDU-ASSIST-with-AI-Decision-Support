import apiClient from './api'

export async function getCurrentUserProfile() {
  const response = await apiClient.get('/auth/me/')
  return response.data
}

export async function updateCurrentUserProfile(payload) {
  const response = await apiClient.patch('/auth/me/', payload)
  return response.data
}

export async function changePassword(payload) {
  const response = await apiClient.post('/auth/change-password/', payload)
  return response.data
}

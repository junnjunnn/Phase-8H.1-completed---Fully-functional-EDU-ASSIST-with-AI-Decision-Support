import apiClient from './api'

export async function searchAdvisers(q = '') {
  const resp = await apiClient.get('/auth/advisers/', { params: { q } })
  return resp.data
}

export async function getUserById(id) {
  const resp = await apiClient.get(`/auth/users/${id}/`)
  return resp.data
}


export async function getUsers() {
  const response = await apiClient.get('/auth/users/')
  const data = response.data
  if (Array.isArray(data)) {
    return data
  }
  return data?.results || []
}

export async function createUser(payload) {
  const response = await apiClient.post('/auth/users/', payload)
  return response.data
}

export async function updateUser(userId, payload) {
  const response = await apiClient.patch(`/auth/users/${userId}/`, payload)
  return response.data
}

export async function resetUserPassword(userId, payload) {
  const response = await apiClient.post(`/auth/users/${userId}/reset-password/`, payload)
  return response.data
}

export async function activateUser(userId) {
  const response = await apiClient.post(`/auth/users/${userId}/activate/`)
  return response.data
}

export async function deactivateUser(userId) {
  const response = await apiClient.post(`/auth/users/${userId}/deactivate/`)
  return response.data
}

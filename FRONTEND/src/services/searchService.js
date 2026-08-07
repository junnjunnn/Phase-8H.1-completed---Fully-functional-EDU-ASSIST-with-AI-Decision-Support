import apiClient from './api'

export async function searchStudents(query) {
  const response = await apiClient.get('/students/', { params: { search: query, ordering: 'last_name', page_size: 10 } })
  return Array.isArray(response.data) ? response.data : response.data.results || []
}

export async function searchPredictions(query) {
  const response = await apiClient.get('/risk-predictions/', { params: { search: query, ordering: '-prediction_date', page_size: 10 } })
  return Array.isArray(response.data) ? response.data : response.data.results || []
}

export async function searchUsers(query) {
  const response = await apiClient.get('/auth/users/')
  const users = Array.isArray(response.data) ? response.data : response.data.results || []
  const term = query.trim().toLowerCase()
  if (!term) {
    return users.slice(0, 10)
  }
  return users.filter((user) => {
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim().toLowerCase()
    return [user.username, user.email, fullName, user.profile?.role_name].some((value) => String(value || '').toLowerCase().includes(term))
  })
}

import apiClient from './api'

export async function getInterventions(params = {}) {
  const response = await apiClient.get('/interventions/', { params })
  return response.data
}

export async function createIntervention(payload) {
  const response = await apiClient.post('/interventions/', payload)
  return response.data
}

export async function updateIntervention(id, payload) {
  const response = await apiClient.patch(`/interventions/${id}/`, payload)
  return response.data
}

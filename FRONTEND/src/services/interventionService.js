import apiClient from './api'

export async function getInterventions(params = {}) {
  const response = await apiClient.get('/interventions/', { params })
  return response.data
}

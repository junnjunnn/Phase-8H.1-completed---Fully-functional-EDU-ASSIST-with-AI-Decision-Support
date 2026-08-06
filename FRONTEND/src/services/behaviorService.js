import apiClient from './api'

export async function getCoreValues(params = {}) {
  const response = await apiClient.get('/core-values/', { params })
  return response.data
}

export async function getBehaviorIndicators(params = {}) {
  const response = await apiClient.get('/behavior-indicators/', { params })
  return response.data
}

export async function getBehavioralRatings(params = {}) {
  const response = await apiClient.get('/behavioral-ratings/', { params })
  return response.data
}

export async function getBehavioralAssessments(params = {}) {
  const response = await apiClient.get('/behavioral-assessments/', { params })
  return response.data
}

export async function createBehavioralAssessment(payload) {
  const response = await apiClient.post('/behavioral-assessments/', payload)
  return response.data
}

export async function updateBehavioralAssessment(id, payload) {
  const response = await apiClient.patch(`/behavioral-assessments/${id}/`, payload)
  return response.data
}

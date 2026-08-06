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

import apiClient from './api'

export async function getRiskPredictions(params = {}) {
  const response = await apiClient.get('/risk-predictions/', { params })
  return response.data
}

export async function getPredictionFactors(params = {}) {
  const response = await apiClient.get('/prediction-factors/', { params })
  return response.data
}

export async function getDashboardSummary(params = {}) {
  const response = await apiClient.get('/dashboard-summary/', { params })
  return response.data
}

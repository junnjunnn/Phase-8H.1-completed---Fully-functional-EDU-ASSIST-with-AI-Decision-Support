import apiClient from './api'

export async function getReportCenter(params = {}) {
  const response = await apiClient.get('/reports/center/', { params })
  return response.data
}

export async function exportReport(params = {}) {
  const response = await apiClient.get('/reports/export/', { params })
  return response.data
}

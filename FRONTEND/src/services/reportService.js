import apiClient from './api'

export async function getReportCenter(params = {}) {
  const response = await apiClient.get('/reports/center/', { params })
  return response.data
}

export async function exportReport(params = {}) {
  return apiClient.get('/reports/export/', { params, responseType: 'blob' })
}

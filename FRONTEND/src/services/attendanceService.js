import apiClient from './api'

export async function getAttendanceRecords(params = {}) {
  const response = await apiClient.get('/attendance-records/', { params })
  return response.data
}

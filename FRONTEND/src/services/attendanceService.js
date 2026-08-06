import apiClient from './api'

export async function getAttendanceRecords(params = {}) {
  const response = await apiClient.get('/attendance-records/', { params })
  return response.data
}

export async function createAttendanceRecord(payload) {
  const response = await apiClient.post('/attendance-records/', payload)
  return response.data
}

export async function updateAttendanceRecord(id, payload) {
  const response = await apiClient.patch(`/attendance-records/${id}/`, payload)
  return response.data
}

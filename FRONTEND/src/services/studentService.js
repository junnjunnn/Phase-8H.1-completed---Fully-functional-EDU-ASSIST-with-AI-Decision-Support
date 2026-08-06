import apiClient from './api'

export async function getStudents(params = {}) {
  const response = await apiClient.get('/students/', { params })
  return response.data
}

export async function getStudentById(id) {
  const response = await apiClient.get(`/students/${id}/`)
  return response.data
}

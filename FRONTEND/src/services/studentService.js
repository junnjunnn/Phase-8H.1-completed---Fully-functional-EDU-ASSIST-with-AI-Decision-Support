import apiClient from './api'

export async function getStudents(params = {}) {
  const response = await apiClient.get('/students/', { params })
  return response.data
}

export async function getStudentById(id) {
  const response = await apiClient.get(`/students/${id}/`)
  return response.data
}

export async function createStudent(payload) {
  const response = await apiClient.post('/students/', payload)
  return response.data
}

export async function updateStudent(id, payload) {
  const response = await apiClient.patch(`/students/${id}/`, payload)
  return response.data
}

export async function createEnrollment(payload) {
  const response = await apiClient.post('/enrollments/', payload)
  return response.data
}

export async function getAcademicYears(params = {}) {
  const response = await apiClient.get('/academic-years/', { params })
  return response.data
}

export async function getGradeLevels(params = {}) {
  const response = await apiClient.get('/grade-levels/', { params })
  return response.data
}

export async function getSections(params = {}) {
  const response = await apiClient.get('/sections/', { params })
  return response.data
}

import apiClient from './api'

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

export async function getStrands(params = {}) {
  const response = await apiClient.get('/strands/', { params })
  return response.data
}

export async function getSubjects(params = {}) {
  const response = await apiClient.get('/subjects/', { params })
  return response.data
}

export async function getEnrollments(params = {}) {
  const response = await apiClient.get('/enrollments/', { params })
  return response.data
}

export async function getAcademicRecords(params = {}) {
  const response = await apiClient.get('/academic-records/', { params })
  return response.data
}

export async function createAcademicRecord(payload) {
  const response = await apiClient.post('/academic-records/', payload)
  return response.data
}

export async function updateAcademicRecord(id, payload) {
  const response = await apiClient.patch(`/academic-records/${id}/`, payload)
  return response.data
}

export async function createAcademicYear(payload) {
  const response = await apiClient.post('/academic-years/', payload)
  return response.data
}

export async function updateAcademicYear(id, payload) {
  const response = await apiClient.patch(`/academic-years/${id}/`, payload)
  return response.data
}

export async function createGradeLevel(payload) {
  const response = await apiClient.post('/grade-levels/', payload)
  return response.data
}

export async function updateGradeLevel(id, payload) {
  const response = await apiClient.patch(`/grade-levels/${id}/`, payload)
  return response.data
}

export async function createSection(payload) {
  const response = await apiClient.post('/sections/', payload)
  return response.data
}

export async function updateSection(id, payload) {
  const response = await apiClient.patch(`/sections/${id}/`, payload)
  return response.data
}

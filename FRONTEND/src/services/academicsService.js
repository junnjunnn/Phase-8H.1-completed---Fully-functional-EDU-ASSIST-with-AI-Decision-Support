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

export async function getSpecializations(params = {}) {
  const response = await apiClient.get('/specializations/', { params })
  return response.data
}

export async function getSubjects(params = {}) {
  const status = params.status === 'true'
    ? 'active'
    : params.status === 'false'
      ? 'archived'
      : params.status
  const response = await apiClient.get('/subjects/', {
    params: status === params.status ? params : { ...params, status },
  })
  return response.data
}

export async function getAcademicDivisions() {
  const response = await apiClient.get('/subjects/academic-divisions/')
  return response.data
}

export async function getTeacherContext() {
  const response = await apiClient.get('/teacher-assignments/my-context/')
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

export async function bulkCreateAcademicRecords(payload) {
  const response = await apiClient.post('/academic-records/bulk/', payload)
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

export async function restoreGradeLevel(id) {
  const response = await apiClient.post(`/grade-levels/${id}/restore/`)
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

export async function createSubject(payload) {
  const response = await apiClient.post('/subjects/', payload)
  return response.data
}

export async function updateSubject(id, payload) {
  const response = await apiClient.patch(`/subjects/${id}/`, payload)
  return response.data
}

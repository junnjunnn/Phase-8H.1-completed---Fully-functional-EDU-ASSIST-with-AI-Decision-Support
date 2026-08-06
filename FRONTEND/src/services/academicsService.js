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

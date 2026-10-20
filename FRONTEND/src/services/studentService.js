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

export async function downloadStudentImportTemplate() {
  const response = await apiClient.get('/students/import/template/', { responseType: 'blob' })
  const url = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = 'edu-assist-student-import-template.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export async function previewStudentImport(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post('/students/import/preview/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function confirmStudentImport(file, importToken) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('import_token', importToken)
  const response = await apiClient.post('/students/import/confirm/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
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

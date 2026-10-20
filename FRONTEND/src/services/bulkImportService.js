import apiClient from './api'

export async function downloadBulkImportTemplate(url, filename) {
  const response = await apiClient.get(url, { responseType: 'blob' })
  const objectUrl = window.URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(objectUrl)
}

export async function previewBulkImport(url, file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function confirmBulkImport(url, file, importToken) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('import_token', importToken)
  const response = await apiClient.post(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

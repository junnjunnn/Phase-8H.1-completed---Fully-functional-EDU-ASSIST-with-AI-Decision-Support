import apiClient from './api'

export async function getAttendanceRecords(params = {}) {
  const response = await apiClient.get('/attendance-records/', { params })
  return response.data
}

export async function getSchoolDaySummary(params = {}) {
  const response = await apiClient.get('/attendance-records/school-day-summary/', { params })
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

export async function bulkSaveAttendanceRecords(payload) {
  const response = await apiClient.post('/attendance-records/bulk/', payload)
  return response.data
}

export async function getSchoolCalendarDays(params = {}) {
  const response = await apiClient.get('/school-calendar-days/', { params })
  return response.data
}

export async function createSchoolCalendarDay(payload) {
  const response = await apiClient.post('/school-calendar-days/', payload)
  return response.data
}

export async function updateSchoolCalendarDay(id, payload) {
  const response = await apiClient.patch(`/school-calendar-days/${id}/`, payload)
  return response.data
}

export async function bulkEditSchoolCalendarDays(payload) {
  const response = await apiClient.post('/school-calendar-days/bulk-edit/', payload)
  return response.data
}

export async function checkSchoolCalendarConflicts(payload) {
  const response = await apiClient.post('/school-calendar-days/check-conflicts/', payload)
  return response.data
}

export async function submitSchoolCalendarDayForApproval(id) {
  const response = await apiClient.post(`/school-calendar-days/${id}/submit-for-approval/`)
  return response.data
}

export async function approveSchoolCalendarDay(id, approvalNotes = '') {
  const response = await apiClient.post(`/school-calendar-days/${id}/approve/`, { approval_notes: approvalNotes })
  return response.data
}

export async function rejectSchoolCalendarDay(id, rejectionReason) {
  const response = await apiClient.post(`/school-calendar-days/${id}/reject/`, { rejection_reason: rejectionReason })
  return response.data
}

export async function publishSchoolCalendarDay(id) {
  const response = await apiClient.post(`/school-calendar-days/${id}/publish/`)
  return response.data
}

export async function cancelSchoolCalendarDay(id, cancellationReason) {
  const response = await apiClient.post(`/school-calendar-days/${id}/cancel/`, { cancellation_reason: cancellationReason })
  return response.data
}

export async function importPhilippineHolidays(academicYearId) {
  const response = await apiClient.post('/school-calendar-days/import-philippine-holidays/', { academic_year: academicYearId })
  return response.data
}

export async function getRecurringSchoolCalendarEvents(params = {}) {
  const response = await apiClient.get('/recurring-school-calendar-events/', { params })
  return response.data
}

export async function createRecurringSchoolCalendarEvent(payload) {
  const response = await apiClient.post('/recurring-school-calendar-events/', payload)
  return response.data
}

export async function updateRecurringSchoolCalendarEvent(id, payload) {
  const response = await apiClient.patch(`/recurring-school-calendar-events/${id}/`, payload)
  return response.data
}

export async function generateRecurringSchoolCalendarEvent(id) {
  const response = await apiClient.post(`/recurring-school-calendar-events/${id}/generate/`)
  return response.data
}

export async function deactivateRecurringSchoolCalendarEvent(id) {
  const response = await apiClient.post(`/recurring-school-calendar-events/${id}/deactivate/`)
  return response.data
}

export async function getNotifications(params = {}) {
  const response = await apiClient.get('/notifications/', { params })
  return response.data
}

export async function getUnreadNotificationCount() {
  const response = await apiClient.get('/notifications/unread_count/')
  return response.data
}

export async function markNotificationRead(id) {
  const response = await apiClient.post(`/notifications/${id}/mark_read/`)
  return response.data
}

import apiClient from './api'

export async function getStudentRelatedAcademicRecords(studentId, params = {}) {
  return apiClient.get('/academic-records/', { params: { 'enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentRelatedAttendanceRecords(studentId, params = {}) {
  return apiClient.get('/attendance-records/', { params: { 'enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentRelatedBehavioralAssessments(studentId, params = {}) {
  return apiClient.get('/behavioral-assessments/', { params: { 'enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentRelatedInterventions(studentId, params = {}) {
  return apiClient.get('/interventions/', { params: { 'enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentRelatedRiskPredictions(studentId, params = {}) {
  return apiClient.get('/risk-predictions/', { params: { 'enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentPredictionFactors(predictionId, params = {}) {
  return apiClient.get('/prediction-factors/', { params: { prediction: predictionId, ...params } }).then((res) => res.data)
}

export async function getStudentRelatedPredictionFactors(studentId, params = {}) {
  return apiClient.get('/prediction-factors/', { params: { 'prediction__enrollment__student': studentId, ...params } }).then((res) => res.data)
}

export async function getStudentEnrollments(studentId, params = {}) {
  return apiClient.get('/enrollments/', { params: { student: studentId, ...params } }).then((res) => res.data)
}

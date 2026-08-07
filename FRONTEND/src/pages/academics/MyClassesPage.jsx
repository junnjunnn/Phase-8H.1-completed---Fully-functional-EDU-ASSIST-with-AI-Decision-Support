import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import apiClient, { getApiErrorMessage } from '../../services/api'
import { getEnrollments } from '../../services/academicsService'
import { getReportCenter } from '../../services/reportService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function MyClassesPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadMyClasses() {
      setLoading(true)
      setError('')
      try {
        const response = await apiClient.get('/teacher-assignments/')
        const normalized = normalizeListResponse(response.data)
        const myAssignments = normalized.items.filter((assignment) => {
          const teacherId = assignment.teacher || assignment.teacher_id || null
          return teacherId === user?.id || String(teacherId) === String(user?.id)
        })

        const assignmentsWithReports = await Promise.all(myAssignments.map(async (assignment) => {
          let reportSummary = null
          try {
            reportSummary = await getReportCenter({
              academic_year: assignment.academic_year,
              grade_level: assignment.grade_level,
              section: assignment.section,
            })
          } catch (reportError) {
            reportSummary = null
          }

          return {
            ...assignment,
            reportSummary,
            studentCount: reportSummary?.student_reports?.student_count ?? 0,
          }
        }))

        setAssignments(assignmentsWithReports)
      } catch (err) {
        setError(getApiErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    if (user?.id) {
      loadMyClasses()
    }
  }, [user?.id])

  function handleViewClass(assignment) {
    navigate(`/academics/encode?academic_year=${assignment.academic_year}&grade_level=${assignment.grade_level}&section=${assignment.section}&subject=${assignment.subject}`)
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="My Classes" title="Assigned classes" description="View the sections you are assigned to teach." />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
      {!loading && assignments.length === 0 ? <EmptyState title="No classes assigned" message="You do not have any assigned classes yet." /> : null}
      {!loading && assignments.length > 0 ? (
        <div className="panel-card record-panel">
          <div className="record-summary-grid">
            {assignments.map((assignment) => (
              <article key={assignment.id} className="detail-card class-insight-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">Assigned class</p>
                    <h3>{assignment.grade_level_name || assignment.grade_level || 'Grade'} · {assignment.section_name || assignment.section || 'Section'}</h3>
                    <p>{assignment.academic_year_name || assignment.academic_year || 'Academic year unavailable'}</p>
                    <p>Subject: {assignment.subject_name || assignment.subject || 'Subject unavailable'}</p>
                  </div>
                  <span className={`badge ${assignment.is_active ? 'badge--success' : 'badge--status'}`}>
                    {assignment.is_active ? 'Open' : 'Inactive'}
                  </span>
                </div>
                <div className="class-metrics-grid">
                  <div>
                    <p className="stat-label">Enrolled students</p>
                    <p className="stat-value">{assignment.studentCount ?? 0}</p>
                  </div>
                  <div>
                    <p className="stat-label">Predictions</p>
                    <p className="stat-value">{assignment.reportSummary?.summary?.prediction_count ?? '—'}</p>
                  </div>
                  <div>
                    <p className="stat-label">At-risk students</p>
                    <p className="stat-value">{assignment.reportSummary?.summary ? `${assignment.reportSummary?.ai_reports?.summary?.high_risk_count ?? 0} high, ${assignment.reportSummary?.ai_reports?.summary?.moderate_risk_count ?? 0} mod` : '—'}</p>
                  </div>
                  <div>
                    <p className="stat-label">Attendance</p>
                    <p className="stat-value">{assignment.reportSummary?.summary?.attendance_percentage != null ? `${assignment.reportSummary.summary.attendance_percentage}%` : '—'}</p>
                  </div>
                </div>
                <div className="class-card-actions">
                  <button type="button" className="action-button action-button--secondary" onClick={() => handleViewClass(assignment)}>
                    View class
                  </button>
                  <button type="button" className="action-button action-button--outline" onClick={() => handleViewClass(assignment)}>
                    Open insights
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

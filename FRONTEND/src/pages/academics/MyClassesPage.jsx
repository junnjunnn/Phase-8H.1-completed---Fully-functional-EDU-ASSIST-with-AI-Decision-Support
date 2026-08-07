import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import apiClient, { getApiErrorMessage } from '../../services/api'
import { getEnrollments } from '../../services/academicsService'

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

        const assignmentsWithCounts = await Promise.all(myAssignments.map(async (assignment) => {
          const enrollmentResponse = await getEnrollments({
            academic_year: assignment.academic_year,
            grade_level: assignment.grade_level,
            section: assignment.section,
            enrollment_status: 'active',
          })
          const enrollmentItems = normalizeListResponse(enrollmentResponse).items
          return {
            ...assignment,
            studentCount: enrollmentItems.length,
          }
        }))

        setAssignments(assignmentsWithCounts)
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
              <article key={assignment.id} className="detail-card">
                <p className="eyebrow">Assigned class</p>
                <h3>{assignment.grade_level_name || assignment.grade_level || 'Grade'} · {assignment.section_name || assignment.section || 'Section'}</h3>
                <p>{assignment.academic_year_name || assignment.academic_year || 'Academic year unavailable'}</p>
                <p>Subject: {assignment.subject_name || assignment.subject || 'Subject unavailable'}</p>
                <p>{assignment.studentCount || 0} students</p>
                <p>Status: {assignment.is_active ? 'Open' : 'Inactive'}</p>
                <button type="button" className="action-button action-button--secondary" onClick={() => handleViewClass(assignment)} style={{ marginTop: '0.75rem' }}>
                  View Class
                </button>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

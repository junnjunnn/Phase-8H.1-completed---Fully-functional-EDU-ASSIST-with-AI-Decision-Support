import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getReportCenter } from '../../services/reportService'
import { getTeacherContext } from '../../services/academicsService'

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
        const context = await getTeacherContext()
        const advisoryClasses = context.advisory_classes || []
        const myAssignments = context.subject_assignments || []

        const assignmentsWithReports = await Promise.all(myAssignments.map(async (assignment) => {
          let reportSummary
          try {
            reportSummary = await getReportCenter({
              academic_year: assignment.academic_year,
              grade_level: assignment.grade_level,
              section: assignment.section,
            })
          } catch {
            reportSummary = null
          }

          return {
            ...assignment,
            reportSummary,
            studentCount: reportSummary?.student_reports?.student_count ?? 0,
          }
        }))

        setAssignments({ advisory: advisoryClasses, subject: assignmentsWithReports })
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
    <div className="page-stack my-classes-page">
      <PageHeader eyebrow="Teaching workspace" title="My classes" description="Your assigned classes appear immediately so you can move straight into attendance, grading, and follow-up actions." />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
      {!loading && !assignments.advisory?.length && !assignments.subject?.length ? <EmptyState title="No classes assigned" message="You do not have any assigned classes yet." /> : null}
      {!loading && (assignments.advisory?.length || assignments.subject?.length) ? (
        <div className="teacher-classes-stack">
          <section className="panel-card record-panel teacher-class-section" aria-labelledby="advisory-classes-title">
          <div className="section-header"><div><p className="eyebrow">Advisory responsibility</p><h2 id="advisory-classes-title">My advisory classes</h2></div></div>
          <div className="workflow-grid my-classes-grid">
            {(assignments.advisory || []).map((assignment) => (
              <article key={`adviser-${assignment.section}`} className="module-card class-landscape-card">
                <div className="class-card-details"><p className="eyebrow">Adviser</p><h3>{assignment.grade_level_name} · {assignment.section_name}</h3><p>Academic year: {assignment.academic_year_name}</p><p className="class-card-students"><span>Students</span><strong>{assignment.student_count}</strong></p></div>
                <div className="class-card-actions"><span className="badge badge--success">Advisory Class</span><div className="module-card-actions"><button type="button" className="action-button action-button--secondary" onClick={() => navigate(`/students?academic_year=${assignment.academic_year}&section=${assignment.section}`)}>View class</button></div></div>
              </article>
            ))}
          </div>
          </section>
          <section className="panel-card record-panel teacher-class-section" aria-labelledby="subject-assignments-title">
          <div className="section-header"><div><p className="eyebrow">Teaching responsibility</p><h2 id="subject-assignments-title">My subject assignments</h2></div></div>
          <div className="workflow-grid my-classes-grid">
            {(assignments.subject || []).map((assignment) => (
              <article key={assignment.id} className="module-card class-landscape-card">
                <div className="class-card-details">
                  <p className="eyebrow">{assignment.role || 'Subject Teacher'}</p>
                  <h3>{assignment.grade_level_name || assignment.grade_level || 'Grade'} · {assignment.section_name || assignment.section || 'Section'}</h3>
                  <p>{assignment.subject_name || assignment.subject || 'Subject unavailable'}</p>
                  <p>{assignment.academic_year_name || assignment.academic_year || 'Academic year unavailable'}</p>
                  <p className="class-card-students"><span>Students</span><strong>{assignment.studentCount ?? 0}</strong></p>
                </div>
                <div className="class-card-actions">
                  <span className={`badge ${assignment.is_active ? 'badge--success' : 'badge--status'}`}>
                    {assignment.is_active ? 'Open' : 'Inactive'}
                  </span>
                  <button type="button" className="action-button action-button--secondary" onClick={() => handleViewClass(assignment)}>Open class</button>
                  <button type="button" className="action-button action-button--outline" onClick={() => handleViewClass(assignment)}>Open insights</button>
                </div>
              </article>
            ))}
          </div>
          </section>
        </div>
      ) : null}
    </div>
  )
}

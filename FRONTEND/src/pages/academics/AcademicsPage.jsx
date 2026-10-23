import { useEffect, useMemo, useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import {
  getAcademicYears,
  getGradeLevels,
  getSubjects,
  getEnrollments,
  getAcademicRecords,
} from '../../services/academicsService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

export function AcademicsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [summary, setSummary] = useState({ years: 0, gradeLevels: 0, subjects: 0, enrollments: 0, records: 0 })
  const [academicRecords, setAcademicRecords] = useState([])
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [enrollments, setEnrollments] = useState([])

  useEffect(() => {
    let active = true

    async function loadAcademics() {
      setLoading(true)
      setError('')

      try {
        const [yearsData, levelsData, subjectsData, enrollmentsData, recordsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSubjects(),
          getEnrollments({ ordering: 'student__last_name,student__first_name' }),
          getAcademicRecords({ search, ordering: '-created_at' }),
        ])

        if (!active) {
          return
        }

        const years = normalizeListResponse(yearsData)
        const gradeLevels = normalizeListResponse(levelsData)
        const subjects = normalizeListResponse(subjectsData)
        const enrollmentList = normalizeListResponse(enrollmentsData)
        const records = normalizeListResponse(recordsData)

        setEnrollments(enrollmentList.items)
        setSummary({
          years: years.count,
          gradeLevels: gradeLevels.count,
          subjects: subjects.count,
          enrollments: enrollmentList.count,
          records: records.count,
        })
        setAcademicRecords(records.items.slice(0, 12))
        setPagination({
          count: records.count,
          next: records.next,
          previous: records.previous,
        })
      } catch (err) {
        if (!active) {
          return
        }
        setError(getApiErrorMessage(err))
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadAcademics()
    return () => {
      active = false
    }
  }, [search])

  const enrollmentLookup = useMemo(() => {
    return enrollments.reduce((lookup, enrollment) => {
      const studentName = [enrollment.student_name, enrollment.student?.full_name]
        .filter(Boolean)
        .find(Boolean) || 'Student'
      lookup[enrollment.id] = studentName
      return lookup
    }, {})
  }, [enrollments])

  const academicMetrics = useMemo(() => {
    const grades = academicRecords
      .map((record) => Number(record.final_grade ?? record.grade))
      .filter((value) => !Number.isNaN(value))

    const averageGrade = grades.length ? (grades.reduce((sum, value) => sum + value, 0) / grades.length).toFixed(2) : null
    const atRiskRecords = academicRecords.filter((record) => {
      const gradeValue = Number(record.final_grade ?? record.grade)
      return !Number.isNaN(gradeValue) && gradeValue < 75
    }).length
    const missingRemarks = academicRecords.filter((record) => !record.remarks || !String(record.remarks).trim()).length

    return {
      averageGrade,
      atRiskRecords,
      missingRemarks,
      subjectsNeedingReview: new Set(
        academicRecords
          .filter((record) => {
            const gradeValue = Number(record.final_grade ?? record.grade)
            return !Number.isNaN(gradeValue) && gradeValue < 75
          })
          .map((record) => record.subject_name || record.subject)
          .filter(Boolean),
      ).size,
    }
  }, [academicRecords])

  return (
    <div className="page-stack academics-page">
      <PageHeader
        eyebrow="Academics"
        title="Academic monitoring"
        description="Use this workspace to review academic outcomes, spot follow-ups, and move quickly from record review to grade entry."
      />

      <section className="detail-card workflow-guide-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Workflow guidance</p>
            <h3>Keep academic reviews action-ready</h3>
          </div>
        </div>
        <ul className="workflow-guide-list">
          <li>Review the latest evaluations before planning a teacher follow-up.</li>
          <li>Search by student or subject to isolate a specific performance concern.</li>
          <li>Open the grade encoding flow when a class needs the next action.</li>
        </ul>
        <div className="workflow-guide-actions">
          <span className="action-chip">Instructional review</span>
          <span className="action-chip">Progress tracking</span>
        </div>
      </section>

      <div className="record-summary-grid monitoring-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Average grade</p>
          <p className="stat-value">{academicMetrics.averageGrade ?? 'No data'}</p>
          <span className={`badge ${academicMetrics.averageGrade != null && Number(academicMetrics.averageGrade) < 75 ? 'badge--warning' : 'badge--success'}`}>
            {academicMetrics.averageGrade != null && Number(academicMetrics.averageGrade) < 75 ? 'Below target' : 'On track'}
          </span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic records</p>
          <p className="stat-value">{summary.records}</p>
          <span className="badge badge--info">Latest evaluations</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Subjects requiring attention</p>
          <p className="stat-value">{academicMetrics.subjectsNeedingReview}</p>
          <span className="badge badge--warning">{academicMetrics.atRiskRecords} at-risk records</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Missing remarks</p>
          <p className="stat-value">{academicMetrics.missingRemarks}</p>
          <span className={`badge ${academicMetrics.missingRemarks ? 'badge--warning' : 'badge--success'}`}>
            {academicMetrics.missingRemarks ? 'Needs review' : 'Complete'}
          </span>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic records</p>
            <h2>Latest academic evaluations</h2>
          </div>
          <div className="section-actions">
            <a className="action-button" href="/academics/encode">Encode grades</a>
            <div className="search-input-group">
              <MagnifyingGlassIcon className="icon search-icon" aria-hidden="true" />
              <input
                aria-label="Search academic records"
                placeholder="Search student name or subject"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="table-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && academicRecords.length === 0 ? (
          <EmptyState
            title={search ? 'No academic records match search' : 'No academic records available'}
            message={search ? 'Try a different keyword or clear the search filter.' : 'There are no academic records available in the backend.'}
          />
        ) : null}

        {!loading && !error && academicRecords.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{pagination.count} academic record{pagination.count === 1 ? '' : 's'} found.</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Student</th>
                    <th scope="col">Subject</th>
                    <th scope="col">Grade / section</th>
                    <th scope="col">Period</th>
                    <th scope="col">Grade</th>
                    <th scope="col">Status</th>
                    <th scope="col">Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {academicRecords.map((record) => {
                    const gradeValue = Number(record.final_grade ?? record.grade)
                    const isAcademicConcern = !Number.isNaN(gradeValue) && gradeValue < 75
                    const studentName = enrollmentLookup[record.enrollment] || 'Enrollment unavailable'
                    const enrollmentInfo = record.enrollment ? `Enrollment ${record.enrollment}` : 'No enrollment link'

                    return (
                      <tr key={record.id}>
                        <td data-label="Student">
                          <div className="monitoring-primary-cell">
                            <strong>{studentName}</strong>
                            <small>{enrollmentInfo}</small>
                          </div>
                        </td>
                        <td data-label="Subject">
                          <span className="badge badge--subject">{record.subject_name || record.subject || '—'}</span>
                          {record.official_subject_code || record.subject_code ? (
                            <small>
                              {record.official_subject_code ? `Official: ${record.official_subject_code}` : ''}
                              {record.official_subject_code && record.subject_code ? ' · ' : ''}
                              {record.subject_code ? `System ID: ${record.subject_code}` : ''}
                            </small>
                          ) : null}
                        </td>
                        <td data-label="Grade / section">
                          <div className="monitoring-meta-cell">
                            <span>{record.academic_year_name || record.academic_year || 'Year unavailable'}</span>
                            <small>{record.grading_period_type || 'Period unavailable'}</small>
                          </div>
                        </td>
                        <td data-label="Period">{record.grading_period_type || '—'}</td>
                        <td data-label="Grade">{record.final_grade ?? record.grade ?? '—'}</td>
                        <td data-label="Status">
                          <span className={`badge ${isAcademicConcern ? 'badge--warning' : 'badge--success'}`}>
                            {isAcademicConcern ? 'Needs attention' : 'On track'}
                          </span>
                        </td>
                        <td data-label="Remarks">{record.remarks || 'No remarks recorded'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

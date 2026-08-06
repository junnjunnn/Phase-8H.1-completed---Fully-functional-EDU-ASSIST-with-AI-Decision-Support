import { useEffect, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
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
          getEnrollments(),
          getAcademicRecords({ search, ordering: '-created_at' }),
        ])

        if (!active) {
          return
        }

        const years = normalizeListResponse(yearsData)
        const gradeLevels = normalizeListResponse(levelsData)
        const subjects = normalizeListResponse(subjectsData)
        const enrollments = normalizeListResponse(enrollmentsData)
        const records = normalizeListResponse(recordsData)

        setSummary({
          years: years.count,
          gradeLevels: gradeLevels.count,
          subjects: subjects.count,
          enrollments: enrollments.count,
          records: records.count,
        })
        setAcademicRecords(records.items.slice(0, 10))
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

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Academics"
        title="Academic monitoring"
        description="Browse academic years, enrollments, subjects, and academic records from the backend."
      />

      <div className="summary-grid">
        <article className="info-card stat-card-accent">
          <p className="stat-label">Academic years</p>
          <p className="stat-value">{summary.years}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Grade levels</p>
          <p className="stat-value">{summary.gradeLevels}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Subjects</p>
          <p className="stat-value">{summary.subjects}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Enrollments</p>
          <p className="stat-value">{summary.enrollments}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Academic records</p>
          <p className="stat-value">{summary.records}</p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic records</p>
            <h2>Latest academic evaluations</h2>
          </div>
          <input
            aria-label="Search academic records"
            placeholder="Search student name or subject"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? <LoadingSpinner label="Loading academic data..." /> : null}

        {!loading && !error && academicRecords.length === 0 ? (
          <EmptyState
            title="No academic records found"
            message="There are no academic records in the backend for the current search criteria."
          />
        ) : null}

        {!loading && !error && academicRecords.length > 0 ? (
          <>
            <p>{pagination.count} record(s) found.</p>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Enrollment</th>
                    <th>Subject</th>
                    <th>Year</th>
                    <th>Period</th>
                    <th>Grade</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {academicRecords.map((record) => (
                    <tr key={record.id}>
                      <td>{record.enrollment || '—'}</td>
                      <td>{record.subject || '—'}</td>
                      <td>{record.academic_year || '—'}</td>
                      <td>{record.grading_period_type || '—'}</td>
                      <td>{record.grade ?? '—'}</td>
                      <td>{record.remarks || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

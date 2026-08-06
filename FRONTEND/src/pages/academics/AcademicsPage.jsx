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

  return (
    <div className="page-stack academics-page">
      <PageHeader
        eyebrow="Academics"
        title="Academic monitoring"
        description="Browse academic years, enrollments, subjects, and academic records from the backend."
      />

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic years</p>
          <p className="stat-value">{summary.years}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Grade levels</p>
          <p className="stat-value">{summary.gradeLevels}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Subjects</p>
          <p className="stat-value">{summary.subjects}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Enrollments</p>
          <p className="stat-value">{summary.enrollments}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic records</p>
          <p className="stat-value">{summary.records}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic records</p>
            <h2>Latest academic evaluations</h2>
          </div>
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search academic records"
              placeholder="Search student name or subject"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
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
                    <th scope="col">Enrollment</th>
                    <th scope="col">Subject</th>
                    <th scope="col">Year</th>
                    <th scope="col">Period</th>
                    <th scope="col">Grade</th>
                    <th scope="col">Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {academicRecords.map((record) => (
                    <tr key={record.id}>
                      <td data-label="Enrollment">{record.enrollment || '—'}</td>
                      <td data-label="Subject">
                        <span className="badge badge--subject">{record.subject || '—'}</span>
                      </td>
                      <td data-label="Year">{record.academic_year || '—'}</td>
                      <td data-label="Period">{record.grading_period_type || '—'}</td>
                      <td data-label="Grade">{record.grade ?? '—'}</td>
                      <td data-label="Remarks">{record.remarks || '—'}</td>
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

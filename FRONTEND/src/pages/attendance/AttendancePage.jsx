import { useEffect, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getAttendanceRecords } from '../../services/attendanceService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

export function AttendancePage() {
  const [attendanceRecords, setAttendanceRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ records: 0, present: 0, absences: 0, tardies: 0 })

  useEffect(() => {
    let active = true

    async function loadAttendance() {
      setLoading(true)
      setError('')

      try {
        const data = await getAttendanceRecords({ search, ordering: '-created_at' })
        if (!active) {
          return
        }

        const normalized = normalizeListResponse(data)
        const records = normalized.items
        const totals = records.reduce(
          (acc, record) => ({
            records: acc.records + 1,
            present: acc.present + (record.days_present || 0),
            absences: acc.absences + (record.absences || 0),
            tardies: acc.tardies + (record.times_tardy || 0),
          }),
          { records: 0, present: 0, absences: 0, tardies: 0 },
        )

        setAttendanceRecords(records.slice(0, 12))
        setSummary({ records: normalized.count, present: totals.present, absences: totals.absences, tardies: totals.tardies })
        setPagination({ count: normalized.count, next: normalized.next, previous: normalized.previous })
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

    loadAttendance()
    return () => {
      active = false
    }
  }, [search])

  return (
    <div className="page-stack attendance-page">
      <PageHeader
        eyebrow="Attendance"
        title="Attendance monitoring"
        description="Review backend attendance records and absence summaries."
      />

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Attendance records</p>
          <p className="stat-value">{summary.records}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Days present</p>
          <p className="stat-value">{summary.present}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Absences</p>
          <p className="stat-value">{summary.absences}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Tardies</p>
          <p className="stat-value">{summary.tardies}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Attendance records</p>
            <h2>Recent attendance snapshots</h2>
          </div>
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search attendance records"
              placeholder="Search by student name or month"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="students-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && attendanceRecords.length === 0 ? (
          <EmptyState
            title={search ? 'No attendance records match search' : 'No attendance records available'}
            message={search ? 'Try a different keyword or clear the search filter.' : 'There are no attendance records available in the backend.'}
          />
        ) : null}

        {!loading && !error && attendanceRecords.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{pagination.count} attendance record{pagination.count === 1 ? '' : 's'} found.</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Enrollment</th>
                    <th scope="col">Month</th>
                    <th scope="col">Days present</th>
                    <th scope="col">Absences</th>
                    <th scope="col">Tardies</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceRecords.map((record) => (
                    <tr key={record.id}>
                      <td data-label="Enrollment">{record.enrollment || '—'}</td>
                      <td data-label="Month">{record.month || '—'}</td>
                      <td data-label="Days present">{record.days_present ?? '—'}</td>
                      <td data-label="Absences">{record.absences ?? '—'}</td>
                      <td data-label="Tardies">{record.times_tardy ?? '—'}</td>
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

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

        setAttendanceRecords(records.slice(0, 10))
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
    <div className="page-stack">
      <PageHeader
        eyebrow="Attendance"
        title="Attendance monitoring"
        description="Review backend attendance records and absence summaries."
      />

      <div className="summary-grid">
        <article className="info-card stat-card-accent">
          <p className="stat-label">Attendance records</p>
          <p className="stat-value">{summary.records}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Days present</p>
          <p className="stat-value">{summary.present}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Absences</p>
          <p className="stat-value">{summary.absences}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Tardies</p>
          <p className="stat-value">{summary.tardies}</p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Attendance records</p>
            <h2>Recent attendance snapshots</h2>
          </div>
          <input
            aria-label="Search attendance records"
            placeholder="Search by student name or month"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? <LoadingSpinner label="Loading attendance data..." /> : null}

        {!loading && !error && attendanceRecords.length === 0 ? (
          <EmptyState
            title="No attendance records found"
            message="There are currently no attendance records available for the current search criteria."
          />
        ) : null}

        {!loading && !error && attendanceRecords.length > 0 ? (
          <>
            <p>{pagination.count} record(s) found.</p>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Enrollment</th>
                    <th>Month</th>
                    <th>Days present</th>
                    <th>Absences</th>
                    <th>Tardies</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceRecords.map((record) => (
                    <tr key={record.id}>
                      <td>{record.enrollment || '—'}</td>
                      <td>{record.month || '—'}</td>
                      <td>{record.days_present ?? '—'}</td>
                      <td>{record.absences ?? '—'}</td>
                      <td>{record.times_tardy ?? '—'}</td>
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

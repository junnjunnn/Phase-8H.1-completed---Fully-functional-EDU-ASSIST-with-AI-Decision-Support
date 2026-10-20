import { useEffect, useMemo, useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getEnrollments } from '../../services/academicsService'
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
  const [status, setStatus] = useState('active')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ records: 0, present: 0, absences: 0, tardies: 0, attendanceRate: 0 })
  const [enrollments, setEnrollments] = useState([])

  useEffect(() => {
    let active = true

    async function loadAttendance() {
      setLoading(true)
      setError('')

      try {
        const [enrollmentData, attendanceData] = await Promise.all([
          status === 'active'
            ? getEnrollments({ active_only: 'true', ordering: 'student__last_name,student__first_name' })
            : getEnrollments({ include_archived: 'true', ordering: 'student__last_name,student__first_name' }),
          getAttendanceRecords({ status, search, ordering: '-created_at' }),
        ])

        if (!active) {
          return
        }

        const normalizedEnrollments = normalizeListResponse(enrollmentData)
        const normalized = normalizeListResponse(attendanceData)
        const records = normalized.items
        const totals = records.reduce(
          (acc, record) => ({
            records: acc.records + 1,
            present: acc.present + (Number(record.days_present) || 0),
            absences: acc.absences + (Number(record.absences) || 0),
            tardies: acc.tardies + (Number(record.times_tardy) || 0),
            schoolDays: acc.schoolDays + (Number(record.school_days) || 0),
          }),
          { records: 0, present: 0, absences: 0, tardies: 0, schoolDays: 0 },
        )

        setEnrollments(normalizedEnrollments.items)
        setAttendanceRecords(records.slice(0, 12))
        setSummary({
          records: normalized.count,
          present: totals.present,
          absences: totals.absences,
          tardies: totals.tardies,
          attendanceRate: totals.schoolDays ? Math.round((totals.present / totals.schoolDays) * 100) : 0,
        })
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
  }, [search, status])

  const enrollmentLookup = useMemo(() => {
    return enrollments.reduce((lookup, enrollment) => {
      const studentName = [enrollment.student_name, enrollment.student?.full_name]
        .filter(Boolean)
        .find(Boolean) || 'Student'
      lookup[enrollment.id] = studentName
      return lookup
    }, {})
  }, [enrollments])

  return (
    <div className="page-stack attendance-page">
      <PageHeader
        eyebrow="Attendance"
        title="Attendance monitoring"
        description="Review attendance patterns, compare absence trends, and move from review to follow-up in a single workspace."
      />

      <section className="detail-card workflow-guide-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Workflow guidance</p>
            <h3>Bring attendance follow-up into focus</h3>
          </div>
        </div>
        <ul className="workflow-guide-list">
          <li>Use the overview cards to spot high-impact attendance concerns quickly.</li>
          <li>Search by student or month to review a narrower set of records.</li>
          <li>Open the attendance encoding flow whenever a class needs immediate updates.</li>
        </ul>
        <div className="workflow-guide-actions">
          <span className="action-chip">Attendance review</span>
          <span className="action-chip">Support follow-up</span>
        </div>
      </section>

      <div className="record-summary-grid monitoring-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Attendance records</p>
          <p className="stat-value">{summary.records}</p>
          <span className="badge badge--info">Latest snapshots</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Overall rate</p>
          <p className="stat-value">{summary.attendanceRate}%</p>
          <span className={`badge ${summary.attendanceRate < 80 ? 'badge--warning' : 'badge--success'}`}>
            {summary.attendanceRate < 80 ? 'Monitor closely' : 'On track'}
          </span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Days present</p>
          <p className="stat-value">{summary.present}</p>
          <span className="badge badge--success">Present</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Absences / tardies</p>
          <p className="stat-value">{summary.absences} / {summary.tardies}</p>
          <span className="badge badge--warning">Follow-up</span>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Attendance records</p>
            <h2>Recent attendance snapshots</h2>
          </div>
          <div className="section-actions">
            <a className="action-button" href="/attendance/encode">Encode attendance</a>
            <label>
              <span className="sr-only">Attendance record status</span>
              <select aria-label="Attendance record status" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
                <option value="all">All</option>
              </select>
            </label>
            <div className="search-input-group">
              <MagnifyingGlassIcon className="icon search-icon" aria-hidden="true" />
              <input
                aria-label="Search attendance records"
                placeholder="Search by student name or month"
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
                    <th scope="col">Student</th>
                    <th scope="col">Month</th>
                    <th scope="col">Attendance %</th>
                    <th scope="col">Present</th>
                    <th scope="col">Absent</th>
                    <th scope="col">Late</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceRecords.map((record) => {
                    const schoolDays = Number(record.school_days || 0)
                    const present = Number(record.days_present || 0)
                    const absent = Number(record.absences || 0)
                    const late = Number(record.times_tardy || 0)
                    const percentage = schoolDays > 0 ? Math.round((present / schoolDays) * 100) : 0
                    const status = percentage < 80 ? 'Needs attention' : 'Stable'
                    const studentName = record.student_name || enrollmentLookup[record.enrollment] || 'Enrollment unavailable'

                    return (
                      <tr key={record.id}>
                        <td data-label="Student">
                          <div className="monitoring-primary-cell">
                            <strong>{studentName}</strong>
                            <small>{record.academic_year_name || 'Historical context'}{record.section_name ? ` · ${record.section_name}` : ''}</small>
                          </div>
                        </td>
                        <td data-label="Month">{record.month || '—'}</td>
                        <td data-label="Attendance %">{percentage}%</td>
                        <td data-label="Present">{present}</td>
                        <td data-label="Absent">{absent}</td>
                        <td data-label="Late">{late}</td>
                        <td data-label="Status">
                          <span className={`badge ${status === 'Needs attention' ? 'badge--warning' : 'badge--success'}`}>{status}</span>
                        </td>
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

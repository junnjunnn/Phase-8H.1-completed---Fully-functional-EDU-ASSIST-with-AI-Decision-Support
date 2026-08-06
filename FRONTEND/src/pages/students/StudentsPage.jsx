import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getStudents } from '../../services/studentService'
import { getApiErrorMessage } from '../../services/api'

function statusBadgeClass(status) {
  const normalized = (status || '').toLowerCase()
  if (normalized.includes('active')) {
    return 'status-pill status-pill--success'
  }
  if (normalized.includes('inactive') || normalized.includes('suspended')) {
    return 'status-pill status-pill--warning'
  }
  if (normalized.includes('graduated') || normalized.includes('completed')) {
    return 'status-pill status-pill--neutral'
  }
  return 'status-pill status-pill--default'
}

export function StudentsPage() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })

  useEffect(() => {
    let active = true

    async function loadStudents() {
      setLoading(true)
      setError('')
      try {
        const data = await getStudents({ search })
        if (!active) {
          return
        }
        setStudents(data.results || [])
        setPagination({ count: data.count || 0, next: data.next, previous: data.previous })
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

    loadStudents()
    return () => {
      active = false
    }
  }, [search])

  return (
    <div className="page-stack students-page">
      <PageHeader eyebrow="Students" title="Student management" description="Browse student records from the backend." />

      <div className="panel-card students-panel">
        <div className="students-toolbar">
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true"><MagnifyingGlassIcon className="icon" /></span>
            <input
              aria-label="Search students"
              placeholder="Search by name or LRN"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="students-meta">
            <p>{pagination.count} student{pagination.count === 1 ? '' : 's'} found</p>
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? (
          <div className="students-skeleton-grid">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="students-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && students.length === 0 ? (
          <EmptyState
            title={search ? 'No students match your search' : 'No students available'}
            message={search ? 'Try another name, LRN, or clear the search filter.' : 'There are no student records available in the system right now.'}
          />
        ) : null}

        {!loading && !error && students.length > 0 ? (
          <div className="students-table-wrapper">
            <table className="students-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">LRN</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="sticky-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id}>
                    <td data-label="Name">
                      <div className="student-row-main">
                        <span className="student-name">{`${student.first_name || ''} ${student.last_name || ''}`.trim() || 'Unknown student'}</span>
                        <span className="student-meta">Grade {student.grade_level || '—'} · Section {student.section || '—'}</span>
                      </div>
                    </td>
                    <td data-label="LRN">{student.lrn || '—'}</td>
                    <td data-label="Status">
                      <span className={statusBadgeClass(student.student_status)}>{student.student_status || 'Unknown'}</span>
                    </td>
                    <td className="action-cell" data-label="Action">
                      <Link
                        className="action-button action-button--primary"
                        to={`/students/${student.id}`}
                        aria-label={`View details for ${student.first_name || ''} ${student.last_name || ''}`.trim()}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  )
}

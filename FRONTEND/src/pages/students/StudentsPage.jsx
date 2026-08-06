import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getStudents } from '../../services/studentService'
import { getApiErrorMessage } from '../../services/api'

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
    <div className="page-stack">
      <PageHeader eyebrow="Students" title="Student management" description="Browse student records from the backend." />

      <div className="panel-card">
        <div className="section-header">
          <input
            aria-label="Search students"
            placeholder="Search by name or LRN"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? <LoadingSpinner label="Loading students..." /> : null}

        {!loading && !error && students.length === 0 ? (
          <EmptyState title="No students found" message="There are currently no student records available in the system." />
        ) : null}

        {!loading && !error && students.length > 0 ? (
          <>
            <p>{pagination.count} record(s) found.</p>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>LRN</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((student) => (
                    <tr key={student.id}>
                      <td>{`${student.first_name || ''} ${student.last_name || ''}`.trim()}</td>
                      <td>{student.lrn || '—'}</td>
                      <td>{student.student_status || '—'}</td>
                      <td>
                        <Link to={`/students/${student.id}`}>View</Link>
                      </td>
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

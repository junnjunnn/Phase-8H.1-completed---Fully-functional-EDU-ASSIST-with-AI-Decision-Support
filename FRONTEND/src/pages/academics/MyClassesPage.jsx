import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getSections } from '../../services/academicsService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function MyClassesPage() {
  const { user } = useAuth()
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadMyClasses() {
      setLoading(true)
      setError('')
      try {
        const data = await getSections({ ordering: 'name' })
        const normalized = normalizeListResponse(data)
        const assignedSections = normalized.items.filter((section) => {
          const adviserId = section.adviser || section.adviser_id || null
          return adviserId === user?.id || String(adviserId) === String(user?.id)
        })
        setSections(assignedSections)
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

  return (
    <div className="page-stack">
      <PageHeader eyebrow="My Classes" title="Assigned classes" description="View the sections you are assigned to teach." />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
      {!loading && sections.length === 0 ? <EmptyState title="No classes assigned" message="You do not have any assigned classes yet." /> : null}
      {!loading && sections.length > 0 ? (
        <div className="panel-card record-panel">
          <div className="record-summary-grid">
            {sections.map((section) => (
              <article key={section.id} className="detail-card">
                <p className="eyebrow">Assigned class</p>
                <h3>{section.grade_level_name || section.grade_level || 'Grade'} · {section.name}</h3>
                <p>{section.academic_year_name || section.academic_year || 'Academic year unavailable'}</p>
                <p>{section.student_count || 0} students</p>
                <p>Status: {section.is_active ? 'Open' : 'Inactive'}</p>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

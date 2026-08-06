import { useEffect, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getInterventions } from '../../services/interventionService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

export function InterventionsPage() {
  const [interventions, setInterventions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ interventions: 0, inProgress: 0, completed: 0 })

  useEffect(() => {
    let active = true

    async function loadInterventions() {
      setLoading(true)
      setError('')

      try {
        const data = await getInterventions({ search, ordering: '-created_at' })
        if (!active) {
          return
        }

        const normalized = normalizeListResponse(data)
        const items = normalized.items
        const statusTotals = items.reduce(
          (acc, item) => {
            const status = item.status || 'unknown'
            return {
              ...acc,
              inProgress: acc.inProgress + (status === 'in_progress' ? 1 : 0),
              completed: acc.completed + (status === 'completed' ? 1 : 0),
            }
          },
          { inProgress: 0, completed: 0 },
        )

        setInterventions(items.slice(0, 10))
        setSummary({ interventions: normalized.count, inProgress: statusTotals.inProgress, completed: statusTotals.completed })
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

    loadInterventions()
    return () => {
      active = false
    }
  }, [search])

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Interventions"
        title="Intervention monitoring"
        description="Track backend intervention assignments, statuses, and follow-up notes."
      />

      <div className="summary-grid">
        <article className="info-card stat-card-accent">
          <p className="stat-label">Interventions</p>
          <p className="stat-value">{summary.interventions}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">In progress</p>
          <p className="stat-value">{summary.inProgress}</p>
        </article>
        <article className="info-card stat-card-accent">
          <p className="stat-label">Completed</p>
          <p className="stat-value">{summary.completed}</p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Intervention records</p>
            <h2>Recent interventions</h2>
          </div>
          <input
            aria-label="Search interventions"
            placeholder="Search by student, type or notes"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? <LoadingSpinner label="Loading intervention data..." /> : null}

        {!loading && !error && interventions.length === 0 ? (
          <EmptyState
            title="No interventions found"
            message="There are currently no intervention records available for the current search criteria."
          />
        ) : null}

        {!loading && !error && interventions.length > 0 ? (
          <>
            <p>{pagination.count} record(s) found.</p>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Enrollment</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Start</th>
                    <th>End</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((item) => (
                    <tr key={item.id}>
                      <td>{item.enrollment || '—'}</td>
                      <td>{item.intervention_type || '—'}</td>
                      <td>{item.status || '—'}</td>
                      <td>{item.priority || '—'}</td>
                      <td>{item.start_date || '—'}</td>
                      <td>{item.end_date || '—'}</td>
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

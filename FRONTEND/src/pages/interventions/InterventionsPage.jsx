import { useEffect, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { InterventionFormModal } from '../../components/interventions/InterventionFormModal'
import { getInterventions, deleteIntervention } from '../../services/interventionService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

function formatInterventionStatus(status) {
  const normalized = (status || '').toLowerCase()
  if (normalized === 'completed') return 'badge--success status-neutral'
  if (normalized === 'in_progress' || normalized === 'in progress') return 'badge--warning status-warning'
  return 'badge--info status-neutral'
}

export function InterventionsPage() {
  const [interventions, setInterventions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ interventions: 0, inProgress: 0, completed: 0 })
  const [showModal, setShowModal] = useState(false)
  const [selectedCurrentValue, setSelectedCurrentValue] = useState(null)

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
            const status = (item.status || '').toLowerCase()
            return {
              inProgress: acc.inProgress + (status === 'in_progress' || status === 'in progress' ? 1 : 0),
              completed: acc.completed + (status === 'completed' ? 1 : 0),
            }
          },
          { inProgress: 0, completed: 0 },
        )

        setInterventions(items.slice(0, 12))
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

  async function refreshInterventions() {
    setLoading(true)
    setError('')

    try {
      const data = await getInterventions({ search, ordering: '-created_at' })
      const normalized = normalizeListResponse(data)
      const items = normalized.items
      const statusTotals = items.reduce(
        (acc, item) => {
          const status = (item.status || '').toLowerCase()
          return {
            inProgress: acc.inProgress + (status === 'in_progress' || status === 'in progress' ? 1 : 0),
            completed: acc.completed + (status === 'completed' ? 1 : 0),
          }
        },
        { inProgress: 0, completed: 0 },
      )

      setInterventions(items.slice(0, 12))
      setSummary({ interventions: normalized.count, inProgress: statusTotals.inProgress, completed: statusTotals.completed })
      setPagination({ count: normalized.count, next: normalized.next, previous: normalized.previous })
      setSuccessMessage('Intervention records refreshed.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(intervention) {
    if (!intervention?.id) {
      return
    }

    if (window.confirm(`Delete this intervention for ${intervention.enrollment || 'the selected enrollment'}?`)) {
      try {
        await deleteIntervention(intervention.id)
        await refreshInterventions()
        setSuccessMessage('Intervention deleted successfully.')
      } catch (err) {
        setError(getApiErrorMessage(err))
      }
    }
  }

  return (
    <div className="page-stack interventions-page">
      <PageHeader
        eyebrow="Interventions"
        title="Intervention monitoring"
        description="Track backend intervention assignments, statuses, and follow-up notes."
        actions={(
          <button type="button" className="action-button action-button--primary" onClick={() => { setSelectedCurrentValue(null); setShowModal(true) }}>
            Create Intervention
          </button>
        )}
      />

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Interventions</p>
          <p className="stat-value">{summary.interventions}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">In progress</p>
          <p className="stat-value">{summary.inProgress}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Completed</p>
          <p className="stat-value">{summary.completed}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Intervention records</p>
            <h2>Recent interventions</h2>
          </div>
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search interventions"
              placeholder="Search by student, type or notes"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="students-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && interventions.length === 0 ? (
          <EmptyState
            title={search ? 'No interventions match search' : 'No intervention records available'}
            message={search ? 'Try a different keyword or clear the search filter.' : 'There are no intervention records returned from the backend.'}
          />
        ) : null}

        {!loading && !error && interventions.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{pagination.count} intervention record{pagination.count === 1 ? '' : 's'} found.</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Enrollment</th>
                    <th scope="col">Type</th>
                    <th scope="col">Status</th>
                    <th scope="col">Priority</th>
                    <th scope="col">Start</th>
                    <th scope="col">End</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((item) => (
                    <tr key={item.id}>
                      <td data-label="Enrollment">{item.enrollment || '—'}</td>
                      <td data-label="Type">{item.intervention_type || '—'}</td>
                      <td data-label="Status">
                        <span className={`badge badge--status ${formatInterventionStatus(item.status)}`}>{item.status || 'Unknown'}</span>
                      </td>
                      <td data-label="Priority">{item.priority || '—'}</td>
                      <td data-label="Start">{item.start_date || '—'}</td>
                      <td data-label="End">{item.end_date || '—'}</td>
                      <td data-label="Actions">
                        <div className="section-actions">
                          <button type="button" className="action-button action-button--neutral" onClick={() => { setSelectedCurrentValue(item); setShowModal(true) }}>Edit</button>
                          <button type="button" className="action-button action-button--danger" onClick={() => handleDelete(item)}>Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>

      <InterventionFormModal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setSelectedCurrentValue(null) }}
        currentValue={selectedCurrentValue}
        studentName="Student"
        latestPrediction={null}
        latestPredictionFactors={[]}
        enrollmentId={selectedCurrentValue?.enrollment ?? null}
        onSaved={async () => {
          setShowModal(false)
          setSelectedCurrentValue(null)
          await refreshInterventions()
          setSuccessMessage('Intervention saved successfully.')
        }}
      />
    </div>
  )
}

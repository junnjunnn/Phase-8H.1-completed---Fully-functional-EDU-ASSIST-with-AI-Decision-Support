import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { useAuth } from '../../context/AuthContext'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getBehavioralAssessments } from '../../services/behaviorService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

export function BehaviorPage() {
  const { user } = useAuth()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageBehavior = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN' || role === 'TEACHER'

  const [behavioralAssessments, setBehavioralAssessments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ assessments: 0 })

  useEffect(() => {
    let active = true

    async function loadBehavior() {
      setLoading(true)
      setError('')

      try {
        const data = await getBehavioralAssessments({ search, ordering: '-assessment_date' })
        if (!active) {
          return
        }

        const normalized = normalizeListResponse(data)
        const assessments = normalized.items

        setBehavioralAssessments(assessments.slice(0, 12))
        setSummary({ assessments: normalized.count })
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

    loadBehavior()
    return () => {
      active = false
    }
  }, [search])

  return (
    <div className="page-stack behavior-page">
      <PageHeader
        eyebrow="Behavior"
        title="Behavior monitoring"
        description="Review behavioral assessments and risk factor summaries from the backend."
        actions={canManageBehavior ? (
          <Link className="action-button" to="/behavior/encode">
            Encode behavior
          </Link>
        ) : null}
      />

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Behavioral assessments</p>
          <p className="stat-value">{summary.assessments}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Behavior assessments</p>
            <h2>Recent behavioral evaluations</h2>
          </div>
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search behavioral assessments"
              placeholder="Search by student or behavior indicator"
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

        {!loading && !error && behavioralAssessments.length === 0 ? (
          <EmptyState
            title={search ? 'No behavior records match search' : 'No behavioral assessments available'}
            message={search ? 'Try a different search term or clear the filter.' : 'There are no behavioral assessment records available from the backend.'}
          />
        ) : null}

        {!loading && !error && behavioralAssessments.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{pagination.count} behavioral record{pagination.count === 1 ? '' : 's'} found.</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Enrollment</th>
                    <th scope="col">Indicator</th>
                    <th scope="col">Rating</th>
                    <th scope="col">Period</th>
                    <th scope="col">Date</th>
                    <th scope="col">Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {behavioralAssessments.map((assessment) => {
                    const ratingDisplay = assessment.rating_code || assessment.rating_label || assessment.rating || '—'
                    const period = assessment.grading_period_type === 'Quarter'
                      ? `Quarter ${assessment.quarter ?? '—'}`
                      : assessment.grading_period_type === 'Semester'
                      ? `Semester ${assessment.semester ?? '—'}`
                      : assessment.grading_period_type || '—'
                    return (
                      <tr key={assessment.id}>
                        <td data-label="Enrollment">{assessment.enrollment || '—'}</td>
                        <td data-label="Indicator">{assessment.behavior_indicator_name || assessment.behavior_indicator || '—'}</td>
                        <td data-label="Rating">{ratingDisplay}</td>
                        <td data-label="Period">{period}</td>
                        <td data-label="Date">{assessment.assessment_date || '—'}</td>
                        <td data-label="Remarks">{assessment.remarks || '—'}</td>
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

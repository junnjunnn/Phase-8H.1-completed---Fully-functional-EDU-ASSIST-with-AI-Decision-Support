import { useEffect, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getBehavioralAssessments } from '../../services/behaviorService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

export function BehaviorPage() {
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

        setBehavioralAssessments(assessments.slice(0, 10))
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
    <div className="page-stack">
      <PageHeader
        eyebrow="Behavior"
        title="Behavior monitoring"
        description="Review behavioral assessments and risk factor summaries from the backend."
      />

      <div className="summary-grid">
        <article className="info-card stat-card-accent">
          <p className="stat-label">Behavioral assessments</p>
          <p className="stat-value">{summary.assessments}</p>
        </article>
      </div>

      <div className="panel-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Behavior assessments</p>
            <h2>Recent behavioral evaluations</h2>
          </div>
          <input
            aria-label="Search behavioral assessments"
            placeholder="Search by student or behavior indicator"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {loading ? <LoadingSpinner label="Loading behavior data..." /> : null}

        {!loading && !error && behavioralAssessments.length === 0 ? (
          <EmptyState
            title="No behavioral assessments found"
            message="There are currently no behavioral assessment records matching your search."
          />
        ) : null}

        {!loading && !error && behavioralAssessments.length > 0 ? (
          <>
            <p>{pagination.count} record(s) found.</p>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Enrollment</th>
                    <th>Indicator</th>
                    <th>Rating</th>
                    <th>Period</th>
                    <th>Date</th>
                    <th>Remarks</th>
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
                        <td>{assessment.enrollment || '—'}</td>
                        <td>{assessment.behavior_indicator_name || assessment.behavior_indicator || '—'}</td>
                        <td>{ratingDisplay}</td>
                        <td>{period}</td>
                        <td>{assessment.assessment_date || '—'}</td>
                        <td>{assessment.remarks || '—'}</td>
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

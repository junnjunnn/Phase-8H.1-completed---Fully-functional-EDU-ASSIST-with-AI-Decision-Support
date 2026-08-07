import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getRiskPredictions, getPredictionFactors } from '../../services/predictionService'
import { getApiErrorMessage } from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  const count = typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0
  return { items, count, next: data?.next || null, previous: data?.previous || null }
}

function formatRiskBadge(level) {
  const normalized = String(level || '').toLowerCase()
  if (normalized.includes('high')) return 'risk-badge high'
  if (normalized.includes('moderate')) return 'risk-badge moderate'
  if (normalized.includes('low')) return 'risk-badge low'
  return 'badge badge--info'
}

function getStudentName(item) {
  const firstName = item.enrollment__student__first_name || item.student_first_name || item.first_name || ''
  const lastName = item.enrollment__student__last_name || item.student_last_name || item.last_name || ''
  const name = `${firstName} ${lastName}`.trim()
  return name || 'Unknown student'
}

function getPredictionGuidance(riskSummary) {
  if (riskSummary.high > 0) {
    return {
      title: 'High risk alert',
      items: [
        'Review high-risk students immediately and connect with teachers or guidance.',
        'Prioritize attendance and academic support plans for these learners.',
        'Use student profiles to validate the latest predictive factors.',
      ],
    }
  }

  if (riskSummary.moderate > 0) {
    return {
      title: 'Moderate risk monitoring',
      items: [
        'Monitor these students closely and look for early intervention opportunities.',
        'Coordinate with subject teachers for targeted support.',
        'Track attendance, grades, and behavior trends consistently.',
      ],
    }
  }

  return {
    title: 'Low risk overview',
    items: [
      'Continue positive reinforcement and maintain current supports.',
      'Share progress updates with the student and family.',
      'Watch for changes over time as new predictions arrive.',
    ],
  }
}
export function PredictionsPage() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [selectedPrediction, setSelectedPrediction] = useState(null)
  const [drawerFactors, setDrawerFactors] = useState([])
  const [drawerLoading, setDrawerLoading] = useState(false)
  const [drawerError, setDrawerError] = useState('')

  useEffect(() => {
    let active = true

    async function loadPredictions() {
      setLoading(true)
      setError('')

      try {
        const data = await getRiskPredictions({ search, ordering: '-prediction_date' })
        if (!active) {
          return
        }

        const normalized = normalizeListResponse(data)
        setPredictions(normalized.items.slice(0, 12))
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

    loadPredictions()
    return () => {
      active = false
    }
  }, [search])

  async function openPredictionDetails(prediction) {
    setSelectedPrediction(prediction)
    setDrawerFactors([])
    setDrawerError('')
    setDrawerLoading(true)

    try {
      const data = await getPredictionFactors({ prediction: prediction.id, ordering: 'feature_name' })
      const normalized = normalizeListResponse(data)
      setDrawerFactors(normalized.items)
    } catch (err) {
      setDrawerError(getApiErrorMessage(err))
    } finally {
      setDrawerLoading(false)
    }
  }

  function closePredictionDrawer() {
    setSelectedPrediction(null)
    setDrawerFactors([])
    setDrawerError('')
    setDrawerLoading(false)
  }

  function getRiskTrend(current, previous) {
    if (!current || !previous) {
      return 'No trend available yet.'
    }
    const ranking = { Low: 1, Moderate: 2, High: 3 }
    const currentRank = ranking[current.risk_level] || 0
    const previousRank = ranking[previous.risk_level] || 0
    if (currentRank > previousRank) return 'Risk is increasing compared to the prior prediction.'
    if (currentRank < previousRank) return 'Risk is decreasing compared to the prior prediction.'
    return 'Risk trend remains stable from the previous prediction.'
  }

  const riskSummary = predictions.reduce(
    (acc, item) => {
      const level = String(item.risk_level || '').toLowerCase()
      if (level.includes('high')) acc.high += 1
      else if (level.includes('moderate')) acc.moderate += 1
      else if (level.includes('low')) acc.low += 1
      return acc
    },
    { high: 0, moderate: 0, low: 0 },
  )

  const predictionGuidance = useMemo(() => getPredictionGuidance(riskSummary), [riskSummary])
  const recentAlerts = predictions.slice(0, 4)

  return (
    <div className="page-stack predictions-page">
      <PageHeader
        eyebrow="Predictions"
        title="Risk predictions"
        description="Review AI-driven student risk predictions generated by the backend."
      />

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Prediction results</p>
          <p className="stat-value">{pagination.count}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">High risk</p>
          <p className="stat-value">{riskSummary.high}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Moderate risk</p>
          <p className="stat-value">{riskSummary.moderate}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Low risk</p>
          <p className="stat-value">{riskSummary.low}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Risk predictions</p>
            <h2>Latest risk alerts</h2>
          </div>
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true">🔎</span>
            <input
              aria-label="Search predictions"
              placeholder="Search by student name or risk level"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        <div className="prediction-guidance-panel">
          <div>
            <p className="eyebrow">AI decision support</p>
            <h3>{predictionGuidance.title}</h3>
          </div>
          <ul className="support-list">
            {predictionGuidance.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        {error ? <ErrorBanner message={error} /> : null}

        {!loading && recentAlerts.length > 0 ? (
          <div className="recent-alerts-grid">
            {recentAlerts.map((alert) => (
              <article key={alert.id} className="detail-card alert-card">
                <p className="eyebrow">{alert.risk_level || 'Risk'}</p>
                <h3>{getStudentName(alert)}</h3>
                <p>{alert.enrollment__grade_level__name || alert.grade_level || 'Grade unavailable'} · {alert.prediction_date || 'Date unavailable'}</p>
                <div className="alert-card-meta">
                  <span>{alert.probability != null ? `${Math.round(alert.probability * 100)}%` : 'N/A'}</span>
                  {alert.enrollment__student__id ? (
                    <Link to={`/students/${alert.enrollment__student__id}`} className="detail-link">
                      Profile
                    </Link>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        ) : null}

        {loading ? (
          <div className="table-skeleton-grid">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="students-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && predictions.length === 0 ? (
          <EmptyState
            title={search ? 'No predictions match search' : 'No predictions available'}
            message={search ? 'Try another name or remove the filter to see more results.' : 'There are no risk predictions returned from the backend yet.'}
          />
        ) : null}

        {!loading && !error && predictions.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{pagination.count} prediction record{pagination.count === 1 ? '' : 's'} found.</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Student</th>
                    <th scope="col">Grade</th>
                    <th scope="col">Risk level</th>
                    <th scope="col">Probability</th>
                    <th scope="col">Predicted</th>
                    <th scope="col">Profile</th>
                    <th scope="col">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((item) => (
                    <tr key={item.id}>
                      <td data-label="Student">{getStudentName(item)}</td>
                      <td data-label="Grade">{item.enrollment__grade_level__name || item.grade_level || '—'}</td>
                      <td data-label="Risk level">
                        <span className={formatRiskBadge(item.risk_level)}>{item.risk_level || 'Unknown'}</span>
                      </td>
                      <td data-label="Probability">{item.probability != null ? `${Math.round(item.probability * 100)}%` : 'N/A'}</td>
                      <td data-label="Predicted">{item.prediction_date || '—'}</td>
                      <td data-label="Profile">
                        {item.enrollment__student__id ? (
                          <Link to={`/students/${item.enrollment__student__id}`} className="detail-link">
                            View
                          </Link>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td data-label="Details">
                        <button type="button" className="action-button action-button--outline" onClick={() => openPredictionDetails(item)}>
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </div>

      {selectedPrediction ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={closePredictionDrawer}>
          <aside className="detail-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <p className="eyebrow">Prediction details</p>
                <h2>{getStudentName(selectedPrediction)}</h2>
                <p>{selectedPrediction.enrollment__grade_level__name || selectedPrediction.grade_level || 'Grade unavailable'} · {selectedPrediction.prediction_date || 'Date unavailable'}</p>
              </div>
              <button type="button" className="icon-button" aria-label="Close details" onClick={closePredictionDrawer}>
                ×
              </button>
            </div>

            <div className="drawer-metrics-grid">
              <div>
                <p className="stat-label">Risk level</p>
                <p className={formatRiskBadge(selectedPrediction.risk_level)}>{selectedPrediction.risk_level || 'Unknown'}</p>
              </div>
              <div>
                <p className="stat-label">Confidence</p>
                <p>{selectedPrediction.probability != null ? `${Math.round(selectedPrediction.probability * 100)}%` : 'N/A'}</p>
              </div>
              <div>
                <p className="stat-label">Model</p>
                <p>{selectedPrediction.model_name || selectedPrediction.model_version || 'Unknown'}</p>
              </div>
              <div>
                <p className="stat-label">Prediction type</p>
                <p>{selectedPrediction.prediction_type || 'N/A'}</p>
              </div>
            </div>

            <div className="drawer-section">
              <p className="eyebrow">Insight</p>
              <p>{selectedPrediction.explanation || 'No explanation summary is available for this prediction.'}</p>
            </div>

            <div className="drawer-section">
              <p className="eyebrow">Trend comparison</p>
              <p>{getRiskTrend(selectedPrediction, predictions.find((item) => item.id !== selectedPrediction.id))}</p>
            </div>

            <div className="drawer-section">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Contributing factors</p>
                  <h3>Prediction drivers</h3>
                </div>
              </div>
              {drawerError ? <ErrorBanner message={drawerError} /> : null}
              {drawerLoading ? (
                <div className="table-skeleton-grid">
                  <div className="table-skeleton-card" />
                  <div className="table-skeleton-card" />
                </div>
              ) : null}
              {!drawerLoading && !drawerError && drawerFactors.length === 0 ? (
                <EmptyState title="No factor details" message="No prediction factors are available for this record." />
              ) : null}
              {!drawerLoading && drawerFactors.length > 0 ? (
                <div className="table-card factor-table-card">
                  <table>
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>Value</th>
                        <th>Contribution</th>
                        <th>Direction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {drawerFactors.map((factor) => (
                        <tr key={factor.id}>
                          <td>{factor.feature_name}</td>
                          <td>{factor.feature_value}</td>
                          <td>{factor.contribution != null ? `${Math.round(factor.contribution * 100)}%` : 'N/A'}</td>
                          <td>{factor.direction || 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </div>
          </aside>
        </div>
      ) : null}
    </div>
  )
}

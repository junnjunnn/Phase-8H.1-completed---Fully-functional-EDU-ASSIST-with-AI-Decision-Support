import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import {
  AcademicCapIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  SparklesIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { getApiErrorMessage } from '../../services/api'
import { getDashboardSummary } from '../../services/predictionService'

const placeholderCards = [
  { title: 'Total students', message: 'Loading…', icon: UserGroupIcon },
  { title: 'Risk predictions', message: 'Loading…', icon: SparklesIcon },
  { title: 'At-risk students', message: 'Loading…', icon: ExclamationTriangleIcon },
  { title: 'High risk', message: 'Loading…', icon: ShieldExclamationIcon },
  { title: 'Moderate risk', message: 'Loading…', icon: ChartBarIcon },
  { title: 'Low risk', message: 'Loading…', icon: CheckCircleIcon },
]

const riskBadgeClass = (level) => {
  const normalized = String(level ?? '').toLowerCase()
  if (normalized.includes('high')) return 'badge badge--high'
  if (normalized.includes('moderate')) return 'badge badge--warning'
  if (normalized.includes('low')) return 'badge badge--success'
  return 'badge badge--info'
}

export function Dashboard() {
  const { user } = useAuth()
  const [dashboardData, setDashboardData] = useState(null)
  const [dashboardError, setDashboardError] = useState('')
  const [dashboardLoading, setDashboardLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function fetchDashboard() {
      setDashboardError('')
      setDashboardLoading(true)

      try {
        const summary = await getDashboardSummary()
        if (!active) return
        setDashboardData(summary)
      } catch (error) {
        if (!active) return
        setDashboardError(getApiErrorMessage(error))
      } finally {
        if (active) {
          setDashboardLoading(false)
        }
      }
    }

    fetchDashboard()
    return () => {
      active = false
    }
  }, [])

  const currentDate = useMemo(
    () =>
      new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }).format(new Date()),
    [],
  )

  const summaryCards = dashboardData
    ? [
        { title: 'Total students', message: dashboardData.total_students ?? 'N/A', icon: UserGroupIcon },
        { title: 'Risk predictions', message: dashboardData.total_predictions ?? 'N/A', icon: SparklesIcon },
        { title: 'At-risk students', message: dashboardData.at_risk_students ?? 'N/A', icon: ExclamationTriangleIcon },
        { title: 'High risk', message: dashboardData.high_risk_students ?? 'N/A', icon: ShieldExclamationIcon },
        { title: 'Moderate risk', message: dashboardData.moderate_risk_students ?? 'N/A', icon: ChartBarIcon },
        { title: 'Low risk', message: dashboardData.low_risk_students ?? 'N/A', icon: CheckCircleIcon },
      ]
    : placeholderCards

  const riskDistribution = dashboardData?.risk_distribution || {}
  const attentionStudents = dashboardData?.attention_students || []
  const distributionEntries = Object.entries(riskDistribution)
  const distributionTotal = distributionEntries.reduce((sum, [, count]) => sum + Number(count || 0), 0)

  const highestRiskLevel = useMemo(() => {
    if (!distributionEntries.length) return 'None'
    const highest = distributionEntries.reduce(
      (selected, entry) => (Number(entry[1] || 0) > Number(selected[1] || 0) ? entry : selected),
      ['', 0],
    )
    return highest[0] || 'None'
  }, [distributionEntries])

  const atRiskProportion = useMemo(() => {
    if (!dashboardData?.total_students) return 'N/A'
    return `${Math.round(((dashboardData.at_risk_students || 0) / dashboardData.total_students) * 100)}%`
  }, [dashboardData])

  const attentionCards = attentionStudents.slice(0, 4)

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Welcome back, {user?.username || 'User'}</h1>
          <p className="dashboard-hero-text">
            Monitor student performance and identify learners requiring early intervention through AI-powered decision support.
          </p>
          <div className="dashboard-meta">
            <span>{currentDate}</span>
            <span className="badge badge--info">{user?.role || 'No role'}</span>
          </div>
        </div>
        <div className="dashboard-hero-summary">
          <div className="dashboard-hero-card">
            <p className="dashboard-hero-card-label">Live risk monitoring</p>
            <strong>{dashboardData?.total_predictions ?? '—'}</strong>
          </div>
          <div className="dashboard-hero-card">
            <p className="dashboard-hero-card-label">Active attention alerts</p>
            <strong>{attentionStudents.length}</strong>
          </div>
        </div>
      </section>

      {dashboardError ? <ErrorBanner message={dashboardError} /> : null}
      {dashboardLoading ? (
        <div className="dashboard-skeleton-grid">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="skeleton-card" />
          ))}
        </div>
      ) : (
        <>
          <section className="dashboard-summary-grid" aria-label="Summary metrics">
            {summaryCards.map((card) => (
              <article key={card.title} className="dashboard-metric-card">
                <div className="dashboard-metric-icon">
                  {card.icon ? <card.icon className="icon" /> : null}
                </div>
                <div>
                  <p className="stat-label">{card.title}</p>
                  <p className="stat-value">{card.message}</p>
                </div>
              </article>
            ))}
          </section>

          <section className="dashboard-content-grid">
            <div className="dashboard-panel dashboard-panel--wide">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Risk distribution</p>
                  <h2>Student risk breakdown</h2>
                </div>
                <span className="badge badge--info">Total {distributionTotal}</span>
              </div>
              <div className="risk-distribution">
                {distributionEntries.map(([level, count]) => {
                  const percent = distributionTotal ? Math.round((Number(count || 0) / distributionTotal) * 100) : 0
                  return (
                    <div key={level} className="risk-item">
                      <div className="risk-item-top">
                        <span>{level}</span>
                        <span>{count ?? 0} students</span>
                      </div>
                      <div className="risk-bar">
                        <div className="risk-bar-fill" style={{ width: `${percent}%` }} />
                      </div>
                      <div className="risk-item-footer">
                        <span className={riskBadgeClass(level)}>{percent}%</span>
                        <span>{count ?? 0}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="dashboard-panel dashboard-panel--compact">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Quick insights</p>
                  <h2>Current performance signals</h2>
                </div>
              </div>
              <div className="insights-grid">
                <article className="insight-card">
                  <p>Total predictions</p>
                  <strong>{dashboardData?.total_predictions ?? 'N/A'}</strong>
                </article>
                <article className="insight-card">
                  <p>At-risk proportion</p>
                  <strong>{atRiskProportion}</strong>
                </article>
                <article className="insight-card">
                  <p>Highest risk observed</p>
                  <strong>{highestRiskLevel}</strong>
                </article>
              </div>
            </div>
          </section>

          <section className="dashboard-content-grid">
            <div className="dashboard-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Recent predictions</p>
                  <h2>Latest AI alerts</h2>
                </div>
              </div>
              {attentionStudents.length === 0 ? (
                <EmptyState title="No recent predictions" message="There are no recent prediction alerts for this period." />
              ) : (
                <div className="table-card recent-predictions-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Grade</th>
                        <th>Risk</th>
                        <th>Probability</th>
                        <th>Predicted</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attentionStudents.map((item) => (
                        <tr key={item.id}>
                          <td>{`${item.enrollment__student__first_name} ${item.enrollment__student__last_name}`}</td>
                          <td>{item.enrollment__grade_level__name || 'Unknown'}</td>
                          <td>
                            <span className={riskBadgeClass(item.risk_level)}>{item.risk_level}</span>
                          </td>
                          <td>{item.probability != null ? `${Math.round(item.probability * 100)}%` : 'N/A'}</td>
                          <td>{item.prediction_date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="dashboard-panel dashboard-panel--compact">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Students needing attention</p>
                  <h2>Priority student alerts</h2>
                </div>
              </div>
              {attentionCards.length === 0 ? (
                <EmptyState title="No attention alerts" message="Priority student monitoring is currently clear." />
              ) : (
                <div className="attention-stack">
                  {attentionCards.map((item) => (
                    <article key={item.id} className="attention-card">
                      <div className="attention-card-top">
                        <div>
                          <p className="attention-name">{`${item.enrollment__student__first_name} ${item.enrollment__student__last_name}`}</p>
                          <p className="attention-note">{item.enrollment__grade_level__name || 'Grade unknown'}</p>
                        </div>
                        <span className={riskBadgeClass(item.risk_level)}>{item.risk_level}</span>
                      </div>
                      <div className="attention-details">
                        <span>{item.probability != null ? `${Math.round(item.probability * 100)}% probability` : 'Probability unknown'}</span>
                        <span>{item.prediction_date}</span>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="dashboard-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">AI decision support</p>
                <h2>Empowering educators with evidence-based direction</h2>
              </div>
            </div>
            <div className="support-grid">
              <article className="support-card">
                <h3>Intervention prioritization</h3>
                <p>Identify students requiring immediate attention and match them to academic or behavioral interventions.</p>
              </article>
              <article className="support-card">
                <h3>Trend visibility</h3>
                <p>Monitor the risk mix across the student population and surface changes in at-risk counts.</p>
              </article>
              <article className="support-card">
                <h3>Focused follow-up</h3>
                <p>Use the latest prediction alerts to coordinate with teachers and guidance counselors.</p>
              </article>
            </div>
          </section>
        </>
      )}

      <section className="dashboard-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Quick actions</p>
            <h2>Navigate the core modules</h2>
          </div>
        </div>
        <div className="quick-actions">
          <Link className="action-button" to="/students">View Students</Link>
          <Link className="action-button" to="/academics">Academic Records</Link>
          <Link className="action-button" to="/attendance">Attendance</Link>
          <Link className="action-button" to="/behavior">Behavior</Link>
          <Link className="action-button" to="/interventions">Interventions</Link>
          <Link className="action-button" to="/reports?category=ai">Open AI reports</Link>
          <Link className="action-button" to="/reports?category=attendance">Open attendance reports</Link>
          <Link className="action-button" to="/reports?category=intervention">Open intervention reports</Link>
        </div>
      </section>
    </div>
  )
}

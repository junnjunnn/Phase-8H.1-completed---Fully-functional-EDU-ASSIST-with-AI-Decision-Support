import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getDashboardSummary } from '../../services/predictionService'

const placeholderCards = [
  { title: 'Total students', message: 'Loading…' },
  { title: 'Risk predictions', message: 'Loading…' },
  { title: 'At-risk students', message: 'Loading…' },
  { title: 'High risk', message: 'Loading…' },
  { title: 'Moderate risk', message: 'Loading…' },
  { title: 'Low risk', message: 'Loading…' },
]

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

  const summaryCards = dashboardData
    ? [
        { title: 'Total students', message: dashboardData.total_students ?? 'N/A' },
        { title: 'Risk predictions', message: dashboardData.total_predictions ?? 'N/A' },
        { title: 'At-risk students', message: dashboardData.at_risk_students ?? 'N/A' },
        { title: 'High risk', message: dashboardData.high_risk_students ?? 'N/A' },
        { title: 'Moderate risk', message: dashboardData.moderate_risk_students ?? 'N/A' },
        { title: 'Low risk', message: dashboardData.low_risk_students ?? 'N/A' },
      ]
    : placeholderCards

  const riskDistribution = dashboardData?.risk_distribution || {}
  const attentionStudents = dashboardData?.attention_students || []

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome, ${user?.username || 'User'}`}
        description={`Role: ${user?.role || 'NONE'}`}
      />

      <div className="hero-card">
        <p className="eyebrow">Connected</p>
        <h2>EDU ASSIST is linked to the Django REST API</h2>
        <p>Live student risk monitoring, intervention status, and prediction summaries are available here.</p>
      </div>

      <div className="summary-grid">
        {summaryCards.map((card) => (
          <article key={card.title} className="info-card stat-card-accent">
            <p className="stat-label">{card.title}</p>
            <p className="stat-value">{card.message}</p>
          </article>
        ))}
      </div>

      {dashboardError ? <ErrorBanner message={dashboardError} /> : null}
      {dashboardLoading ? <LoadingSpinner label="Loading dashboard metrics..." /> : null}

      {!dashboardLoading && !dashboardError && (
        <>
          <div className="panel-card">
            <div className="section-header">
              <div>
                <p className="eyebrow">Risk distribution</p>
                <h2>AI risk segmentation</h2>
              </div>
            </div>
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Risk level</th>
                    <th>Student count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(riskDistribution).map(([level, count]) => (
                    <tr key={level}>
                      <td>{level}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel-card">
            <div className="section-header">
              <div>
                <p className="eyebrow">Priority students</p>
                <h2>Top students needing attention</h2>
              </div>
            </div>
            {attentionStudents.length === 0 ? (
              <EmptyState title="No priority students" message="No recent high-risk students were identified." />
            ) : (
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Grade level</th>
                      <th>Risk</th>
                      <th>Confidence</th>
                      <th>Predicted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attentionStudents.map((item) => (
                      <tr key={item.id}>
                        <td>{`${item.enrollment__student__first_name} ${item.enrollment__student__last_name}`}</td>
                        <td>{item.enrollment__grade_level__name || 'Unknown'}</td>
                        <td>{item.risk_level}</td>
                        <td>{item.probability != null ? `${Math.round(item.probability * 100)}%` : 'N/A'}</td>
                        <td>{item.prediction_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="panel-card">
            <div className="section-header">
              <div>
                <p className="eyebrow">Action guidance</p>
                <h2>Where administrators should focus</h2>
              </div>
            </div>
            <div className="panel-card">
              <p>Use the risk distribution and recent prediction activity to prioritize students for targeted academic support, behavior coaching, and intervention planning.</p>
              <ul>
                <li>Review high-risk cases first and confirm that interventions are active.</li>
                <li>Track moderate-risk students for worsening attendance or grades.</li>
                <li>Use recent prediction summaries to follow up with teachers and guidance staff.</li>
              </ul>
            </div>
          </div>
        </>
      )}

      <div className="panel-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Quick actions</p>
            <h2>Navigate to the main modules</h2>
          </div>
        </div>
        <div className="quick-actions">
          <Link className="action-button" to="/students">View Students</Link>
          <Link className="action-button" to="/academics">Academic Records</Link>
          <Link className="action-button" to="/attendance">Attendance</Link>
          <Link className="action-button" to="/behavior">Behavior</Link>
          <Link className="action-button" to="/interventions">Interventions</Link>
        </div>
      </div>
    </div>
  )
}

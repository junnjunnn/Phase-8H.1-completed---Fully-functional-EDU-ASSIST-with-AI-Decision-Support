import { useEffect, useState } from 'react'
import { CalendarDaysIcon, ChartBarIcon, ClipboardDocumentListIcon, UserGroupIcon } from '@heroicons/react/24/outline'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getRegistrarDashboard } from '../../services/predictionService'

function formatMetric(value) {
  return value == null ? 'N/A' : value.toLocaleString?.() ?? value
}

function formatDate(value) {
  if (!value) return 'No date'
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

export function RegistrarDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getRegistrarDashboard()
      .then((response) => { if (active) setData(response) })
      .catch((requestError) => { if (active) setError(getApiErrorMessage(requestError)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) {
    return <div className="dashboard-page"><PageHeader title="Registrar Dashboard" description="Monitor current student registration and enrollment operations." /><div className="dashboard-skeleton-grid">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="skeleton-card" />)}</div></div>
  }

  const distribution = data?.enrollment_distribution || []
  const distributionTotal = distribution.reduce((total, item) => total + Number(item.count || 0), 0)
  const recentEnrollments = data?.recent_enrollments || []

  return (
    <div className="dashboard-page registrar-dashboard">
      <PageHeader title="Registrar Dashboard" description="Monitor current student registration and enrollment operations." />
      {error ? <ErrorBanner message={error} /> : null}

      <section className="dashboard-summary-grid" aria-label="Registrar summary metrics">
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><UserGroupIcon className="icon" /></div><div><p className="stat-label">Active students</p><p className="stat-value">{formatMetric(data?.total_active_students)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ClipboardDocumentListIcon className="icon" /></div><div><p className="stat-label">Active enrollments</p><p className="stat-value">{formatMetric(data?.total_active_enrollments)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><UserGroupIcon className="icon" /></div><div><p className="stat-label">Active sections</p><p className="stat-value">{formatMetric(data?.total_active_sections)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><CalendarDaysIcon className="icon" /></div><div><p className="stat-label">Current academic year</p><p className="stat-value">{data?.current_academic_year || 'N/A'}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><CalendarDaysIcon className="icon" /></div><div><p className="stat-label">Number of school days</p><p className="stat-value">{formatMetric(data?.school_days)}</p></div></article>
      </section>

      <section className="dashboard-content-grid">
        <div className="dashboard-panel dashboard-panel--wide">
          <div className="panel-heading"><div><p className="eyebrow">Current enrollment</p><h2>Distribution by grade level</h2></div><span className="badge badge--info">Total {distributionTotal}</span></div>
          {distribution.length ? <div className="risk-distribution">{distribution.map((item) => { const percent = distributionTotal ? Math.round((item.count / distributionTotal) * 100) : 0; return <div key={item.grade_level_id} className="risk-item"><div className="risk-item-top"><span>{item.grade_level__name}</span><strong>{item.count}</strong></div><div className="risk-bar"><div className="risk-bar-fill" style={{ width: `${percent}%` }} /></div><div className="risk-item-footer"><span>{percent}%</span><span>{item.count} enrollments</span></div></div> })}</div> : <EmptyState title="No active enrollments" message="There are no current enrollment records to distribute." />}
        </div>
        <div className="dashboard-panel">
          <div className="panel-heading"><div><p className="eyebrow">Registration activity</p><h2>Recent enrollments</h2></div><ChartBarIcon className="icon" /></div>
          {recentEnrollments.length ? <div className="table-card"><table><thead><tr><th>Student</th><th>Grade / section</th><th>Date</th></tr></thead><tbody>{recentEnrollments.map((item) => <tr key={item.id}><td>{item.student__first_name} {item.student__last_name}</td><td>{item.grade_level__name} · {item.section__name || 'Unassigned'}</td><td>{formatDate(item.enrollment_date)}</td></tr>)}</tbody></table></div> : <EmptyState title="No recent enrollments" message="No active registration activity is available." />}
        </div>
      </section>
    </div>
  )
}
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDaysIcon, ChartBarIcon, ExclamationTriangleIcon, UserGroupIcon, SparklesIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getAdviserDashboard } from '../../services/predictionService'

function riskBadgeClass(level) {
  const value = String(level || '').toLowerCase()
  if (value === 'high') return 'badge badge--high'
  if (value === 'moderate') return 'badge badge--warning'
  if (value === 'low') return 'badge badge--success'
  return 'badge badge--info'
}

function formatMetric(value) {
  return value == null ? 'N/A' : value
}

export function AdviserDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    getAdviserDashboard()
      .then((response) => {
        if (mounted) setData(response)
      })
      .catch((requestError) => {
        if (mounted) setError(getApiErrorMessage(requestError))
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => { mounted = false }
  }, [])

  if (loading) {
    return <div className="dashboard-page"><PageHeader title="Adviser Dashboard" description="Monitor your currently assigned advisory students." /><div className="dashboard-skeleton-grid">{Array.from({ length: 6 }).map((_, index) => <div key={index} className="skeleton-card" />)}</div></div>
  }

  if (error) {
    return <div className="dashboard-page"><PageHeader title="Adviser Dashboard" description="Monitor your currently assigned advisory students." /><ErrorBanner message={error} /></div>
  }

  const summary = data?.summary || {}
  const attentionStudents = data?.students_requiring_attention || []
  const riskDistribution = Object.entries(data?.risk_distribution || {})
  const riskTotal = riskDistribution.reduce((total, [, count]) => total + Number(count || 0), 0)
  const attendanceSummary = data?.attendance_summary || {}
  const behaviorSummary = data?.behavior_summary || {}

  return (
    <div className="dashboard-page adviser-dashboard">
      <PageHeader title="Adviser Dashboard" description="Monitor your currently assigned advisory students." />

      <section className="dashboard-summary-grid" aria-label="Adviser summary metrics">
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><UserGroupIcon className="icon" /></div><div><p className="stat-label">Active students</p><p className="stat-value">{formatMetric(summary.active_students)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><UserGroupIcon className="icon" /></div><div><p className="stat-label">Total students</p><p className="stat-value">{formatMetric(summary.total_students)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ChartBarIcon className="icon" /></div><div><p className="stat-label">Class average</p><p className="stat-value">{formatMetric(summary.class_general_average)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><CalendarDaysIcon className="icon" /></div><div><p className="stat-label">Attendance rate</p><p className="stat-value">{summary.attendance_rate == null ? 'N/A' : `${summary.attendance_rate}%`}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><CalendarDaysIcon className="icon" /></div><div><p className="stat-label">Number of School Days</p><p className="stat-value">{formatMetric(data?.school_days)}</p><p className="support-copy">{data?.academic_year ? `Current Academic Year: ${data.academic_year}` : 'Current Academic Year'}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ExclamationTriangleIcon className="icon" /></div><div><p className="stat-label">Academic concerns</p><p className="stat-value">{formatMetric(summary.academic_concerns)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ExclamationTriangleIcon className="icon" /></div><div><p className="stat-label">Attendance records</p><p className="stat-value">{formatMetric(attendanceSummary.record_count)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ShieldCheckIcon className="icon" /></div><div><p className="stat-label">Behavior records</p><p className="stat-value">{formatMetric(behaviorSummary.record_count)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ShieldCheckIcon className="icon" /></div><div><p className="stat-label">Active interventions</p><p className="stat-value">{formatMetric(summary.active_interventions)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><SparklesIcon className="icon" /></div><div><p className="stat-label">Follow-up required</p><p className="stat-value">{formatMetric(summary.follow_up_required)}</p></div></article>
        <article className="dashboard-metric-card"><div className="dashboard-metric-icon"><ExclamationTriangleIcon className="icon" /></div><div><p className="stat-label">Needs attention</p><p className="stat-value">{formatMetric(summary.students_requiring_attention)}</p></div></article>
      </section>

      <section className="dashboard-content-grid">
        <div className="dashboard-panel dashboard-panel--wide">
          <div className="panel-heading"><div><p className="eyebrow">Advisory sections</p><h2>{summary.total_students || 0} students in scope</h2></div></div>
          {data?.sections?.length ? <div className="adviser-section-list">{data.sections.map((section) => <span key={section.id} className="badge badge--info">{section.grade_level__name} · {section.name} · {section.academic_year__name}</span>)}</div> : <EmptyState title="No advisory sections" message="There are no active advisory sections assigned to this account." />}
        </div>
        <div className="dashboard-panel">
          <div className="panel-heading"><div><p className="eyebrow">Stored predictions</p><h2>Risk distribution</h2></div></div>
          {riskTotal ? <div className="risk-distribution">{riskDistribution.map(([level, count]) => <div key={level} className="risk-item"><div className="risk-item-top"><span>{level}</span><strong>{count}</strong></div><div className="risk-bar"><div className="risk-bar-fill" style={{ width: `${Math.round((count / riskTotal) * 100)}%` }} /></div></div>)}</div> : <EmptyState title="No predictions available" message="No stored risk predictions exist for your active advisory students." />}
        </div>
      </section>

      <section className="dashboard-panel">
        <div className="panel-heading"><div><p className="eyebrow">Priority monitoring</p><h2>Students requiring attention</h2></div><span className="badge badge--warning">{attentionStudents.length}</span></div>
        {attentionStudents.length === 0 ? <EmptyState title="No attention items" message="No current academic, intervention, follow-up, or stored risk concerns were found." /> : <div className="table-card adviser-attention-table"><table><thead><tr><th>Student</th><th>Grade / section</th><th>Average</th><th>Attendance</th><th>Behavior</th><th>Risk</th><th>Support signals</th></tr></thead><tbody>{attentionStudents.map((student) => <tr key={student.id}><td><Link to={`/students/${student.id}`}>{student.name}</Link></td><td>{student.grade} · {student.section}</td><td>{student.general_average ?? 'N/A'}</td><td>{student.attendance_percentage == null ? 'N/A' : `${student.attendance_percentage}%`}</td><td>{student.behavior_average ?? 'N/A'}</td><td>{student.risk_level ? <><span className={riskBadgeClass(student.risk_level)}>{student.risk_level}</span><small>{student.risk_probability == null ? 'Probability N/A' : `${Math.round(student.risk_probability * 100)}% probability`}</small>{student.risk_explanation || student.risk_factors?.length ? <details><summary>Prediction details</summary>{student.risk_explanation ? <p>{student.risk_explanation}</p> : null}{student.risk_factors?.length ? <ul>{student.risk_factors.map((factor) => <li key={`${factor.feature_name}-${factor.feature_value}`}>{factor.feature_name}: {factor.explanation_text || factor.feature_value}</li>)}</ul> : null}</details> : null}</> : 'N/A'}</td><td>{student.concerns.join(', ')}</td></tr>)}</tbody></table></div>}
      </section>

      <p className="support-copy adviser-dashboard-disclaimer">{data?.disclaimer}</p>
    </div>
  )
}

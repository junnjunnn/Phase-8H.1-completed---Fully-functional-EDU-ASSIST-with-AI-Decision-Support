import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { EmptyState } from '../../components/common/EmptyState'
import { useAuth } from '../../context/AuthContext'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getEnrollments } from '../../services/academicsService'
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
  const [status, setStatus] = useState('active')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [summary, setSummary] = useState({ assessments: 0, averageRating: '—', followUps: 0 })
  const [enrollments, setEnrollments] = useState([])

  useEffect(() => {
    let active = true

    async function loadBehavior() {
      setLoading(true)
      setError('')

      try {
        const [enrollmentData, behaviorData] = await Promise.all([
          status === 'active'
            ? getEnrollments({ active_only: 'true', ordering: 'student__last_name,student__first_name' })
            : getEnrollments({ include_archived: 'true', ordering: 'student__last_name,student__first_name' }),
          getBehavioralAssessments({ status, search, ordering: '-assessment_date' }),
        ])

        if (!active) {
          return
        }

        const normalizedEnrollments = normalizeListResponse(enrollmentData)
        const normalized = normalizeListResponse(behaviorData)
        const assessments = normalized.items
        const numericRatings = assessments
          .map((assessment) => Number(assessment.numeric_score))
          .filter((value) => !Number.isNaN(value))

        const averageRating = numericRatings.length
          ? (numericRatings.reduce((sum, value) => sum + value, 0) / numericRatings.length).toFixed(2)
          : '—'
        const followUps = assessments.filter((assessment) => {
          const numericScore = Number(assessment.numeric_score)
          return !Number.isNaN(numericScore) && numericScore < 3
        }).length

        setEnrollments(normalizedEnrollments.items)
        setBehavioralAssessments(assessments.slice(0, 12))
        setSummary({ assessments: normalized.count, averageRating, followUps })
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
  }, [search, status])

  const enrollmentLookup = useMemo(() => {
    return enrollments.reduce((lookup, enrollment) => {
      const studentName = [enrollment.student_name, enrollment.student?.full_name]
        .filter(Boolean)
        .find(Boolean) || 'Student'
      lookup[enrollment.id] = studentName
      return lookup
    }, {})
  }, [enrollments])

  return (
    <div className="page-stack behavior-page">
      <PageHeader
        eyebrow="Behavior"
        title="Behavior monitoring"
        description="Review behavioral assessments and use the latest patterns to coordinate support and intervention planning."
        actions={canManageBehavior ? (
          <Link className="action-button" to="/behavior/encode">
            Encode behavior
          </Link>
        ) : null}
      />

      <section className="detail-card workflow-guide-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Workflow guidance</p>
            <h3>Turn behavior insight into action</h3>
          </div>
        </div>
        <ul className="workflow-guide-list">
          <li>Review recent evaluations to identify students who may need coordinated support.</li>
          <li>Use search to focus on a single student or indicator before sharing the results.</li>
          <li>Move to encoding when the latest assessment needs to be captured immediately.</li>
        </ul>
        <div className="workflow-guide-actions">
          <span className="action-chip">Behavior review</span>
          <span className="action-chip">Support planning</span>
        </div>
      </section>

      <div className="record-summary-grid monitoring-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Behavioral assessments</p>
          <p className="stat-value">{summary.assessments}</p>
          <span className="badge badge--info">Latest records</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Average rating</p>
          <p className="stat-value">{summary.averageRating}</p>
          <span className="badge badge--success">Numeric average</span>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Follow-up alerts</p>
          <p className="stat-value">{summary.followUps}</p>
          <span className={`badge ${summary.followUps ? 'badge--warning' : 'badge--success'}`}>
            {summary.followUps ? 'Needs review' : 'Stable'}
          </span>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Behavior assessments</p>
            <h2>Recent behavioral evaluations</h2>
          </div>
          <div className="section-actions">
            <label>
              <span className="sr-only">Behavior record status</span>
              <select aria-label="Behavior record status" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="active">Active</option>
                <option value="archived">Archived</option>
                <option value="all">All</option>
              </select>
            </label>
            <div className="search-input-group">
            <MagnifyingGlassIcon className="icon search-icon" aria-hidden="true" />
            <input
              aria-label="Search behavioral assessments"
              placeholder="Search by student or behavior indicator"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            </div>
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
                    <th scope="col">Student</th>
                    <th scope="col">Indicator</th>
                    <th scope="col">Rating</th>
                    <th scope="col">Date</th>
                    <th scope="col">Period</th>
                    <th scope="col">Status</th>
                    <th scope="col">Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {behavioralAssessments.map((assessment) => {
                    const ratingDisplay = assessment.rating_code || assessment.rating_label || assessment.rating || '—'
                    const numericScore = Number(assessment.numeric_score)
                    const isFollowUp = !Number.isNaN(numericScore) && numericScore < 3
                    const period = assessment.grading_period_type === 'Quarter'
                      ? `Quarter ${assessment.quarter ?? '—'}`
                      : assessment.grading_period_type === 'Semester'
                      ? `Semester ${assessment.semester ?? '—'}`
                      : assessment.grading_period_type || '—'
                    const studentName = assessment.student_name || enrollmentLookup[assessment.enrollment] || 'Enrollment unavailable'

                    return (
                      <tr key={assessment.id}>
                        <td data-label="Student">
                          <div className="monitoring-primary-cell">
                            <strong>{studentName}</strong>
                            <small>{assessment.academic_year_name || 'Historical context'}{assessment.section_name ? ` · ${assessment.section_name}` : ''}</small>
                          </div>
                        </td>
                        <td data-label="Indicator">{assessment.behavior_indicator_name || assessment.behavior_indicator || '—'}</td>
                        <td data-label="Rating">{ratingDisplay}</td>
                        <td data-label="Date">{assessment.assessment_date || '—'}</td>
                        <td data-label="Period">{period}</td>
                        <td data-label="Status">
                          <span className={`badge ${isFollowUp ? 'badge--warning' : 'badge--success'}`}>
                            {isFollowUp ? 'Follow-up' : 'Stable'}
                          </span>
                        </td>
                        <td data-label="Remarks">{assessment.remarks || 'No remarks recorded'}</td>
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

import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getTeacherContext } from '../../services/academicsService'
import { getAdviserDashboard } from '../../services/predictionService'

function valueOrFallback(value) {
  return value == null || value === '' ? 'N/A' : value
}

function riskClass(level) {
  const normalized = String(level || '').toLowerCase()
  if (normalized === 'high') return 'badge badge--high'
  if (normalized === 'moderate') return 'badge badge--warning'
  if (normalized === 'low') return 'badge badge--success'
  return 'badge badge--info'
}

export function MyAdvisoryClassPage() {
  const [sections, setSections] = useState([])
  const [selectedSection, setSelectedSection] = useState('')
  const [search, setSearch] = useState('')
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingSections, setLoadingSections] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getTeacherContext()
      .then((context) => {
        if (!active) return
        const advisorySections = context.advisory_classes || []
        setSections(advisorySections)
        setSelectedSection(advisorySections[0]?.section ? String(advisorySections[0].section) : '')
      })
      .catch((requestError) => {
        if (active) setError(getApiErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoadingSections(false)
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (loadingSections || !selectedSection) {
      return undefined
    }

    let active = true
    getAdviserDashboard({ section: selectedSection, search: search || undefined })
      .then((response) => {
        if (active) {
          setError('')
          setDashboard(response)
        }
      })
      .catch((requestError) => {
        if (active) setError(getApiErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [loadingSections, search, selectedSection])

  const students = dashboard?.students || []
  const summary = dashboard?.summary || {}
  const selected = sections.find((section) => String(section.section) === String(selectedSection))

  return (
    <div className="page-stack advisory-roster-page">
      <PageHeader eyebrow="Advisory responsibility" title="My Advisory Class" description="Monitor active students assigned to your advisory section." />
      {error ? <ErrorBanner message={error} /> : null}
      {loadingSections ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
      {!loadingSections && !sections.length ? <EmptyState title="No advisory class assigned" message="You do not have an active advisory section assigned to this account." /> : null}
      {!loadingSections && sections.length ? (
        <>
          <section className="panel-card record-panel advisory-roster-controls" aria-label="Advisory class selection and search">
            <div className="section-header"><div><p className="eyebrow">Authorized sections</p><h2>{selected?.section_name || 'Advisory section'}</h2></div><span className="badge badge--success">{summary.active_students ?? 0} active students</span></div>
            <div className="advisory-roster-toolbar">
              <label>Advisory section<select value={selectedSection} onChange={(event) => setSelectedSection(event.target.value)}>{sections.map((section) => <option key={section.section} value={section.section}>{section.grade_level_name} · {section.section_name} · {section.academic_year_name}</option>)}</select></label>
              <label className="advisory-search-field">Search students<div className="search-input-group"><MagnifyingGlassIcon className="icon" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name or LRN" /></div></label>
            </div>
            {selected ? <p className="support-copy">{selected.grade_level_name} · {selected.academic_year_name} · {selected.student_count} active students</p> : null}
          </section>
          <section className="panel-card record-panel" aria-labelledby="advisory-roster-title">
            <div className="section-header"><div><p className="eyebrow">Current roster</p><h2 id="advisory-roster-title">Students in this advisory class</h2></div><span className="badge badge--info">{students.length} shown</span></div>
            {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
            {!loading && !students.length ? <EmptyState title="No active students are currently enrolled" message={search ? 'No authorized students matched this search.' : 'No active students are currently enrolled in this advisory section.'} /> : null}
            {!loading && students.length ? <div className="table-card advisory-roster-table"><table><thead><tr><th>Student</th><th>Grade / section</th><th>Status</th><th>General average</th><th>Attendance</th><th>Behavior</th><th>Risk</th><th>Intervention</th><th>Action</th></tr></thead><tbody>{students.map((student) => <tr key={student.id}><td><Link to={`/students/${student.id}`}>{student.name}</Link><small>LRN: {valueOrFallback(student.lrn)}</small></td><td>{student.grade} · {student.section}</td><td>{student.enrollment_status}</td><td>{valueOrFallback(student.general_average)}</td><td>{student.attendance_percentage == null ? 'No record' : `${student.attendance_percentage}%`}<small>{student.school_days == null ? '' : `${student.days_present}/${student.school_days} days · ${student.times_tardy} tardy`}</small></td><td>{valueOrFallback(student.behavior_average)}<small>{student.behavior_records ? `${student.behavior_records} records` : 'No record'}</small></td><td>{student.risk_level ? <><span className={riskClass(student.risk_level)}>{student.risk_level}</span><small>{student.risk_probability == null ? 'Probability N/A' : `${Math.round(student.risk_probability * 100)}% probability`}</small></> : 'No prediction'}</td><td>{student.intervention ? student.intervention_statuses.join(', ') : 'No active intervention'}{student.follow_up ? <small>Follow-up due</small> : null}</td><td><Link className="action-button action-button--secondary" to={`/students/${student.id}`}>View Student</Link></td></tr>)}</tbody></table></div> : null}
          </section>
          <p className="support-copy">AI predictions are decision-support information and should be interpreted using professional judgment.</p>
        </>
      ) : null}
    </div>
  )
}

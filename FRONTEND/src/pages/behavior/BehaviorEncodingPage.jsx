import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useRoleAwareAutoLoad } from '../../hooks/useRoleAwareAutoLoad'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  bulkCreateBehavioralAssessments,
  getBehavioralAssessments,
  getBehavioralRatings,
  getBehaviorIndicators,
  getCoreValues,
} from '../../services/behaviorService'
import { getAcademicYears, getEnrollments, getGradeLevels, getSections, getTeacherContext } from '../../services/academicsService'
import { getStudentById } from '../../services/studentService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return Array.isArray(items) ? items : []
}

export function BehaviorEncodingPage() {
  const { user } = useAuth()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageBehavior = ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER'].includes(role)

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [teacherContext, setTeacherContext] = useState(null)
  const [coreValues, setCoreValues] = useState([])
  const [indicators, setIndicators] = useState([])
  const [ratings, setRatings] = useState([])
  const [selectedCoreValueId, setSelectedCoreValueId] = useState('')
  const [selectedIndicatorId, setSelectedIndicatorId] = useState('')
  const [filters, setFilters] = useState({
    academicYear: '',
    gradeLevel: '',
    section: '',
    gradingPeriod: 'Quarter',
    quarter: '1',
  })
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingClass, setLoadingClass] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')
      try {
        const context = role === 'TEACHER' ? await getTeacherContext() : null
        const referencesPromise = context
          ? Promise.resolve([
            [...new Map([...(context.advisory_classes || []), ...(context.subject_assignments || [])].map((item) => [item.academic_year, { id: item.academic_year, name: item.academic_year_name }])).values()],
            [...new Map([...(context.advisory_classes || []), ...(context.subject_assignments || [])].map((item) => [item.grade_level, { id: item.grade_level, name: item.grade_level_name }])).values()],
            [...new Map([...(context.advisory_classes || []), ...(context.subject_assignments || [])].map((item) => [item.section, { id: item.section, name: item.section_name, academic_year: item.academic_year, grade_level: item.grade_level }])).values()],
          ])
          : Promise.all([getAcademicYears(), getGradeLevels(), getSections()])
        const [[yearsData, levelsData, sectionsData], coreValuesData, indicatorsData, ratingsData] = await Promise.all([
          referencesPromise,
          getCoreValues({ is_active: true }),
          getBehaviorIndicators({ is_active: true }),
          getBehavioralRatings({ is_active: true }),
        ])
        if (!active) return
        setTeacherContext(context)
        setAcademicYears(normalizeListResponse(yearsData))
        setGradeLevels(normalizeListResponse(levelsData))
        setSections(normalizeListResponse(sectionsData))
        const nextCoreValues = normalizeListResponse(coreValuesData)
        const nextIndicators = normalizeListResponse(indicatorsData)
        setCoreValues(nextCoreValues)
        setIndicators(nextIndicators)
        setRatings(normalizeListResponse(ratingsData))
        const firstCoreValue = nextCoreValues[0]
        const firstIndicator = nextIndicators.find((indicator) => String(indicator.core_value) === String(firstCoreValue?.id))
        setSelectedCoreValueId(firstCoreValue ? String(firstCoreValue.id) : '')
        setSelectedIndicatorId(firstIndicator ? String(firstIndicator.id) : '')
      } catch (err) {
        if (active) setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadReferences()
    return () => { active = false }
  }, [role])

  const teacherClassOptions = useMemo(() => {
    if (!teacherContext) return []
    const options = new Map()
    const entries = [...(teacherContext.advisory_classes || []), ...(teacherContext.subject_assignments || [])]
    entries.forEach((entry) => {
      const key = `${entry.academic_year}-${entry.section}`
      const existing = options.get(key)
      const roles = new Set(existing?.roles || [])
      if (entry.role === 'Adviser' || entry.assignment_type === 'ADVISER') {
        roles.add('Adviser')
      }
      if (entry.assignment_type === 'SUBJECT' || entry.role === 'Subject Teacher') {
        roles.add('Subject Teacher')
      }
      options.set(key, { ...existing, ...entry, roles, role: [...roles].join(' and ') })
    })
    return [...options.values()]
  }, [teacherContext])

  const selectedAcademicYear = useMemo(() => academicYears.find((year) => String(year.id) === String(filters.academicYear)) || null, [academicYears, filters.academicYear])
  const selectedGradeLevel = useMemo(() => gradeLevels.find((level) => String(level.id) === String(filters.gradeLevel)) || null, [gradeLevels, filters.gradeLevel])
  const selectedSection = useMemo(() => sections.find((section) => String(section.id) === String(filters.section)) || null, [sections, filters.section])
  const selectedCoreValue = useMemo(() => coreValues.find((value) => String(value.id) === String(selectedCoreValueId)) || null, [coreValues, selectedCoreValueId])
  const selectedIndicator = useMemo(() => indicators.find((indicator) => String(indicator.id) === String(selectedIndicatorId)) || null, [indicators, selectedIndicatorId])
  const coreValueIndicators = useMemo(() => indicators.filter((indicator) => String(indicator.core_value) === String(selectedCoreValueId)), [indicators, selectedCoreValueId])
  const filteredSections = useMemo(() => sections.filter((section) => {
    const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
    const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
    return matchesYear && matchesLevel
  }), [filters.academicYear, filters.gradeLevel, sections])
  const canEdit = canManageBehavior && selectedAcademicYear?.is_active !== false

  function getDefaultBehaviorFilters() {
    const assignment = teacherClassOptions[0] || sections[0]
    if (!assignment) return null
    return {
      academicYear: String(assignment.academic_year),
      gradeLevel: String(assignment.grade_level),
      section: String(assignment.section || assignment.id),
      gradingPeriod: filters.gradingPeriod,
      quarter: filters.quarter,
    }
  }

  async function loadClassData(nextFilters = filters) {
    if (!nextFilters.academicYear || !nextFilters.gradeLevel || !nextFilters.section) {
      setError('Select an academic year, grade level, and section before loading the behavior roster.')
      return
    }
    setLoadingClass(true)
    setError('')
    setSuccessMessage('')
    try {
      const [enrollmentsData, assessmentsData] = await Promise.all([
        getEnrollments({ academic_year: nextFilters.academicYear, grade_level: nextFilters.gradeLevel, section: nextFilters.section, enrollment_status: 'active' }),
        getBehavioralAssessments({
          academic_year: nextFilters.academicYear,
          grading_period_type: nextFilters.gradingPeriod,
          quarter: nextFilters.gradingPeriod === 'Quarter' ? nextFilters.quarter : undefined,
          semester: nextFilters.gradingPeriod === 'Semester' ? nextFilters.quarter : undefined,
        }),
      ])
      const enrollments = normalizeListResponse(enrollmentsData)
      const assessments = normalizeListResponse(assessmentsData)
      const assessmentMap = assessments.reduce((map, assessment) => {
        map[`${assessment.enrollment}:${assessment.behavior_indicator}`] = assessment
        return map
      }, {})
      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      const studentMap = studentProfiles.reduce((map, student) => {
        if (student?.id) map[student.id] = student
        return map
      }, {})
      setRows(enrollments.map((enrollment) => {
        const student = studentMap[enrollment.student]
        const assessmentsByIndicator = indicators.reduce((map, indicator) => {
          const assessment = assessmentMap[`${enrollment.id}:${indicator.id}`]
          map[indicator.id] = {
            assessmentId: assessment?.id || null,
            ratingId: assessment?.rating || '',
            remarks: assessment?.remarks || '',
          }
          return map
        }, {})
        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          assessments: assessmentsByIndicator,
        }
      }))
    } catch (err) {
      setError(getApiErrorMessage(err))
      setRows([])
    } finally {
      setLoadingClass(false)
    }
  }

  useRoleAwareAutoLoad({
    enabled: canManageBehavior,
    loading,
    filters,
    setFilters,
    getDefaultFilters: getDefaultBehaviorFilters,
    onLoad: loadClassData,
    dependencies: [academicYears.length, gradeLevels.length, sections.length, indicators.length],
  })

  function selectTeacherClass(value) {
    const assignment = teacherClassOptions.find((entry) => `${entry.academic_year}-${entry.section}` === value)
    if (!assignment) return
    const nextFilters = { ...filters, academicYear: String(assignment.academic_year), gradeLevel: String(assignment.grade_level), section: String(assignment.section) }
    setFilters(nextFilters)
    loadClassData(nextFilters)
  }

  function selectCoreValue(value) {
    setSelectedCoreValueId(value)
    const firstIndicator = indicators.find((indicator) => String(indicator.core_value) === String(value))
    setSelectedIndicatorId(firstIndicator ? String(firstIndicator.id) : '')
  }

  function updateRowRating(rowId, value) {
    setRows((currentRows) => currentRows.map((row) => row.id !== rowId ? row : {
      ...row,
      assessments: {
        ...row.assessments,
        [selectedIndicatorId]: {
          ...row.assessments[selectedIndicatorId],
          ratingId: value,
        },
      },
    }))
  }

  async function handleSave(shouldFinalize) {
    if (!canEdit) {
      setError(selectedAcademicYear?.is_active === false ? 'Archived Academic Year - Read Only' : 'You do not have permission to encode behavior for this class.')
      return
    }
    if (!selectedIndicator) {
      setError('Select a Core Value and behavior statement before saving.')
      return
    }
    const payload = rows.map((row) => {
      const selection = row.assessments[selectedIndicator.id]
      if (!selection?.ratingId) return null
      return {
        id: selection.assessmentId || undefined,
        enrollment: row.enrollmentId,
        academic_year: Number(filters.academicYear),
        grading_period_type: filters.gradingPeriod,
        quarter: filters.gradingPeriod === 'Quarter' ? Number(filters.quarter) : null,
        semester: filters.gradingPeriod === 'Semester' ? Number(filters.quarter) : null,
        core_value: selectedIndicator.core_value,
        behavior_indicator: Number(selectedIndicator.id),
        rating: Number(selection.ratingId),
        assessment_date: new Date().toISOString().slice(0, 10),
        remarks: shouldFinalize ? 'Finalized' : '',
      }
    }).filter(Boolean)
    if (!payload.length) {
      setError('Select at least one rating before saving.')
      return
    }
    setError('')
    setSuccessMessage('')
    try {
      await bulkCreateBehavioralAssessments(payload)
      await loadClassData(filters)
      setSuccessMessage(shouldFinalize ? 'Behavior evaluation finalized successfully.' : 'Behavior evaluation saved successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  if (loading) return <LoadingSpinner label="Loading behavior workspace..." />

  return (
    <div className="page-stack behavior-encoding-page">
      <PageHeader
        eyebrow="Behavior workflow"
        title="Behavior encoding"
        description="Assess the DepEd Core Values for an authorized class using the source behavior statements and observed-value ratings."
        actions={<Link className="action-button action-button--secondary" to="/behavior">Back to behavior</Link>}
      />
      {!canManageBehavior ? <div className="status-banner status-banner--warning">You do not currently have permission to encode behavior.</div> : null}
      <section className="students-panel behavior-encoding-panel">
        <div className="form-section-card">
          <div className="gradebook-context-header">
            <div className="gradebook-context-title-block">
              <p className="eyebrow">DepEd observed values</p>
              <h2>{selectedGradeLevel?.name || 'Class'}{selectedSection ? ` - ${selectedSection.name}` : ''}</h2>
              <p>{selectedCoreValue?.name || 'Select a Core Value'}{selectedIndicator ? ` · ${selectedIndicator.name}` : ''}</p>
            </div>
            <div className="gradebook-context-metrics">
              <span>Academic Year: {selectedAcademicYear?.name || '—'}</span>
              <span>Grade Level: {selectedGradeLevel?.name || '—'}</span>
              <span>Section: {selectedSection?.name || '—'}</span>
              <span>Evaluation: {filters.gradingPeriod} {filters.quarter}</span>
            </div>
          </div>
          <div className="form-grid">
            {role === 'TEACHER' ? (
              <label className="form-grid-full">
                <span>Authorized class</span>
                <select value={filters.academicYear && filters.section ? `${filters.academicYear}-${filters.section}` : ''} onChange={(event) => selectTeacherClass(event.target.value)}>
                  <option value="">Select an authorized class</option>
                  {teacherClassOptions.map((assignment) => <option key={`${assignment.academic_year}-${assignment.section}`} value={`${assignment.academic_year}-${assignment.section}`}>{assignment.grade_level_name} · {assignment.section_name} · {assignment.role}</option>)}
                </select>
              </label>
            ) : null}
            {role !== 'TEACHER' ? (
              <>
                <label><span>Academic year</span><select value={filters.academicYear} onChange={(event) => setFilters({ ...filters, academicYear: event.target.value })}><option value="">Select academic year</option>{academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}</select></label>
                <label><span>Grade level</span><select value={filters.gradeLevel} onChange={(event) => setFilters({ ...filters, gradeLevel: event.target.value })}><option value="">Select grade level</option>{gradeLevels.map((level) => <option key={level.id} value={level.id}>{level.name}</option>)}</select></label>
                <label><span>Section</span><select value={filters.section} onChange={(event) => setFilters({ ...filters, section: event.target.value })}><option value="">Select section</option>{filteredSections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}</select></label>
              </>
            ) : null}
            <label><span>Core Value</span><select value={selectedCoreValueId} onChange={(event) => selectCoreValue(event.target.value)}><option value="">Select Core Value</option>{coreValues.map((coreValue) => <option key={coreValue.id} value={coreValue.id}>{coreValue.name}</option>)}</select></label>
            <label className="form-grid-full"><span>Behavior Statement</span><select value={selectedIndicatorId} onChange={(event) => setSelectedIndicatorId(event.target.value)}><option value="">Select behavior statement</option>{coreValueIndicators.map((indicator) => <option key={indicator.id} value={indicator.id}>{indicator.name}</option>)}</select></label>
            <label><span>Evaluation period</span><select value={filters.gradingPeriod} onChange={(event) => setFilters({ ...filters, gradingPeriod: event.target.value })}><option value="Quarter">Quarter</option><option value="Semester">Semester</option></select></label>
            <label><span>{filters.gradingPeriod === 'Quarter' ? 'Quarter' : 'Semester'}</span><select value={filters.quarter} onChange={(event) => setFilters({ ...filters, quarter: event.target.value })}>{(filters.gradingPeriod === 'Quarter' ? [1, 2, 3, 4] : [1, 2]).map((period) => <option key={period} value={period}>{period}</option>)}</select></label>
          </div>
          <div className="grade-encoding-actions"><button type="button" className="action-button" onClick={() => loadClassData()} disabled={loadingClass}>{loadingClass ? 'Loading roster...' : 'Load class roster'}</button>{selectedAcademicYear?.is_active === false ? <span className="status-banner status-banner--warning">Archived Academic Year - Read Only</span> : null}</div>
        </div>
        {error ? <ErrorBanner message={error} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}
        {!rows.length ? <EmptyState title="Ready for behavior entry" message="Select a class, Core Value, and behavior statement to load the roster." /> : null}
        {rows.length > 0 ? (
          <div className="table-card grade-encoding-table-wrapper">
            <table className="encoding-table" aria-label="Behavior encoding table">
              <thead><tr><th scope="col">Student ID</th><th scope="col">Student name</th><th scope="col">{selectedCoreValue?.name || 'Core Value'} / {selectedIndicator?.name || 'Behavior Statement'}</th><th scope="col">Status</th></tr></thead>
              <tbody>{rows.map((row) => { const selection = row.assessments[selectedIndicatorId] || {}; return <tr key={row.id}><td data-label="Student ID">{row.studentId}</td><td data-label="Student name">{row.studentName}</td><td data-label="Rating"><label className="sr-only" htmlFor={`behavior-rating-${row.id}`}>Rating for {row.studentName}</label><select id={`behavior-rating-${row.id}`} value={selection.ratingId || ''} onChange={(event) => updateRowRating(row.id, event.target.value)} disabled={!canEdit}><option value="">Select rating</option>{ratings.map((rating) => <option key={rating.id} value={rating.id}>{rating.code} - {rating.label}</option>)}</select></td><td data-label="Status">{selection.ratingId ? 'Rated' : 'Pending'}</td></tr> })}</tbody>
            </table>
          </div>
        ) : null}
        {rows.length > 0 && canEdit ? <div className="grade-encoding-actions"><button type="button" className="action-button" onClick={() => handleSave(false)}>Save assessments</button><button type="button" className="action-button action-button--secondary" onClick={() => handleSave(true)}>Finalize assessments</button></div> : null}
      </section>
    </div>
  )
}

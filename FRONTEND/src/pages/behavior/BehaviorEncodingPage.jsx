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
  createBehavioralAssessment,
  getBehavioralAssessments,
  getBehavioralRatings,
  getBehaviorIndicators,
  updateBehavioralAssessment,
} from '../../services/behaviorService'
import { getAcademicYears, getEnrollments, getGradeLevels, getSections } from '../../services/academicsService'
import { getStudentById } from '../../services/studentService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return {
    items,
    count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0,
    next: data?.next || null,
    previous: data?.previous || null,
  }
}

const CLASSIFICATION_RULES = [
  { minimum: 4.5, label: 'Outstanding' },
  { minimum: 4.0, label: 'Very Good' },
  { minimum: 3.0, label: 'Good' },
  { minimum: 2.0, label: 'Needs Improvement' },
  { minimum: 0, label: 'At Risk' },
]

function getClassification(average) {
  const numericAverage = Number(average)
  if (Number.isNaN(numericAverage)) {
    return 'Pending'
  }

  return CLASSIFICATION_RULES.find((rule) => numericAverage >= rule.minimum)?.label || 'At Risk'
}

function getAverageValue(values) {
  const numericValues = values.filter((value) => typeof value === 'number' && !Number.isNaN(value))
  if (!numericValues.length) {
    return ''
  }
  return (numericValues.reduce((sum, value) => sum + value, 0) / numericValues.length).toFixed(2)
}

export function BehaviorEncodingPage() {
  const { user } = useAuth()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageBehavior = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN' || role === 'TEACHER'

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [indicators, setIndicators] = useState([])
  const [ratings, setRatings] = useState([])

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
        const [yearsData, levelsData, sectionsData, indicatorsData, ratingsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getBehaviorIndicators({ is_active: true }),
          getBehavioralRatings({ is_active: true }),
        ])

        if (!active) {
          return
        }

        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(levelsData).items)
        setSections(normalizeListResponse(sectionsData).items)
        setIndicators(normalizeListResponse(indicatorsData).items)
        setRatings(normalizeListResponse(ratingsData).items)
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

    loadReferences()
    return () => {
      active = false
    }
  }, [])

  const getDefaultBehaviorFilters = () => {
    const defaultSection = sections[0]
    if (!defaultSection) {
      return null
    }

    return {
      academicYear: String(defaultSection.academic_year),
      gradeLevel: String(defaultSection.grade_level),
      section: String(defaultSection.id),
      gradingPeriod: filters.gradingPeriod,
      quarter: filters.quarter,
    }
  }

  useRoleAwareAutoLoad({
    enabled: canManageBehavior,
    loading,
    filters,
    setFilters,
    getDefaultFilters: getDefaultBehaviorFilters,
    onLoad: loadClassData,
    dependencies: [academicYears.length, gradeLevels.length, sections.length, filters.gradingPeriod, filters.quarter],
  })

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
      const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
      return matchesYear && matchesLevel
    })
  }, [filters.academicYear, filters.gradeLevel, sections])

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
          semester: nextFilters.gradingPeriod === 'Semester' ? 1 : undefined,
        }),
      ])

      const enrollments = normalizeListResponse(enrollmentsData).items
      const assessments = normalizeListResponse(assessmentsData).items

      const assessmentMap = assessments.reduce((accumulator, assessment) => {
        const key = `${assessment.enrollment}:${assessment.behavior_indicator}`
        accumulator[key] = assessment
        return accumulator
      }, {})

      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      const studentMap = studentProfiles.reduce((accumulator, student) => {
        accumulator[student.id] = student
        return accumulator
      }, {})

      const classRows = enrollments.map((enrollment) => {
        const student = studentMap[enrollment.student]
        const assessmentsByIndicator = indicators.reduce((accumulator, indicator) => {
          const assessment = assessmentMap[`${enrollment.id}:${indicator.id}`]
          const rating = assessment?.rating ? ratings.find((entry) => entry.id === assessment.rating) || null : null
          accumulator[indicator.id] = {
            assessmentId: assessment?.id || null,
            ratingId: assessment?.rating || '',
            numericScore: assessment?.numeric_score != null ? Number(assessment.numeric_score) : '',
            ratingCode: rating?.code || '',
            ratingLabel: rating?.label || '',
            remarks: assessment?.remarks || '',
          }
          return accumulator
        }, {})

        const numericScores = Object.values(assessmentsByIndicator)
          .map((selection) => (selection.numericScore === '' ? null : Number(selection.numericScore)))
          .filter((value) => value !== null && !Number.isNaN(value))

        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          assessments: assessmentsByIndicator,
          average: numericScores.length ? getAverageValue(numericScores) : '',
          classification: numericScores.length ? getClassification(getAverageValue(numericScores)) : 'Pending',
          status: numericScores.length ? 'Loaded' : 'Pending',
        }
      })

      setRows(classRows)
    } catch (err) {
      setError(getApiErrorMessage(err))
      setRows([])
    } finally {
      setLoadingClass(false)
    }
  }

  function updateRowIndicator(rowId, indicatorId, value) {
    const selectedRating = ratings.find((entry) => String(entry.id) === String(value)) || null

    setRows((currentRows) => currentRows.map((row) => {
      if (row.id !== rowId) {
        return row
      }

      const nextAssessments = {
        ...row.assessments,
        [indicatorId]: {
          ...row.assessments[indicatorId],
          ratingId: value,
          numericScore: selectedRating?.numeric_value != null ? Number(selectedRating.numeric_value) : '',
          ratingCode: selectedRating?.code || '',
          ratingLabel: selectedRating?.label || '',
          remarks: row.assessments[indicatorId]?.remarks || '',
        },
      }

      const numericScores = Object.values(nextAssessments)
        .map((selection) => (selection.numericScore === '' ? null : Number(selection.numericScore)))
        .filter((value) => value !== null && !Number.isNaN(value))

      return {
        ...row,
        assessments: nextAssessments,
        average: numericScores.length ? getAverageValue(numericScores) : '',
        classification: numericScores.length ? getClassification(getAverageValue(numericScores)) : 'Pending',
        status: 'Draft',
      }
    }))
  }

  async function handleSave(shouldFinalize) {
    if (!canManageBehavior) {
      setError('You do not have permission to encode behavior for this class.')
      return
    }

    setError('')
    setSuccessMessage('')

    try {
      for (const row of rows) {
        const indicatorEntries = Object.entries(row.assessments)

        for (const [indicatorId, selection] of indicatorEntries) {
          if (!selection.ratingId) {
            continue
          }

          const payload = {
            enrollment: row.enrollmentId,
            academic_year: Number(filters.academicYear),
            grading_period_type: filters.gradingPeriod,
            quarter: filters.gradingPeriod === 'Quarter' ? Number(filters.quarter) : null,
            semester: filters.gradingPeriod === 'Semester' ? 1 : null,
            core_value: indicators.find((indicator) => String(indicator.id) === String(indicatorId))?.core_value || null,
            behavior_indicator: Number(indicatorId),
            rating: Number(selection.ratingId),
            numeric_score: selection.numericScore,
            assessment_date: new Date().toISOString().slice(0, 10),
            remarks: shouldFinalize ? `${selection.remarks || ''} Finalized`.trim() : selection.remarks || '',
          }

          if (selection.assessmentId) {
            await updateBehavioralAssessment(selection.assessmentId, payload)
          } else {
            await createBehavioralAssessment(payload)
          }
        }
      }

      setSuccessMessage(shouldFinalize ? 'Behavior evaluation finalized successfully.' : 'Behavior evaluation saved as draft successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading behavior workspace..." />
  }

  return (
    <div className="page-stack behavior-encoding-page">
      <PageHeader
        eyebrow="Behavior workflow"
        title="Behavior encoding"
        description="Open the assigned class, rate each student’s indicators, and save the evaluation in a single guided workflow."
        actions={(
          <Link className="action-button action-button--secondary" to="/behavior">
            Back to behavior
          </Link>
        )}
      />

      {!canManageBehavior ? (
        <div className="status-banner status-banner--warning">You do not currently have permission to encode behavior.</div>
      ) : null}

      <section className="students-panel behavior-encoding-panel">
        <div className="form-section-card">
          <div className="workflow-step">Choose the class and grading period.</div>
          <div className="workflow-step">Rate the indicators for each student.</div>
          <div className="workflow-step">Save the draft or finalize the evaluation.</div>
          <div className="form-grid">
            <label>
              <span>Academic year</span>
              <select value={filters.academicYear} onChange={(event) => setFilters({ ...filters, academicYear: event.target.value })}>
                <option value="">Select academic year</option>
                {academicYears.map((year) => (
                  <option key={year.id} value={year.id}>{year.name}</option>
                ))}
              </select>
            </label>

            <label>
              <span>Grade level</span>
              <select value={filters.gradeLevel} onChange={(event) => setFilters({ ...filters, gradeLevel: event.target.value })}>
                <option value="">Select grade level</option>
                {gradeLevels.map((gradeLevel) => (
                  <option key={gradeLevel.id} value={gradeLevel.id}>{gradeLevel.name}</option>
                ))}
              </select>
            </label>

            <label>
              <span>Section</span>
              <select value={filters.section} onChange={(event) => setFilters({ ...filters, section: event.target.value })}>
                <option value="">Select section</option>
                {filteredSections.map((section) => (
                  <option key={section.id} value={section.id}>{section.name}</option>
                ))}
              </select>
            </label>

            <label>
              <span>Evaluation period</span>
              <select value={filters.gradingPeriod} onChange={(event) => setFilters({ ...filters, gradingPeriod: event.target.value })}>
                <option value="Quarter">Quarter</option>
                <option value="Semester">Semester</option>
              </select>
            </label>

            <label>
              <span>{filters.gradingPeriod === 'Quarter' ? 'Quarter' : 'Semester'}</span>
              <select value={filters.quarter} onChange={(event) => setFilters({ ...filters, quarter: event.target.value })}>
                {filters.gradingPeriod === 'Quarter' ? (
                  [1, 2, 3, 4].map((quarter) => <option key={quarter} value={quarter}>{quarter}</option>)
                ) : (
                  [1, 2].map((semester) => <option key={semester} value={semester}>{semester}</option>)
                )}
              </select>
            </label>
          </div>

          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={loadClassData} disabled={loadingClass}>
              {loadingClass ? 'Loading...' : 'Load class roster'}
            </button>
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}

        {rows.length === 0 ? (
          <EmptyState title="Ready for behavior entry" message="Load a class roster to begin encoding behavior indicators for the selected evaluation period." />
        ) : null}

        {rows.length > 0 ? (
          <div className="table-card grade-encoding-table-wrapper">
            <table className="encoding-table" aria-label="Behavior encoding table">
              <thead>
                <tr>
                  <th scope="col">Student ID</th>
                  <th scope="col">Student name</th>
                  {indicators.map((indicator) => (
                    <th key={indicator.id} scope="col">{indicator.name}</th>
                  ))}
                  <th scope="col">Behavior average</th>
                  <th scope="col">Classification</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td data-label="Student ID">{row.studentId}</td>
                    <td data-label="Student name">{row.studentName}</td>
                    {indicators.map((indicator) => (
                      <td key={indicator.id} data-label={indicator.name}>
                        <label className="sr-only" htmlFor={`indicator-${row.id}-${indicator.id}`}>
                          {`${indicator.name} for ${row.studentName}`}
                        </label>
                        <select
                          id={`indicator-${row.id}-${indicator.id}`}
                          value={row.assessments[indicator.id]?.ratingId || ''}
                          onChange={(event) => updateRowIndicator(row.id, indicator.id, event.target.value)}
                          aria-label={`${indicator.name} for ${row.studentName}`}
                        >
                          <option value="">Select rating</option>
                          {ratings.map((rating) => (
                            <option key={rating.id} value={rating.id}>{rating.code} - {rating.label}</option>
                          ))}
                        </select>
                      </td>
                    ))}
                    <td data-label="Behavior average">{row.average || '—'}</td>
                    <td data-label="Classification">{row.classification}</td>
                    <td data-label="Status">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {rows.length > 0 ? (
          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={() => handleSave(false)}>Save draft</button>
            <button type="button" className="action-button action-button--secondary" onClick={() => handleSave(true)}>Finalize evaluation</button>
          </div>
        ) : null}
      </section>
    </div>
  )
}

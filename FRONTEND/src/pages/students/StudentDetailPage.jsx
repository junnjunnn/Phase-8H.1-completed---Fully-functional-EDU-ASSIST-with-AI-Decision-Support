import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { InterventionFormModal } from '../../components/interventions/InterventionFormModal'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import { generatePrediction } from '../../services/predictionService'
import { getStudentById } from '../../services/studentService'
import {
  getStudentRelatedAcademicRecords,
  getStudentRelatedAttendanceRecords,
  getStudentRelatedBehavioralAssessments,
  getStudentRelatedInterventions,
  getStudentRelatedRiskPredictions,
  getStudentRelatedPredictionFactors,
  getStudentEnrollments,
} from '../../services/studentDetailService'

function safeText(value) {
  return value || 'Not available'
}

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return {
    items,
    count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0,
    next: data?.next || null,
    previous: data?.previous || null,
  }
}

async function getAllStudentAttendanceRecords(studentId, params) {
  const recordsById = new Map()
  let page = 1
  let normalized
  let count = 0

  do {
    normalized = normalizeListResponse(
      await getStudentRelatedAttendanceRecords(studentId, { ...params, page }),
    )
    count = normalized.count
    normalized.items.forEach((record) => {
      if (record?.id != null) recordsById.set(String(record.id), record)
    })
    page += 1
  } while (normalized.next)

  return { records: [...recordsById.values()], count }
}

function formatProbability(probability) {
  if (probability == null) {
    return 'Not available'
  }
  return `${Math.round(probability * 100)}%`
}

function riskBadgeClass(riskLevel) {
  if (riskLevel === 'High') {
    return 'badge risk-badge high'
  }
  if (riskLevel === 'Moderate') {
    return 'badge risk-badge moderate'
  }
  return 'badge risk-badge low'
}

function formatFactorContribution(value) {
  const contribution = Number(value)
  if (Number.isNaN(contribution)) {
    return 'Not available'
  }
  const prefix = contribution > 0 ? '+' : ''
  return `${prefix}${contribution.toFixed(2)}`
}

export function StudentDetailPage() {
  const { id } = useParams()

  const [student, setStudent] = useState(null)
  const [studentError, setStudentError] = useState('')
  const [studentLoading, setStudentLoading] = useState(true)

  const [enrollments, setEnrollments] = useState([])

  const [academicRecords, setAcademicRecords] = useState([])
  const [academicError, setAcademicError] = useState('')
  const [academicLoading, setAcademicLoading] = useState(true)

  const [attendanceRecords, setAttendanceRecords] = useState([])
  const [attendanceError, setAttendanceError] = useState('')
  const [attendanceLoading, setAttendanceLoading] = useState(true)

  const [behaviorRecords, setBehaviorRecords] = useState([])
  const [behaviorError, setBehaviorError] = useState('')
  const [behaviorLoading, setBehaviorLoading] = useState(true)

  const [interventions, setInterventions] = useState([])
  const [interventionError, setInterventionError] = useState('')
  const [interventionLoading, setInterventionLoading] = useState(true)

  const { user } = useAuth()
  const [predictions, setPredictions] = useState([])
  const [predictionError, setPredictionError] = useState('')
  const [predictionLoading, setPredictionLoading] = useState(true)
  const [generatingPrediction, setGeneratingPrediction] = useState(false)
  const [generationMessage, setGenerationMessage] = useState('')

  const [predictionFactors, setPredictionFactors] = useState([])
  const [predictionFactorError, setPredictionFactorError] = useState('')
  const [predictionFactorLoading, setPredictionFactorLoading] = useState(true)

  const [showInterventionModal, setShowInterventionModal] = useState(false)
  const [selectedIntervention, setSelectedIntervention] = useState(null)

  const [activeTab, setActiveTab] = useState('overview')
  const [academicPeriod, setAcademicPeriod] = useState('')

  const [studentSummary, setStudentSummary] = useState({
    academicCount: 0,
    attendanceCount: 0,
    behaviorCount: 0,
    interventionCount: 0,
    predictionCount: 0,
    predictionFactorCount: 0,
  })

  useEffect(() => {
    let active = true

    async function loadStudentProfile() {
      setStudentLoading(true)
      setStudentError('')

      try {
        const [studentData, enrollmentData] = await Promise.all([
          getStudentById(id),
          getStudentEnrollments(id, { ordering: '-enrollment_date' }),
        ])

        if (!active) {
          return
        }

        setStudent(studentData)
        setEnrollments(normalizeListResponse(enrollmentData).items)
      } catch (err) {
        if (!active) {
          return
        }
        const message = getApiErrorMessage(err)
        setStudentError(message)
      } finally {
        if (active) {
          setStudentLoading(false)
        }
      }
    }

    loadStudentProfile()
    return () => {
      active = false
    }
  }, [id])

  useEffect(() => {
    let active = true

    async function loadStudentRecords() {
      setAcademicLoading(true)
      setAttendanceLoading(true)
      setBehaviorLoading(true)
      setInterventionLoading(true)
      setPredictionLoading(true)
      setPredictionFactorLoading(true)

      setAcademicError('')
      setAttendanceError('')
      setBehaviorError('')
      setInterventionError('')
      setPredictionError('')
      setPredictionFactorError('')

      try {
        const [periodType, periodNumber] = academicPeriod ? academicPeriod.split(':') : ['', '']
        const academicParams = {
          ordering: '-created_at',
          ...(periodType ? {
            grading_period_type: periodType,
            ...(periodType === 'Quarter' ? { quarter: periodNumber } : { semester: periodNumber }),
          } : {}),
        }
        const [academicData, attendanceResult, behaviorData, interventionData, predictionData, predictionFactorData] = await Promise.all([
          getStudentRelatedAcademicRecords(id, academicParams),
          getAllStudentAttendanceRecords(id, { ordering: '-created_at' }),
          getStudentRelatedBehavioralAssessments(id, { ordering: '-assessment_date' }),
          getStudentRelatedInterventions(id, { ordering: '-created_at' }),
          getStudentRelatedRiskPredictions(id, { ordering: '-prediction_date' }),
          getStudentRelatedPredictionFactors(id, { ordering: 'feature_name' }),
        ])

        if (!active) {
          return
        }

        const normalizedAcademic = normalizeListResponse(academicData)
        const normalizedBehavior = normalizeListResponse(behaviorData)
        const normalizedInterventions = normalizeListResponse(interventionData)
        const normalizedPredictions = normalizeListResponse(predictionData)
        const normalizedPredictionFactors = normalizeListResponse(predictionFactorData)

        setAcademicRecords(normalizedAcademic.items)
        setAttendanceRecords(attendanceResult.records)
        setBehaviorRecords(normalizedBehavior.items)
        setInterventions(normalizedInterventions.items)
        setPredictions(normalizedPredictions.items)
        setPredictionFactors(normalizedPredictionFactors.items)

        setStudentSummary({
          academicCount: normalizedAcademic.count,
          attendanceCount: attendanceResult.count,
          behaviorCount: normalizedBehavior.count,
          interventionCount: normalizedInterventions.count,
          predictionCount: normalizedPredictions.count,
          predictionFactorCount: normalizedPredictionFactors.count,
        })
      } catch (err) {
        if (!active) {
          return
        }
        const message = getApiErrorMessage(err)
        setAcademicError(message)
        setAttendanceError(message)
        setBehaviorError(message)
        setInterventionError(message)
        setPredictionError(message)
        setPredictionFactorError(message)
      } finally {
        if (active) {
          setAcademicLoading(false)
          setAttendanceLoading(false)
          setBehaviorLoading(false)
          setInterventionLoading(false)
          setPredictionLoading(false)
          setPredictionFactorLoading(false)
        }
      }
    }

    loadStudentRecords()
    return () => {
      active = false
    }
  }, [academicPeriod, id])

  const latestPrediction = useMemo(() => {
    if (!predictions.length) {
      return null
    }
    return predictions[0]
  }, [predictions])

  const latestPredictionFactors = useMemo(() => {
    if (!latestPrediction || predictionFactors.length === 0) {
      return []
    }
    return predictionFactors.filter((factor) => factor.prediction === latestPrediction.id)
  }, [latestPrediction, predictionFactors])

  const latestPredictionDrivers = useMemo(() => {
    return latestPredictionFactors
      .map((factor) => ({
        ...factor,
        numericContribution: Number(factor.contribution),
      }))
      .filter((factor) => !Number.isNaN(factor.numericContribution))
      .sort((a, b) => Math.abs(b.numericContribution) - Math.abs(a.numericContribution))
      .slice(0, 4)
  }, [latestPredictionFactors])

  const predictionTimeline = useMemo(() => predictions.slice(0, 6), [predictions])

  async function refreshStudentRecords() {
    setInterventionLoading(true)
    setInterventionError('')

    try {
      const interventionData = await getStudentRelatedInterventions(id, { ordering: '-created_at' })
      const normalizedInterventions = normalizeListResponse(interventionData)
      setInterventions(normalizedInterventions.items)
      setStudentSummary((current) => ({ ...current, interventionCount: normalizedInterventions.count }))
    } catch (err) {
      setInterventionError(getApiErrorMessage(err))
    } finally {
      setInterventionLoading(false)
    }
  }

  const academicSummary = useMemo(() => {
    const grades = academicRecords
      .map((record) => Number(record.final_grade))
      .filter((value) => !Number.isNaN(value))
    const failedSubjects = new Set(
      academicRecords
        .filter((record) => record.final_grade != null && Number(record.final_grade) < 75)
        .map((record) => record.subject_name || record.subject)
        .filter(Boolean),
    )

    return {
      generalAverage: grades.length ? (grades.reduce((sum, grade) => sum + grade, 0) / grades.length).toFixed(2) : null,
      failedSubjects: failedSubjects.size,
      lowestGrade: grades.length ? Math.min(...grades).toFixed(2) : null,
    }
  }, [academicRecords])

  const academicConcern = useMemo(() => {
    if (academicSummary.generalAverage == null) {
      return false
    }
    return Number(academicSummary.generalAverage) < 75
  }, [academicSummary.generalAverage])

  const aiRiskStatus = useMemo(() => {
    if (!latestPrediction) {
      return 'No prediction available'
    }
    return latestPrediction.risk_level === 'High' ? 'AT RISK' : 'NOT AT RISK'
  }, [latestPrediction])

  const riskGuidance = useMemo(() => {
    if (!latestPrediction) {
      return {
        title: 'No prediction available',
        items: [
          'Generate a risk prediction to review the current model-based estimate for this student.',
          'The estimate is only advisory and should be checked against the student’s actual academic, attendance, and behavior records.',
        ],
      }
    }

    if (latestPrediction.risk_level === 'High') {
      return {
        title: 'AI Risk Prediction: AT RISK',
        items: [
          'This means the model found patterns in the student’s current records that are associated with higher risk.',
          'Use the top contributing factors below to focus your review on the strongest signals before making a formal support decision.',
          'This is an AI-generated risk estimate, not a diagnosis. Teacher judgment and the live academic record remain the deciding evidence.',
        ],
      }
    }

    return {
      title: 'AI Risk Prediction: NOT AT RISK',
      items: [
        'This means the model did not find a high-risk pattern in the student’s current records.',
        'Maintain ongoing monitoring and continue reviewing the student’s actual grades, attendance, and engagement data.',
        'Use the prediction as decision support, not as a guarantee that no intervention is needed.',
      ],
    }
  }, [latestPrediction])

  const behaviorAverage = useMemo(() => {
    if (!behaviorRecords.length) {
      return null
    }

    const numericScores = behaviorRecords
      .map((record) => Number(record.numeric_score))
      .filter((value) => !Number.isNaN(value))

    if (!numericScores.length) {
      return null
    }

    return (numericScores.reduce((sum, value) => sum + value, 0) / numericScores.length).toFixed(2)
  }, [behaviorRecords])

  const attendanceSummary = useMemo(() => {
    if (!attendanceRecords.length) {
      return { schoolDays: null, daysPresent: null, absences: null, excusedAbsences: null, unclassifiedExcusedRecords: 0, timesTardy: null, percentage: null, mixedGranularityEnrollmentCount: 0 }
    }

    const granularityByEnrollment = attendanceRecords.reduce((result, record) => {
      const enrollmentId = String(record.enrollment)
      const granularity = result[enrollmentId] || { dated: false, period: false }
      if (record.attendance_date) granularity.dated = true
      else granularity.period = true
      result[enrollmentId] = granularity
      return result
    }, {})
    const mixedEnrollmentIds = new Set(
      Object.entries(granularityByEnrollment)
        .filter(([, granularity]) => granularity.dated && granularity.period)
        .map(([enrollmentId]) => enrollmentId),
    )
    const hasMixedGranularity = mixedEnrollmentIds.size > 0
    const eligibleRecords = attendanceRecords.filter(
      (record) => !mixedEnrollmentIds.has(String(record.enrollment)),
    )
    const totals = eligibleRecords.reduce((summary, record) => ({
      schoolDays: summary.schoolDays + Number(record.school_days || 0),
      daysPresent: summary.daysPresent + Number(record.days_present || 0),
      absences: summary.absences + Number(record.absences || 0),
      excusedAbsences: summary.excusedAbsences + (Number(record.excused_absences) || 0),
      unclassifiedExcusedRecords: summary.unclassifiedExcusedRecords + (record.excused_absences == null ? 1 : 0),
      timesTardy: summary.timesTardy + Number(record.times_tardy || 0),
    }), { schoolDays: 0, daysPresent: 0, absences: 0, excusedAbsences: 0, unclassifiedExcusedRecords: 0, timesTardy: 0 })

    return {
      schoolDays: hasMixedGranularity ? null : totals.schoolDays,
      daysPresent: hasMixedGranularity ? null : totals.daysPresent,
      absences: hasMixedGranularity ? null : totals.absences,
      excusedAbsences: hasMixedGranularity ? null : totals.excusedAbsences,
      unclassifiedExcusedRecords: attendanceRecords.filter((record) => record.excused_absences == null).length,
      timesTardy: hasMixedGranularity ? null : totals.timesTardy,
      percentage: !hasMixedGranularity && totals.schoolDays
        ? ((totals.daysPresent / totals.schoolDays) * 100).toFixed(2)
        : null,
      mixedGranularityEnrollmentCount: mixedEnrollmentIds.size,
    }
  }, [attendanceRecords])

  const monitoringSummary = useMemo(() => [
    {
      area: 'Academic concern',
      value: academicSummary.generalAverage ?? 'No record',
      status: academicSummary.generalAverage == null ? 'No record' : Number(academicSummary.generalAverage) < 75 ? 'YES' : 'NO',
    },
    {
      area: 'Attendance',
      value: attendanceSummary.percentage == null ? 'No record' : `${attendanceSummary.percentage}%`,
      status: attendanceSummary.percentage == null ? 'No record' : 'Recorded',
    },
    {
      area: 'Behavior',
      value: behaviorRecords.length ? `${behaviorRecords.length} assessments` : 'No record',
      status: behaviorRecords.length ? 'Recorded' : 'No record',
    },
    {
      area: 'AI prediction',
      value: latestPrediction ? (latestPrediction.risk_level === 'High' ? 'AT RISK' : 'NOT AT RISK') : 'No record',
      status: latestPrediction ? 'Stored prediction' : 'No record',
    },
    {
      area: 'Intervention',
      value: interventions.length ? `${interventions.length} records` : 'No record',
      status: interventions.length ? 'Recorded' : 'No record',
    },
  ], [academicSummary, attendanceSummary, behaviorRecords.length, interventions.length, latestPrediction])

  const currentRole = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canGeneratePrediction = ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER'].includes(currentRole)

  async function handleGeneratePrediction() {
    if (!canGeneratePrediction) {
      setPredictionError('You do not have permission to generate a prediction.')
      return
    }
    if (generatingPrediction) {
      return
    }

    setGeneratingPrediction(true)
    setGenerationMessage('')
    setPredictionError('')

    try {
      await generatePrediction(id)
      const [predictionData, factorData] = await Promise.all([
        getStudentRelatedRiskPredictions(id, { ordering: '-prediction_date' }),
        getStudentRelatedPredictionFactors(id, { ordering: 'feature_name' }),
      ])

      const normalizedPredictions = normalizeListResponse(predictionData)
      const normalizedFactors = normalizeListResponse(factorData)

      setPredictions(normalizedPredictions.items)
      setPredictionFactors(normalizedFactors.items)
      setStudentSummary((current) => ({
        ...current,
        predictionCount: normalizedPredictions.count,
        predictionFactorCount: normalizedFactors.count,
      }))
      setGenerationMessage('Prediction generated successfully. Refreshing the latest scores.')
    } catch (err) {
      const diagnostics = err.response?.data?.diagnostics
      setPredictionError(diagnostics?.length ? `${getApiErrorMessage(err)} ${diagnostics.join(' ')}` : getApiErrorMessage(err))
    } finally {
      setGeneratingPrediction(false)
    }
  }

  const enrollmentSummary = useMemo(() => {
    if (!enrollments.length) {
      return null
    }

    const latest = enrollments[0]
    return {
      gradeLevel: latest.grade_level_name || latest.grade_level || null,
      schoolLevel: latest.school_level || null,
      section: latest.section_name || latest.section || null,
      strand: latest.strand_name || latest.strand || null,
      academicYear: latest.academic_year_name || latest.academic_year || null,
      status: latest.enrollment_status || null,
    }
  }, [enrollments])

  const studentName = student ? [student.first_name, student.last_name].filter(Boolean).join(' ') : ''
  const studentInitials = student
    ? [student.first_name?.[0], student.last_name?.[0]].filter(Boolean).join('').toUpperCase() || 'ST'
    : 'ST'

  const latestIntervention = interventions[0] || null

  const tabItems = [
    { key: 'overview', label: 'Overview' },
    { key: 'academics', label: 'Academics' },
    { key: 'attendance', label: 'Attendance' },
    { key: 'behavior', label: 'Behavior' },
    { key: 'interventions', label: 'Interventions' },
    { key: 'predictions', label: 'Predictions' },
  ]

  if (studentLoading) {
    return <LoadingSpinner label="Loading student profile..." />
  }

  if (studentError) {
    return <ErrorBanner message={studentError} />
  }

  if (!student) {
    return <EmptyState title="Student not found" message="The requested student could not be located." />
  }

  return (
    <div className="page-stack student-detail-page">
      <PageHeader
        eyebrow="Student profile"
        title={studentName || 'Student profile'}
        description={`LRN: ${safeText(student.lrn)}`}
        actions={(
          <div className="tab-navigation" role="tablist" aria-label="Student detail navigation">
            {tabItems.map((tab) => (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.key}
                className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      />

      <section className="student-profile-header">
        <div className="student-profile-card">
          <div className="profile-avatar">{studentInitials}</div>
          <div className="student-profile-meta">
            <p className="eyebrow">Profile</p>
            <h2>{studentName || 'Student profile'}</h2>

            <div className="student-keyline">
              <span className="info-pill">{safeText(enrollmentSummary?.gradeLevel) || 'Grade unavailable'}</span>
              <span className="info-pill">{safeText(enrollmentSummary?.section) || 'Section unavailable'}</span>
              <span className="info-pill">{safeText(enrollmentSummary?.academicYear) || 'Year unavailable'}</span>
            </div>

            <div className="student-profile-details">
              <div>
                <p><strong>Grade level</strong></p>
                <p>{safeText(enrollmentSummary?.gradeLevel)}</p>
              </div>
              <div>
                <p><strong>Section</strong></p>
                <p>{safeText(enrollmentSummary?.section)}</p>
              </div>
              <div>
                <p><strong>Academic year</strong></p>
                <p>{safeText(enrollmentSummary?.academicYear)}</p>
              </div>
              <div>
                <p><strong>School level</strong></p>
                <p>{safeText(enrollmentSummary?.schoolLevel)}</p>
              </div>
              <div>
                <p><strong>Strand</strong></p>
                <p>{safeText(enrollmentSummary?.strand)}</p>
              </div>
            </div>
          </div>
        </div>

        <aside className="student-summary-card">
          <div className="student-summary-row">
            <span>Risk level</span>
            <span className={riskBadgeClass(latestPrediction?.risk_level)}>{safeText(latestPrediction?.risk_level || 'Unknown')}</span>
          </div>
          <div className="student-summary-row">
            <span>Latest prediction</span>
            <span>{safeText(latestPrediction?.prediction_date)}</span>
          </div>
          <div className="student-summary-row">
            <span>Model</span>
            <span>{safeText(latestPrediction?.model_name)}</span>
          </div>
          <div className="student-summary-row">
            <span>Factors</span>
            <span>{studentSummary.predictionFactorCount}</span>
          </div>
        </aside>
      </section>

      <div className="student-detail-stats">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic records</p>
          <p className="stat-value">{studentSummary.academicCount}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Attendance records</p>
          <p className="stat-value">{studentSummary.attendanceCount}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Behavior assessments</p>
          <p className="stat-value">{studentSummary.behaviorCount}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Interventions</p>
          <p className="stat-value">{studentSummary.interventionCount}</p>
        </article>
      </div>

      <InterventionFormModal
        isOpen={showInterventionModal}
        onClose={() => {
          setShowInterventionModal(false)
          setSelectedIntervention(null)
        }}
        currentValue={selectedIntervention}
        studentName={studentName}
        latestPrediction={latestPrediction}
        latestPredictionFactors={latestPredictionFactors}
        enrollmentId={enrollments[0]?.id || null}
        onSaved={() => {
          setShowInterventionModal(false)
          setSelectedIntervention(null)
          refreshStudentRecords()
        }}
        userRole="teacher"
      />

      {activeTab === 'overview' && (
        <section className="student-section overview-section">
          <section className="detail-card workflow-guide-card" style={{ marginBottom: 'var(--space-4)' }}>
            <div className="section-header">
              <div>
                <p className="eyebrow">Support workflow</p>
                <h3>What to review next</h3>
              </div>
            </div>
            <ul className="workflow-guide-list">
              <li>Review the latest prediction and the top risk drivers before planning a response.</li>
              <li>Use the academics, attendance, and behavior tabs to confirm whether the concern is growing or improving.</li>
              <li>Create an intervention when the student needs a coordinated follow-up or escalation.</li>
            </ul>
            <div className="workflow-guide-actions">
              <span className="action-chip">Student-centered view</span>
              <span className="action-chip">Action-ready support</span>
            </div>
          </section>
          <div className="overview-grid">
            <article className="detail-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Personal information</p>
                  <h3>Student profile</h3>
                </div>
              </div>
              <div className="student-info-list">
                <div>
                  <p><strong>Name</strong></p>
                  <p>{studentName}</p>
                </div>
                <div>
                  <p><strong>Student ID</strong></p>
                  <p>{safeText(student.lrn)}</p>
                </div>
                <div>
                  <p><strong>Sex</strong></p>
                  <p>{safeText(student.gender)}</p>
                </div>
                <div>
                  <p><strong>Date of birth</strong></p>
                  <p>{safeText(student.birth_date)}</p>
                </div>
                <div>
                  <p><strong>Status</strong></p>
                  <p>{safeText(student.student_status)}</p>
                </div>
              </div>
            </article>

            <article className="detail-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Enrollment information</p>
                  <h3>Current placement</h3>
                </div>
              </div>
              <div className="student-info-list">
                <div>
                  <p><strong>Current grade</strong></p>
                  <p>{safeText(enrollmentSummary?.gradeLevel)}</p>
                </div>
                <div>
                  <p><strong>Current section</strong></p>
                  <p>{safeText(enrollmentSummary?.section)}</p>
                </div>
                <div>
                  <p><strong>School year</strong></p>
                  <p>{safeText(enrollmentSummary?.academicYear)}</p>
                </div>
                <div>
                  <p><strong>Enrollment status</strong></p>
                  <p>{safeText(enrollmentSummary?.status)}</p>
                </div>
              </div>
            </article>

            <article className="detail-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Guardian information</p>
                  <h3>Contacts</h3>
                </div>
              </div>
              <div className="student-info-list">
                <div>
                  <p><strong>Guardian name</strong></p>
                  <p>Not available</p>
                </div>
                <div>
                  <p><strong>Guardian contact</strong></p>
                  <p>Not available</p>
                </div>
              </div>
            </article>

            <article className="detail-card decision-support-card overview-support-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Academic concern</p>
                  <h3>General Average: {academicSummary.generalAverage ?? 'No record'}</h3>
                </div>
              </div>
              <p><strong>Academic Concern:</strong> {academicConcern ? 'YES' : 'NO'}</p>
              <p><strong>Reason:</strong> {academicConcern ? 'General Average is below 75.' : 'General Average is at or above 75.'}</p>
              <p className="support-copy">This is a school monitoring rule and is not the AI prediction.</p>
            </article>

            <article className="detail-card decision-support-card overview-support-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">AI decision support</p>
                  <h3>{riskGuidance.title}</h3>
                </div>
              </div>
              <p><strong>AI Risk:</strong> {aiRiskStatus}</p>
              <p><strong>Probability:</strong> {latestPrediction ? formatProbability(latestPrediction.probability) : 'No record'}</p>
              <p><strong>Model:</strong> Random Forest</p>
              <p className="support-copy">This is an AI-generated risk estimate based on multiple student indicators. It is not a diagnosis and should not replace teacher/adviser judgment.</p>
              <ul className="support-list">
                {riskGuidance.items.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </article>
          </div>

          {academicConcern && latestPrediction && latestPrediction.risk_level === 'Low' ? (
            <div className="status-banner status-banner--warning">
              Academic concern and AI risk are different indicators. The student currently has an academic concern because the General Average is below 75. However, the Random Forest model classified the current overall pattern as Not At Risk.
            </div>
          ) : null}

          {!academicConcern && latestPrediction && latestPrediction.risk_level === 'High' ? (
            <div className="status-banner status-banner--warning">
              The student’s General Average is not below 75, but the AI model identified a higher-risk pattern based on the combination of available student indicators.
            </div>
          ) : null}

          <section className="detail-card monitoring-summary-card">
            <div className="section-header">
              <div>
                <p className="eyebrow">Integrated monitoring</p>
                <h3>Student monitoring summary</h3>
              </div>
              <span className="badge badge--info">Trend classification unavailable</span>
            </div>
            <div className="table-card">
              <table>
                <thead><tr><th>Area</th><th>Current information</th><th>Status</th></tr></thead>
                <tbody>
                  {monitoringSummary.map((item) => <tr key={item.area}><td>{item.area}</td><td>{item.value}</td><td>{item.status}</td></tr>)}
                </tbody>
              </table>
            </div>
            <p className="support-copy">Historical records are shown in the tabs below. No overall improving, stable, or declining label is assigned without a supported calculation.</p>
          </section>

          <div className="overview-data-grid">
            <article className="detail-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Prediction summary</p>
                  <h3>Latest prediction</h3>
                </div>
              </div>
              {predictionLoading ? (
                <div className="skeleton-card skeleton-tall" />
              ) : latestPrediction ? (
                <>
                  <div className="summary-card-list">
                    <div className="summary-card-item">
                      <p className="stat-label">Current risk</p>
                      <span className={riskBadgeClass(latestPrediction.risk_level)}>{safeText(latestPrediction.risk_level)}</span>
                    </div>
                    <div className="summary-card-item">
                      <p className="stat-label">Probability</p>
                      <p>{formatProbability(latestPrediction.probability)}</p>
                    </div>
                    <div className="summary-card-item">
                      <p className="stat-label">Prediction date</p>
                      <p>{safeText(latestPrediction.prediction_date)}</p>
                    </div>
                    <div className="summary-card-item">
                      <p className="stat-label">Model</p>
                      <p>{safeText(latestPrediction.model_name)}</p>
                    </div>
                  </div>
                  {latestPrediction ? (
                    <div className="grade-encoding-actions">
                      <button type="button" className="action-button" onClick={() => setShowInterventionModal(true)}>
                        Create intervention
                      </button>
                    </div>
                  ) : null}
                  {canGeneratePrediction ? (
                    <div className="grade-encoding-actions" style={{ marginTop: '1rem' }}>
                      <button type="button" className="action-button action-button--secondary" onClick={handleGeneratePrediction} disabled={generatingPrediction}>
                        {generatingPrediction ? 'Generating Prediction…' : 'Generate Prediction'}
                      </button>
                      {generationMessage ? <span className="status-text">{generationMessage}</span> : null}
                      {predictionError ? <ErrorBanner message={predictionError} /> : null}
                    </div>
                  ) : null}
                </>
              ) : (
                <>
                  <EmptyState title="No prediction records" message={predictionError || 'No stored prediction is available for this student.'} />
                  {canGeneratePrediction ? (
                    <div className="grade-encoding-actions">
                      <button type="button" className="action-button action-button--secondary" onClick={handleGeneratePrediction} disabled={generatingPrediction}>
                        {generatingPrediction ? 'Generating Prediction…' : 'Generate Prediction'}
                      </button>
                    </div>
                  ) : null}
                </>
              )}
            </article>

            <article className="detail-card feature-card">
              <div className="section-header">
                <div>
                  <p className="eyebrow">Key indicators</p>
                  <h3>Student progress signals</h3>
                </div>
              </div>
              <div className="student-indicators">
                <div className="indicator-card">
                  <p className="stat-label">General average</p>
                  <p className="stat-value">{academicSummary.generalAverage ?? 'No record'}</p>
                  {academicSummary.generalAverage != null && Number(academicSummary.generalAverage) < 75 ? <small>Below 75</small> : null}
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Failed subjects</p>
                  <p className="stat-value">{academicRecords.length ? academicSummary.failedSubjects : 'No record'}</p>
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Lowest grade</p>
                  <p className="stat-value">{academicSummary.lowestGrade ?? 'No record'}</p>
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Attendance</p>
                  <p className="stat-value">{!attendanceRecords.length ? 'No record' : attendanceSummary.percentage == null ? 'Unavailable' : `${attendanceSummary.percentage}%`}</p>
                  {attendanceSummary.mixedGranularityEnrollmentCount
                    ? <small>Combined attendance totals are unavailable: {attendanceSummary.mixedGranularityEnrollmentCount} enrollment(s) have dated and period-level records that may overlap. {attendanceSummary.unclassifiedExcusedRecords} attendance record(s) have an unclassified excused-absence value.</small>
                    : attendanceSummary.schoolDays != null
                      ? <small>{attendanceSummary.daysPresent}/{attendanceSummary.schoolDays} days · {attendanceSummary.absences} recorded absent · {attendanceSummary.excusedAbsences} known excused · {attendanceSummary.timesTardy} tardy{attendanceSummary.unclassifiedExcusedRecords ? ` · ${attendanceSummary.unclassifiedExcusedRecords} record(s) unclassified` : ''}</small>
                      : <small>Attendance totals are unavailable because no scheduled-day denominator exists.</small>}
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Academic items</p>
                  <p className="stat-value">{studentSummary.academicCount}</p>
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Attendance items</p>
                  <p className="stat-value">{studentSummary.attendanceCount}</p>
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Behavior items</p>
                  <p className="stat-value">{studentSummary.behaviorCount}</p>
                </div>
                <div className="indicator-card">
                  <p className="stat-label">Interventions</p>
                  <p className="stat-value">{studentSummary.interventionCount}</p>
                </div>
              </div>
            </article>
          </div>
        </section>
      )}

      {activeTab === 'academics' && (
        <section className="student-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Academics</p>
              <h3>Academic performance</h3>
            </div>
              <label>Academic period<select value={academicPeriod} onChange={(event) => setAcademicPeriod(event.target.value)}><option value="">All</option><option value="Quarter:1">Quarter 1</option><option value="Quarter:2">Quarter 2</option><option value="Quarter:3">Quarter 3</option><option value="Quarter:4">Quarter 4</option><option value="Semester:1">Semester 1</option><option value="Semester:2">Semester 2</option></select></label>
          </div>

          {academicError ? <ErrorBanner message={academicError} /> : null}
          {academicLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!academicLoading && !academicError && academicRecords.length === 0 ? (
            <EmptyState title="No academic data" message="No academic records are available for this student." />
          ) : null}

          {!academicLoading && !academicError && academicRecords.length > 0 ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Subject</th>
                    <th>Teacher</th>
                    <th>Period</th>
                    <th>Grade</th>
                    <th>Final grade</th>
                    <th>Remarks</th>
                    <th>Academic year</th>
                  </tr>
                </thead>
                <tbody>
                  {academicRecords.map((record) => (
                    <tr key={record.id}>
                      <td>
                        <span className="badge badge--subject">{safeText(record.subject_name || record.subject)}</span>
                        {record.official_subject_code || record.subject_code ? (
                          <small>
                            {record.official_subject_code ? `Official: ${safeText(record.official_subject_code)}` : ''}
                            {record.official_subject_code && record.subject_code ? ' · ' : ''}
                            {record.subject_code ? `System ID: ${safeText(record.subject_code)}` : ''}
                          </small>
                        ) : null}
                      </td>
                      <td>{safeText(record.encoded_by_name)}</td>
                      <td><span className="badge badge--period">{safeText(record.quarter ? `Quarter ${record.quarter}` : record.semester ? `Semester ${record.semester}` : record.grading_period_type)}</span></td>
                      <td>{record.grade ?? 'Not available'}</td>
                      <td>{record.final_grade ?? 'Not available'}</td>
                      <td>{safeText(record.remarks)}</td>
                      <td>{safeText(record.academic_year_name || record.academic_year)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      )}

      {activeTab === 'attendance' && (
        <section className="student-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Attendance</p>
              <h3>Attendance monitoring</h3>
            </div>
          </div>

          {attendanceError ? <ErrorBanner message={attendanceError} /> : null}
          {attendanceLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!attendanceLoading && !attendanceError && attendanceRecords.length === 0 ? (
            <EmptyState title="No attendance records" message="No attendance records are available for this student." />
          ) : null}

          {!attendanceLoading && !attendanceError && attendanceRecords.length > 0 ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Attendance %</th>
                    <th>Present</th>
                    <th>Absent</th>
                    <th>Excused</th>
                    <th>Late</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceRecords.map((record) => {
                    const schoolDays = Number(record.school_days ?? 0)
                    const present = Number(record.days_present ?? 0)
                    const absent = Number(record.absences ?? 0)
                    const excused = record.excused_absences == null ? 'Unclassified' : Number(record.excused_absences)
                    const late = Number(record.times_tardy ?? 0)
                    const attendancePercentage = schoolDays > 0 ? Math.round((present / schoolDays) * 100) : null
                    const status = attendancePercentage == null ? 'Unavailable' : attendancePercentage < 80 ? 'Attention needed' : 'Stable'
                    return (
                      <tr key={record.id}>
                        <td>{safeText(record.month)}</td>
                        <td>{attendancePercentage == null ? 'Unavailable' : `${attendancePercentage}%`}</td>
                        <td>{present}</td>
                        <td>{absent}</td>
                        <td>{excused}</td>
                        <td>{late}</td>
                        <td><span className={`badge badge--status ${status === 'Attention needed' ? 'status-warning' : status === 'Stable' ? 'status-success' : 'status-neutral'}`}>{status}</span></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      )}

      {activeTab === 'behavior' && (
        <section className="student-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Behavior</p>
              <h3>Behavioral evaluations</h3>
            </div>
          </div>

          {behaviorError ? <ErrorBanner message={behaviorError} /> : null}
          {behaviorLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!behaviorLoading && !behaviorError && behaviorRecords.length === 0 ? (
            <EmptyState title="No behavior records" message="No behavioral records are available for this student." />
          ) : null}

          {!behaviorLoading && !behaviorError && behaviorRecords.length > 0 ? (
            <div className="table-card">
              <div className="record-summary-grid">
                <article className="detail-card">
                  <p className="stat-label">Behavior average</p>
                  <p className="stat-value">{behaviorAverage ?? '—'}</p>
                </article>
                <article className="detail-card">
                  <p className="stat-label">Recorded assessments</p>
                  <p className="stat-value">{behaviorRecords.length}</p>
                </article>
                <article className="detail-card">
                  <p className="stat-label">Latest period</p>
                  <p className="stat-value">{behaviorRecords[0]?.quarter ? `Quarter ${behaviorRecords[0].quarter}` : safeText(behaviorRecords[0]?.grading_period_type)}</p>
                </article>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Indicator</th>
                    <th>Core value</th>
                    <th>Rating</th>
                    <th>Quarter</th>
                    <th>Date</th>
                    <th>Remarks</th>
                  </tr>
                </thead>
                <tbody>
                  {behaviorRecords.map((record) => {
                    const ratingDisplay = record.rating_code || record.rating_label || record.rating || 'Not available'
                    const period = record.quarter ? `Q${record.quarter}` : record.grading_period_type || 'Not available'
                    return (
                      <tr key={record.id}>
                        <td>{safeText(record.behavior_indicator_name || record.behavior_indicator)}</td>
                        <td>{safeText(record.core_value_name || record.core_value)}</td>
                        <td>{ratingDisplay}</td>
                        <td>{period}</td>
                        <td>{safeText(record.assessment_date)}</td>
                        <td>{safeText(record.remarks)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      )}

      {activeTab === 'interventions' && (
        <section className="student-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Interventions</p>
              <h3>Support and outcomes</h3>
            </div>
            {latestPrediction ? (
              <button type="button" className="action-button" onClick={() => setShowInterventionModal(true)}>
                Create intervention
              </button>
            ) : null}
          </div>

          {interventionError ? <ErrorBanner message={interventionError} /> : null}
          {interventionLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!interventionLoading && !interventionError && interventions.length === 0 ? (
            <EmptyState title="No intervention history" message="No intervention records are available for this student." />
          ) : null}

          {!interventionLoading && !interventionError && interventions.length > 0 ? (
            <div className="table-card">
              <div className="record-summary-grid">
                <article className="detail-card">
                  <p className="stat-label">Current status</p>
                  <p className="stat-value">{latestIntervention?.status || '—'}</p>
                </article>
                <article className="detail-card">
                  <p className="stat-label">Assigned staff</p>
                  <p className="stat-value">{latestIntervention?.assigned_personnel || 'Unassigned'}</p>
                </article>
                <article className="detail-card">
                  <p className="stat-label">Priority</p>
                  <p className="stat-value">{latestIntervention?.priority || '—'}</p>
                </article>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Recommendation</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Start</th>
                    <th>End</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((item) => (
                    <tr key={item.id}>
                      <td>{safeText(item.intervention_type)}</td>
                      <td>{safeText(item.recommendation || item.notes)}</td>
                      <td><span className={`badge badge--status ${item.status === 'completed' ? 'status-success' : item.status === 'in_progress' ? 'status-warning' : 'status-neutral'}`}>{safeText(item.status)}</span></td>
                      <td>{safeText(item.priority)}</td>
                      <td>{safeText(item.start_date)}</td>
                      <td>{safeText(item.end_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      )}

      {activeTab === 'predictions' && (
        <section className="student-section predictions-section">
          <div className="section-header">
            <div>
              <p className="eyebrow">Predictions</p>
              <h3>Prediction history and explainability</h3>
            </div>
          </div>

          {predictionError ? <ErrorBanner message={predictionError} /> : null}
          {generationMessage ? <div className="status-banner status-banner--success">{generationMessage}</div> : null}
          {canGeneratePrediction ? (
            <div className="grade-encoding-actions" style={{ marginBottom: '1rem' }}>
              <button type="button" className="action-button" onClick={handleGeneratePrediction} disabled={generatingPrediction}>
                {generatingPrediction ? 'Generating Prediction…' : 'Generate Prediction'}
              </button>
            </div>
          ) : null}
          {predictionLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!predictionLoading && !predictionError && predictions.length === 0 ? (
            <EmptyState title="No prediction history" message="No prediction records are available for this student." />
          ) : null}

          {!predictionLoading && !predictionError && predictions.length > 0 ? (
            <div className="predictions-grid">
              <article className="detail-card latest-prediction-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">Latest prediction</p>
                    <h3>{latestPrediction?.risk_level ? `${latestPrediction.risk_level} risk` : 'Prediction details'}</h3>
                  </div>
                </div>
                <div className="summary-card-list">
                  <div className="summary-card-item">
                    <p className="stat-label">Risk level</p>
                    <span className={riskBadgeClass(latestPrediction?.risk_level)}>{safeText(latestPrediction?.risk_level)}</span>
                  </div>
                  <div className="summary-card-item">
                    <p className="stat-label">Probability</p>
                    <p>{formatProbability(latestPrediction?.probability)}</p>
                  </div>
                  <div className="summary-card-item">
                    <p className="stat-label">Model</p>
                    <p>{safeText(latestPrediction?.model_name)}</p>
                  </div>
                  <div className="summary-card-item">
                    <p className="stat-label">Prediction date</p>
                    <p>{safeText(latestPrediction?.prediction_date)}</p>
                  </div>
                </div>
                <div className="prediction-explanation-block">
                  <p className="eyebrow">Explanation summary</p>
                  <p className="prediction-explanation-text">
                    {latestPrediction?.explanation || 'No explanation summary is available for the latest prediction.'}
                  </p>
                </div>
              </article>

              <article className="detail-card prediction-drivers-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">Risk drivers</p>
                    <h3>Top contributing factors</h3>
                  </div>
                </div>
                  {latestPredictionDrivers.length === 0 ? (
                  <EmptyState title="No factor details" message="No factor contributions are available for the latest prediction." />
                ) : (
                  <div className="prediction-drivers-grid">
                    {latestPredictionDrivers.map((factor) => (
                      <article key={factor.id} className="driver-card">
                        <p className="driver-label">{safeText(factor.feature_name)}</p>
                        <p className="driver-value">{safeText(factor.feature_value)}</p>
                        <div className="driver-meta">
                          <span>{formatFactorContribution(factor.contribution)}</span>
                          <span>{safeText(factor.direction)}</span>
                        </div>
                        <p className="driver-description">
                          {safeText(factor.explanation_text || 'This information was considered by the model.')}
                        </p>
                      </article>
                    ))}
                  </div>
                )}
              </article>

              <article className="detail-card prediction-timeline-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">Prediction timeline</p>
                    <h3>Recent risk history</h3>
                  </div>
                </div>
                <ul className="timeline-list">
                  {predictionTimeline.map((prediction) => (
                    <li key={prediction.id} className="timeline-item">
                      <div className="timeline-item-top">
                        <span>{safeText(prediction.prediction_date)}</span>
                        <span className={riskBadgeClass(prediction.risk_level)}>{safeText(prediction.risk_level)}</span>
                      </div>
                      <div className="timeline-item-summary">
                        <span>{formatProbability(prediction.probability)}</span>
                        <span>{safeText(prediction.model_name)}</span>
                      </div>
                      <p>{prediction.explanation ? `${prediction.explanation.slice(0, 120)}${prediction.explanation.length > 120 ? '…' : ''}` : 'No summary available.'}</p>
                    </li>
                  ))}
                </ul>
              </article>

              <article className="detail-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">History</p>
                    <h3>Past predictions</h3>
                  </div>
                </div>
                <div className="table-card">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Risk</th>
                        <th>Probability</th>
                        <th>Model</th>
                        <th>Explanation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((prediction) => (
                        <tr key={prediction.id} className={prediction.id === latestPrediction?.id ? 'highlight-row' : ''}>
                          <td>{safeText(prediction.prediction_date)}</td>
                          <td><span className={riskBadgeClass(prediction.risk_level)}>{safeText(prediction.risk_level)}</span></td>
                          <td>{formatProbability(prediction.probability)}</td>
                          <td>{safeText(prediction.model_name)}</td>
                          <td>{safeText(prediction.explanation)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="detail-card">
                <div className="section-header">
                  <div>
                    <p className="eyebrow">Prediction factors</p>
                    <h3>Latest factor contributions</h3>
                  </div>
                </div>
                {predictionFactorError ? <ErrorBanner message={predictionFactorError} /> : null}
                {predictionFactorLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
                {!predictionFactorLoading && !predictionFactorError && latestPredictionFactors.length === 0 ? (
                  <EmptyState title="No latest factors" message="No factor data is associated with the latest prediction." />
                ) : null}
                {!predictionFactorLoading && !predictionFactorError && latestPredictionFactors.length > 0 ? (
                  <div className="table-card factor-table-card">
                    <table>
                      <thead>
                        <tr>
                          <th>Factor</th>
                          <th>Current student value</th>
                          <th>Why it matters</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestPredictionFactors.map((factor) => (
                          <tr key={factor.id}>
                            <td>{safeText(factor.feature_name)}</td>
                            <td>{safeText(factor.feature_value)}</td>
                            <td>{safeText(factor.explanation_text || 'This information was considered by the model.')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
              </article>
            </div>
          ) : null}
        </section>
      )}
    </div>
  )
}

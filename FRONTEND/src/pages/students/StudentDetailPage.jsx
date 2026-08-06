import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
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

function getBehaviorClassification(average) {
  const numericAverage = Number(average)
  if (Number.isNaN(numericAverage)) {
    return 'Pending'
  }

  if (numericAverage >= 4.5) {
    return 'Outstanding'
  }
  if (numericAverage >= 4.0) {
    return 'Very Good'
  }
  if (numericAverage >= 3.0) {
    return 'Good'
  }
  if (numericAverage >= 2.0) {
    return 'Needs Improvement'
  }
  return 'At Risk'
}

export function StudentDetailPage() {
  const { id } = useParams()

  const [student, setStudent] = useState(null)
  const [studentError, setStudentError] = useState('')
  const [studentLoading, setStudentLoading] = useState(true)

  const [enrollments, setEnrollments] = useState([])
  const [enrollmentError, setEnrollmentError] = useState('')
  const [enrollmentLoading, setEnrollmentLoading] = useState(true)

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

  const [predictions, setPredictions] = useState([])
  const [predictionError, setPredictionError] = useState('')
  const [predictionLoading, setPredictionLoading] = useState(true)

  const [predictionFactors, setPredictionFactors] = useState([])
  const [predictionFactorError, setPredictionFactorError] = useState('')
  const [predictionFactorLoading, setPredictionFactorLoading] = useState(true)

  const [activeTab, setActiveTab] = useState('overview')

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
      setEnrollmentLoading(true)
      setEnrollmentError('')

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
        setEnrollmentError(message)
      } finally {
        if (active) {
          setStudentLoading(false)
          setEnrollmentLoading(false)
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
        const [academicData, attendanceData, behaviorData, interventionData, predictionData, predictionFactorData] = await Promise.all([
          getStudentRelatedAcademicRecords(id, { ordering: '-created_at' }),
          getStudentRelatedAttendanceRecords(id, { ordering: '-created_at' }),
          getStudentRelatedBehavioralAssessments(id, { ordering: '-assessment_date' }),
          getStudentRelatedInterventions(id, { ordering: '-created_at' }),
          getStudentRelatedRiskPredictions(id, { ordering: '-prediction_date' }),
          getStudentRelatedPredictionFactors(id, { ordering: 'feature_name' }),
        ])

        if (!active) {
          return
        }

        const normalizedAcademic = normalizeListResponse(academicData)
        const normalizedAttendance = normalizeListResponse(attendanceData)
        const normalizedBehavior = normalizeListResponse(behaviorData)
        const normalizedInterventions = normalizeListResponse(interventionData)
        const normalizedPredictions = normalizeListResponse(predictionData)
        const normalizedPredictionFactors = normalizeListResponse(predictionFactorData)

        setAcademicRecords(normalizedAcademic.items)
        setAttendanceRecords(normalizedAttendance.items)
        setBehaviorRecords(normalizedBehavior.items)
        setInterventions(normalizedInterventions.items)
        setPredictions(normalizedPredictions.items)
        setPredictionFactors(normalizedPredictionFactors.items)

        setStudentSummary({
          academicCount: normalizedAcademic.count,
          attendanceCount: normalizedAttendance.count,
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
  }, [id])

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

  const riskGuidance = useMemo(() => {
    if (!latestPrediction) {
      return {
        title: 'No prediction available',
        items: ['Generate a risk prediction to see tailored guidance and intervention recommendations.'],
      }
    }

    if (latestPrediction.risk_level === 'High') {
      return {
        title: 'High risk action plan',
        items: [
          'Review the student’s most recent risk factors immediately.',
          'Coordinate an urgent follow-up with teachers, guidance counselors, and parents.',
          'Check intervention status and assign targeted academic and behavioral support.',
        ],
      }
    }

    if (latestPrediction.risk_level === 'Moderate') {
      return {
        title: 'Moderate risk action plan',
        items: [
          'Monitor the student closely for early signs of performance decline.',
          'Schedule a progress check with the advising team.',
          'Reinforce attendance and engagement interventions where needed.',
        ],
      }
    }

    return {
      title: 'Low risk recommendation',
      items: [
        'Maintain current supports and continue tracking attendance and grades.',
        'Share positive risk progress with the student and family.',
        'Continue collaborating with teachers to sustain strong performance.',
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

  const behaviorClassification = useMemo(() => {
    return behaviorAverage ? getBehaviorClassification(behaviorAverage) : 'Pending'
  }, [behaviorAverage])

  const enrollmentSummary = useMemo(() => {
    if (!enrollments.length) {
      return null
    }

    const latest = enrollments[0]
    return {
      gradeLevel: latest.grade_level || null,
      section: latest.section || null,
      strand: latest.strand || null,
      academicYear: latest.academic_year || null,
      status: latest.enrollment_status || null,
    }
  }, [enrollments])

  const studentName = student ? [student.first_name, student.last_name].filter(Boolean).join(' ') : ''
  const studentInitials = student
    ? [student.first_name?.[0], student.last_name?.[0]].filter(Boolean).join('').toUpperCase() || 'ST'
    : 'ST'

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

      {activeTab === 'overview' && (
        <section className="student-section overview-section">
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
                  <p className="eyebrow">AI decision support</p>
                  <h3>{riskGuidance.title}</h3>
                </div>
              </div>
              <ul className="support-list">
                {riskGuidance.items.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </article>
          </div>

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
              ) : (
                <EmptyState title="No prediction records" message="No prediction data is available for this student." />
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
                    <th>Quarter</th>
                    <th>Grade</th>
                    <th>Remarks</th>
                    <th>Academic year</th>
                  </tr>
                </thead>
                <tbody>
                  {academicRecords.map((record) => (
                    <tr key={record.id}>
                      <td><span className="badge badge--subject">{safeText(record.subject)}</span></td>
                      <td><span className="badge badge--period">{safeText(record.quarter ? `Quarter ${record.quarter}` : record.semester ? `Semester ${record.semester}` : '—')}</span></td>
                      <td>{record.grade ?? 'Not available'}</td>
                      <td>{safeText(record.remarks)}</td>
                      <td>{safeText(record.academic_year)}</td>
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
                    <th>Late</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceRecords.map((record) => {
                    const schoolDays = Number(record.school_days ?? 0)
                    const present = Number(record.days_present ?? 0)
                    const absent = Number(record.absences ?? 0)
                    const late = Number(record.times_tardy ?? 0)
                    const attendancePercentage = schoolDays > 0 ? Math.round((present / schoolDays) * 100) : 0
                    const status = attendancePercentage < 80 ? 'Attention needed' : 'Stable'
                    return (
                      <tr key={record.id}>
                        <td>{safeText(record.month)}</td>
                        <td>{attendancePercentage}%</td>
                        <td>{present}</td>
                        <td>{absent}</td>
                        <td>{late}</td>
                        <td><span className={`badge badge--status ${status === 'Attention needed' ? 'status-warning' : 'status-success'}`}>{status}</span></td>
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
                  <p className="stat-label">Classification</p>
                  <p className="stat-value">{behaviorClassification}</p>
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
          </div>

          {interventionError ? <ErrorBanner message={interventionError} /> : null}
          {interventionLoading ? <div className="table-skeleton"><div /><div /><div /></div> : null}
          {!interventionLoading && !interventionError && interventions.length === 0 ? (
            <EmptyState title="No intervention history" message="No intervention records are available for this student." />
          ) : null}

          {!interventionLoading && !interventionError && interventions.length > 0 ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Reason</th>
                    <th>Status</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((item) => (
                    <tr key={item.id}>
                      <td>{safeText(item.intervention_type)}</td>
                      <td>{safeText(item.reason)}</td>
                      <td><span className={`badge badge--status ${item.status === 'Completed' ? 'status-success' : item.status === 'In Progress' ? 'status-warning' : 'status-neutral'}`}>{safeText(item.status)}</span></td>
                      <td>{safeText(item.start_date)}</td>
                      <td>{safeText(item.end_date)}</td>
                      <td>{safeText(item.outcome)}</td>
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
                          <th>Feature</th>
                          <th>Value</th>
                          <th>Contribution</th>
                          <th>Direction</th>
                          <th>Explanation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestPredictionFactors.map((factor) => (
                          <tr key={factor.id}>
                            <td>{safeText(factor.feature_name)}</td>
                            <td>{safeText(factor.feature_value)}</td>
                            <td>{factor.contribution ?? 'Not available'}</td>
                            <td>{safeText(factor.direction)}</td>
                            <td>{safeText(factor.explanation_text)}</td>
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

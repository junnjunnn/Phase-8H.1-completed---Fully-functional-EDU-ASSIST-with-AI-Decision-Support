import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  createAcademicRecord,
  getAcademicRecords,
  getAcademicYears,
  getEnrollments,
  getGradeLevels,
  getSections,
  getSubjects,
  updateAcademicRecord,
} from '../../services/academicsService'
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

function getAutoRemarks(gradeValue) {
  const numericValue = Number(gradeValue)
  if (Number.isNaN(numericValue)) {
    return ''
  }
  return numericValue >= 75 ? 'Pass' : 'Fail'
}

function validateGradeValue(gradeValue) {
  if (gradeValue === '' || gradeValue === null || gradeValue === undefined) {
    return 'Grade is required.'
  }

  const numericValue = Number(gradeValue)
  if (Number.isNaN(numericValue)) {
    return 'Grade must be numeric.'
  }

  if (numericValue < 0) {
    return 'Grade cannot be negative.'
  }

  if (numericValue > 100) {
    return 'Grade cannot exceed 100.'
  }

  return ''
}

export function GradeEncodingPage() {
  const { user } = useAuth()
  const location = useLocation()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageGrades = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN' || role === 'TEACHER'
  const isAdministrator = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN'

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [subjects, setSubjects] = useState([])

  const [filters, setFilters] = useState({
    academicYear: '',
    gradeLevel: '',
    section: '',
    subject: '',
    gradingPeriod: 'Quarter',
    quarter: '1',
  })

  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingClass, setLoadingClass] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const nextFilters = {
      academicYear: params.get('academic_year') || '',
      gradeLevel: params.get('grade_level') || '',
      section: params.get('section') || '',
      subject: params.get('subject') || '',
      gradingPeriod: 'Quarter',
      quarter: '1',
    }

    setFilters((currentFilters) => ({ ...currentFilters, ...nextFilters }))
  }, [location.search])

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')

      try {
        const [yearsData, levelsData, sectionsData, subjectsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getSubjects(),
        ])

        if (!active) {
          return
        }

        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(levelsData).items)
        setSections(normalizeListResponse(sectionsData).items)
        setSubjects(normalizeListResponse(subjectsData).items)
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

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const academicYear = params.get('academic_year') || ''
    const gradeLevel = params.get('grade_level') || ''
    const section = params.get('section') || ''
    const subject = params.get('subject') || ''

    if (academicYear && gradeLevel && section && subject) {
      loadClassData({ academicYear, gradeLevel, section, subject, gradingPeriod: filters.gradingPeriod, quarter: filters.quarter })
    }
  }, [location.search, filters.gradingPeriod, filters.quarter])

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
      const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
      return matchesYear && matchesLevel
    })
  }, [filters.academicYear, filters.gradeLevel, sections])

  const filteredSubjects = useMemo(() => {
    return subjects.filter((subject) => {
      const matchesLevel = !filters.gradeLevel || String(subject.grade_level) === String(filters.gradeLevel)
      return matchesLevel
    })
  }, [filters.gradeLevel, subjects])

  async function loadClassData(nextFilters = filters) {
    if (!nextFilters.academicYear || !nextFilters.gradeLevel || !nextFilters.section || !nextFilters.subject) {
      setError('Select an academic year, grade level, section, and subject before loading the grade sheet.')
      return
    }

    setLoadingClass(true)
    setError('')
    setSuccessMessage('')

    try {
      const [enrollmentsData, recordsData] = await Promise.all([
        getEnrollments({ academic_year: nextFilters.academicYear, grade_level: nextFilters.gradeLevel, section: nextFilters.section, enrollment_status: 'active' }),
        getAcademicRecords({ academic_year: nextFilters.academicYear, subject: nextFilters.subject, grading_period_type: nextFilters.gradingPeriod, quarter: nextFilters.gradingPeriod === 'Quarter' ? nextFilters.quarter : undefined }),
      ])

      const enrollments = normalizeListResponse(enrollmentsData).items
      const academicRecords = normalizeListResponse(recordsData).items

      const recordsByEnrollment = academicRecords.reduce((accumulator, record) => {
        accumulator[record.enrollment] = record
        return accumulator
      }, {})

      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      const studentMap = studentProfiles.reduce((accumulator, student) => {
        accumulator[student.id] = student
        return accumulator
      }, {})

      const classRows = enrollments.map((enrollment) => {
        const record = recordsByEnrollment[enrollment.id]
        const student = studentMap[enrollment.student]
        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          recordId: record?.id || null,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          grade: record?.grade ?? '',
          remarks: record?.remarks || '',
          finalGrade: record?.final_grade ?? '',
          status: record?.final_grade != null ? 'Finalized' : record?.id ? 'Saved' : 'Pending',
          encodedByCurrentUser: !record || record.encoded_by === user?.id,
          validationError: '',
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

  function updateRow(field, value, rowId) {
    setRows((currentRows) => currentRows.map((row) => {
      if (row.id !== rowId) {
        return row
      }

      return {
        ...row,
        [field]: value,
        validationError: field === 'grade' ? validateGradeValue(value) : row.validationError,
        remarks: field === 'grade' ? getAutoRemarks(value) : row.remarks,
      }
    }))
  }

  async function handleSave(shouldFinalize) {
    if (!canManageGrades) {
      setError('You do not have permission to encode grades for this class.')
      return
    }

    const validationErrors = rows.map((row) => ({ row, error: validateGradeValue(row.grade) }))
    const hasValidationErrors = validationErrors.some((entry) => entry.error)

    if (hasValidationErrors) {
      setRows((currentRows) => currentRows.map((row) => ({
        ...row,
        validationError: validateGradeValue(row.grade),
      })))
      setError('Resolve validation errors before saving the grade sheet.')
      return
    }

    setError('')
    setSuccessMessage('')

    try {
      const savedRows = []

      for (const row of rows) {
        const payload = {
          enrollment: row.enrollmentId,
          subject: Number(filters.subject),
          academic_year: Number(filters.academicYear),
          grading_period_type: filters.gradingPeriod,
          quarter: filters.gradingPeriod === 'Quarter' ? Number(filters.quarter) : null,
          semester: filters.gradingPeriod === 'Semester' ? 1 : null,
          grade: Number(row.grade),
          remarks: row.remarks || getAutoRemarks(row.grade),
          final_grade: shouldFinalize ? Number(row.grade) : null,
        }

        const savedRecord = row.recordId
          ? await updateAcademicRecord(row.recordId, payload)
          : await createAcademicRecord(payload)

        savedRows.push({
          ...row,
          recordId: savedRecord.id,
          status: shouldFinalize ? 'Finalized' : 'Saved',
          finalGrade: savedRecord.final_grade ?? '',
          grade: savedRecord.grade,
          remarks: savedRecord.remarks || getAutoRemarks(savedRecord.grade),
          validationError: '',
        })
      }

      setRows(savedRows)
      setSuccessMessage(shouldFinalize ? 'Grades finalized successfully.' : 'Grades saved as draft successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading grade encoding workspace..." />
  }

  return (
    <div className="page-stack grade-encoding-page">
      <PageHeader
        eyebrow="Academics"
        title="Teacher grade encoding"
        description="Select your assigned class, encode quarter grades, and save drafts or final marks without affecting the prediction workflow."
        actions={(
          <Link className="action-button action-button--secondary" to="/academics">
            Back to academics
          </Link>
        )}
      />

      {!canManageGrades ? (
        <div className="status-banner status-banner--warning">You do not currently have permission to encode grades.</div>
      ) : null}

      <section className="students-panel grade-encoding-panel">
        <div className="grade-encoding-form">
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
              <span>Subject</span>
              <select value={filters.subject} onChange={(event) => setFilters({ ...filters, subject: event.target.value })}>
                <option value="">Select subject</option>
                {filteredSubjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>{subject.name}</option>
                ))}
              </select>
            </label>

            <label>
              <span>Grading period</span>
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
          <EmptyState title="Ready for grade entry" message="Load a class roster to start encoding student grades for the selected section and subject." />
        ) : null}

        {rows.length > 0 ? (
          <div className="table-card grade-encoding-table-wrapper">
            <table className="encoding-table" aria-label="Grade encoding table">
              <thead>
                <tr>
                  <th scope="col">Student ID</th>
                  <th scope="col">Student name</th>
                  <th scope="col">Quarter grade</th>
                  <th scope="col">Remarks</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td data-label="Student ID">{row.studentId}</td>
                    <td data-label="Student name">{row.studentName}</td>
                    <td data-label="Quarter grade">
                      <label className="sr-only" htmlFor={`grade-${row.id}`}>Quarter grade for {row.studentName}</label>
                      <input
                        id={`grade-${row.id}`}
                        className="grade-input"
                        type="number"
                        min="0"
                        max="100"
                        value={row.grade}
                        onChange={(event) => updateRow('grade', event.target.value, row.id)}
                        aria-invalid={Boolean(row.validationError)}
                        disabled={!canManageGrades || !row.encodedByCurrentUser}
                      />
                      {row.validationError ? <p className="field-error">{row.validationError}</p> : null}
                    </td>
                    <td data-label="Remarks">{row.remarks || 'Pass/Fail will appear automatically.'}</td>
                    <td data-label="Status">
                      <span className={`status-pill ${row.status === 'Finalized' ? 'status-pill--success' : 'status-pill--neutral'}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {rows.length > 0 ? (
          <div className="grade-encoding-actions">
            <button type="button" className="action-button action-button--secondary" onClick={() => handleSave(false)}>
              Save draft
            </button>
            <button type="button" className="action-button" onClick={() => handleSave(true)}>
              Save final
            </button>
          </div>
        ) : null}
      </section>
    </div>
  )
}

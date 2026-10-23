import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useRoleAwareAutoLoad } from '../../hooks/useRoleAwareAutoLoad'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  createAcademicRecord,
  bulkCreateAcademicRecords,
  getAcademicRecords,
  getAcademicYears,
  getEnrollments,
  getGradeLevels,
  getSections,
  getSubjects,
  getTeacherContext,
  updateAcademicRecord,
} from '../../services/academicsService'
import { getStudentById } from '../../services/studentService'
import { subscribeSubjectsUpdated, unsubscribeSubjectsUpdated } from '../../services/referenceService'

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
  const isTeacher = role === 'TEACHER'

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [subjects, setSubjects] = useState([])
  const [teacherAssignments, setTeacherAssignments] = useState([])

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

  const _lastAppliedFilters = useRef(null)
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

    const merged = { ...filters, ...nextFilters }
    const last = _lastAppliedFilters.current
    if (JSON.stringify(last) !== JSON.stringify(merged)) {
      setFilters((currentFilters) => ({ ...currentFilters, ...nextFilters }))
      _lastAppliedFilters.current = merged
    }
  }, [location.search])

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')

      try {
        const context = isTeacher ? await getTeacherContext() : null
        const teacherYears = context ? normalizeListResponse(await getAcademicYears()).items : []
        const teacherYearsById = new Map(teacherYears.map((year) => [String(year.id), year]))
        const [yearsData, levelsData, sectionsData, subjectsData] = context
          ? [
            [...new Map((context.subject_assignments || []).map((item) => {
              const year = teacherYearsById.get(String(item.academic_year))
              return [item.academic_year, { id: item.academic_year, name: year?.name || item.academic_year_name, is_active: year?.is_active === true }]
            })).values()],
            [...new Map((context.subject_assignments || []).map((item) => [item.grade_level, { id: item.grade_level, name: item.grade_level_name }])).values()],
            [...new Map((context.subject_assignments || []).map((item) => [item.section, { id: item.section, name: item.section_name, academic_year: item.academic_year, grade_level: item.grade_level }])).values()],
            [...new Map((context.subject_assignments || []).map((item) => [item.subject, {
              id: item.subject,
              name: item.subject_name,
              code: item.subject_code,
              strand: item.subject_strand,
              strand_name: item.subject_strand_name,
              official_subject_code: item.official_subject_code,
              grade_level: item.grade_level,
            }])).values()],
          ]
          : await Promise.all([getAcademicYears(), getGradeLevels(), getSections(), getSubjects()])

        if (!active) {
          return
        }

        if (context) {
          setTeacherAssignments(context.subject_assignments || [])
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
    let active = true

    async function reloadSubjects() {
      try {
        const subjectsData = await getSubjects()
        if (!active) {
          return
        }
        setSubjects(normalizeListResponse(subjectsData).items)
      } catch {
        // Keep the existing subject list if the refresh fails.
      }
    }

    function handleSubjectsUpdated() {
      reloadSubjects()
    }

    subscribeSubjectsUpdated(handleSubjectsUpdated)
    return () => {
      active = false
      unsubscribeSubjectsUpdated(handleSubjectsUpdated)
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const academicYear = params.get('academic_year') || ''
    const gradeLevel = params.get('grade_level') || ''
    const section = params.get('section') || ''
    const subject = params.get('subject') || ''

    if (academicYear || gradeLevel || section || subject) {
      loadClassData({ academicYear, gradeLevel, section, subject, gradingPeriod: filters.gradingPeriod, quarter: filters.quarter })
    }
  }, [location.search, filters.gradingPeriod, filters.quarter])

  const getDefaultGradeFilters = () => {
    if (isTeacher) {
      const assignment = teacherAssignments[0]
      if (!assignment) return null
      return {
        academicYear: String(assignment.academic_year),
        gradeLevel: String(assignment.grade_level),
        section: String(assignment.section),
        subject: String(assignment.subject),
        gradingPeriod: 'Quarter',
        quarter: '1',
      }
    }

    const defaultSection = sections[0]
    if (!defaultSection) {
      return null
    }

    const defaultSubject = subjects.find((subject) => (subject.grade_levels || [subject.grade_level]).map(String).includes(String(defaultSection.grade_level))) || subjects[0]
    if (!defaultSubject) {
      return null
    }

    return {
      academicYear: String(defaultSection.academic_year),
      gradeLevel: String(defaultSection.grade_level),
      section: String(defaultSection.id),
      subject: String(defaultSubject.id),
      gradingPeriod: 'Quarter',
      quarter: '1',
    }
  }

  useRoleAwareAutoLoad({
    enabled: isTeacher,
    loading,
    filters,
    setFilters,
    getDefaultFilters: getDefaultGradeFilters,
    onLoad: loadClassData,
    dependencies: [academicYears.length, gradeLevels.length, sections.length, subjects.length],
  })

  useEffect(() => {
    if (!isTeacher || loading || !teacherAssignments.length || filters.academicYear) return
    const nextFilters = getDefaultGradeFilters()
    if (nextFilters) {
      setFilters(nextFilters)
      loadClassData(nextFilters)
    }
  }, [isTeacher, loading, teacherAssignments.length])

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
      const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
      return matchesYear && matchesLevel
    })
  }, [filters.academicYear, filters.gradeLevel, sections])

  const filteredSubjects = useMemo(() => {
    return subjects.filter((subject) => {
      const matchesLevel = !filters.gradeLevel || (subject.grade_levels || [subject.grade_level]).map(String).includes(String(filters.gradeLevel))
      return matchesLevel
    })
  }, [filters.gradeLevel, subjects])

  const selectedTeacherAssignment = useMemo(() => {
    if (!isTeacher) return null
    return teacherAssignments.find((assignment) =>
      String(assignment.academic_year) === String(filters.academicYear)
      && String(assignment.grade_level) === String(filters.gradeLevel)
      && String(assignment.section) === String(filters.section)
      && String(assignment.subject) === String(filters.subject),
    ) || null
  }, [isTeacher, teacherAssignments, filters.academicYear, filters.gradeLevel, filters.section, filters.subject])

  const selectedAcademicYear = useMemo(() =>
    academicYears.find((year) => String(year.id) === String(filters.academicYear)) || null,
  [academicYears, filters.academicYear])

  const selectedGradeLevel = useMemo(() =>
    gradeLevels.find((grade) => String(grade.id) === String(filters.gradeLevel)) || null,
  [gradeLevels, filters.gradeLevel])

  const selectedSection = useMemo(() =>
    sections.find((section) => String(section.id) === String(filters.section)) || null,
  [sections, filters.section])

  const selectedSubject = useMemo(() =>
    subjects.find((subject) => String(subject.id) === String(filters.subject)) || null,
  [subjects, filters.subject])

  const isArchivedAcademicYear = Boolean(selectedAcademicYear && selectedAcademicYear.is_active === false)
  const canEditCurrentGrades = canManageGrades && !isArchivedAcademicYear

  function selectTeacherAssignment(assignmentId) {
    const assignment = teacherAssignments.find((entry) => String(entry.id) === String(assignmentId))
    if (!assignment) return
    const nextFilters = {
      ...filters,
      academicYear: String(assignment.academic_year),
      gradeLevel: String(assignment.grade_level),
      section: String(assignment.section),
      subject: String(assignment.subject),
    }
    setFilters(nextFilters)
    loadClassData(nextFilters)
  }

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
        getAcademicRecords({
          academic_year: nextFilters.academicYear,
          subject: nextFilters.subject,
          grading_period_type: nextFilters.gradingPeriod,
          quarter: nextFilters.gradingPeriod === 'Quarter' ? nextFilters.quarter : undefined,
          semester: nextFilters.gradingPeriod === 'Semester' ? nextFilters.quarter : undefined,
        }),
      ])

      const enrollments = normalizeListResponse(enrollmentsData).items
      const academicRecords = normalizeListResponse(recordsData).items
      const rosterSubject = subjects.find((subject) => String(subject.id) === String(nextFilters.subject))

      const recordsByEnrollment = academicRecords.reduce((accumulator, record) => {
        accumulator[record.enrollment] = record
        return accumulator
      }, {})

      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      const studentMap = studentProfiles.reduce((accumulator, student) => {
        if (student && student.id) accumulator[student.id] = student
        return accumulator
      }, {})

      const eligibleEnrollments = isTeacher && rosterSubject?.strand
        ? enrollments.filter((enrollment) => String(enrollment.strand) === String(rosterSubject.strand))
        : enrollments
      const classRows = eligibleEnrollments.map((enrollment) => {
        const record = recordsByEnrollment[enrollment.id]
        const student = studentMap[enrollment.student]
        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          recordId: record?.id || null,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          strandName: enrollment.strand_name || '',
          grade: record?.grade ?? '',
          remarks: record?.remarks || '',
          finalGrade: record?.final_grade ?? '',
          status: record?.id ? 'Saved' : 'Not encoded',
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

  async function handleSave() {
    if (!canEditCurrentGrades) {
      setError('You do not have permission to encode grades for this class.')
      return
    }

    if (isArchivedAcademicYear) {
      setError('Archived Academic Year — Read Only')
      return
    }

    const rowsToSave = rows.filter((row) => row.grade !== '' && row.grade !== null && row.grade !== undefined)
    if (!rowsToSave.length) {
      setError('There are no grades to save for this class and grading period.')
      return
    }

    const hasValidationErrors = rowsToSave.some((row) => Boolean(validateGradeValue(row.grade)))
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
      const payload = rowsToSave.map((row) => ({
        id: row.recordId || undefined,
        enrollment: row.enrollmentId,
        subject: Number(filters.subject),
        academic_year: Number(filters.academicYear),
        grading_period_type: filters.gradingPeriod,
        quarter: filters.gradingPeriod === 'Quarter' ? Number(filters.quarter) : null,
        semester: filters.gradingPeriod === 'Semester' ? Number(filters.quarter) : null,
        grade: Number(row.grade),
        remarks: row.remarks || getAutoRemarks(row.grade),
        final_grade: Number(row.grade),
      }))

      const response = await bulkCreateAcademicRecords(payload)
      const savedByEnrollment = new Map((response.results || []).map((record) => [record.enrollment, record]))

      setRows((currentRows) => currentRows.map((row) => {
        const saved = savedByEnrollment.get(row.enrollmentId)
        if (!saved) return row
        return {
          ...row,
          recordId: saved.id,
          grade: saved.grade,
          remarks: saved.remarks || getAutoRemarks(saved.grade),
          finalGrade: saved.final_grade ?? '',
          status: 'Saved',
          validationError: '',
        }
      }))

      setSuccessMessage(`Grades saved successfully. ${rowsToSave.length} grade${rowsToSave.length === 1 ? '' : 's'} updated.`)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  const encodedCount = rows.filter((row) => row.grade !== '' && row.grade !== null && row.grade !== undefined).length
  const selectedAssignmentLabel = selectedTeacherAssignment
    ? `${selectedTeacherAssignment.grade_level_name} – ${selectedTeacherAssignment.section_name} | ${selectedTeacherAssignment.subject_name}${selectedTeacherAssignment.official_subject_code ? ` (Official: ${selectedTeacherAssignment.official_subject_code})` : ''}${selectedTeacherAssignment.subject_code ? ` (System ID: ${selectedTeacherAssignment.subject_code})` : ''} | ${selectedTeacherAssignment.role}`
    : selectedGradeLevel && selectedSection && selectedSubject
      ? `${selectedGradeLevel.name} – ${selectedSection.name} | ${selectedSubject.name}`
      : 'No class selected'

  if (loading) {
    return <LoadingSpinner label="Loading grade encoding workspace..." />
  }

  return (
    <div className="page-stack grade-encoding-page">
      <PageHeader
        eyebrow="Academic workflow"
        title="Class record"
        description="Open a single authorized class, review the roster, and encode grades in a gradebook-style workflow."
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
        <div className="form-section-card">
          <div className="gradebook-context-header">
            <div className="gradebook-context-title-block">
              <p className="eyebrow">Class context</p>
              <h2>{selectedAssignmentLabel}</h2>
            </div>
            <div className="gradebook-context-metrics">
              <span>Academic Year: {selectedAcademicYear?.name || '—'}</span>
              <span>Grade: {selectedGradeLevel?.name || '—'}</span>
              <span>Section: {selectedSection?.name || '—'}</span>
              <span>Subject: {selectedSubject?.name || '—'}</span>
              <span>Teacher: {selectedTeacherAssignment?.teacher_name || user?.first_name || user?.username || '—'}</span>
            </div>
          </div>

          <div className="form-grid">
            {isTeacher ? (
              <label className="form-grid-full">
                <span>Authorized class / subject</span>
                <select value={selectedTeacherAssignment ? selectedTeacherAssignment.id : ''} onChange={(event) => selectTeacherAssignment(event.target.value)}>
                  <option value="">Select an authorized class</option>
                  {teacherAssignments.map((assignment) => (
                    <option key={assignment.id} value={assignment.id}>
                      {assignment.grade_level_name} – {assignment.section_name} | {assignment.subject_name}{assignment.official_subject_code ? ` (Official: ${assignment.official_subject_code})` : ''}{assignment.subject_code ? ` (System ID: ${assignment.subject_code})` : ''} | {assignment.role}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            {!isTeacher ? (
              <>
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
              </>
            ) : null}

            {!isTeacher ? (
              <>
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
                      <option key={subject.id} value={subject.id}>{subject.name}{subject.official_subject_code ? ` (Official: ${subject.official_subject_code})` : ''}{subject.code ? ` (System ID: ${subject.code})` : ''}</option>
                    ))}
                  </select>
                </label>
              </>
            ) : null}

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
            <button type="button" className="action-button" onClick={() => loadClassData()} disabled={loadingClass || !filters.academicYear || !filters.gradeLevel || !filters.section || !filters.subject}>
              {loadingClass ? 'Loading roster...' : 'Load roster'}
            </button>
            {isArchivedAcademicYear ? (
              <span className="status-banner status-banner--warning gradebook-readonly-banner">Archived Academic Year — Read Only</span>
            ) : null}
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}

        {rows.length === 0 ? (
          <EmptyState title="Ready for grade entry" message="Select a class and grading period to load the roster and begin encoding grades." />
        ) : null}

        {rows.length > 0 ? (
          <div className="table-card grade-encoding-table-wrapper">
            <div className="gradebook-summary-row">
              <span>Encoded: {encodedCount} / {rows.length}</span>
              <span>{rows.length - encodedCount} students remaining</span>
              {isArchivedAcademicYear ? <span className="status-pill status-pill--warning">Archived Academic Year — Read Only</span> : null}
            </div>
            <table className="encoding-table" aria-label="Gradebook table">
              <thead>
                <tr>
                  <th scope="col">#</th>
                  <th scope="col">Student</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id}>
                    <td>{index + 1}</td>
                    <td data-label="Student">
                      <div className="student-row-main">
                        <span className="student-name">{row.studentName}</span>
                        <span className="student-meta">{row.studentId}</span>
                        {row.strandName ? <span className="student-meta">Strand: {row.strandName}</span> : null}
                      </div>
                    </td>
                    <td data-label="Grade">
                      <label className="sr-only" htmlFor={`grade-${row.id}`}>Grade for {row.studentName}</label>
                      <input
                        id={`grade-${row.id}`}
                        className="grade-input"
                        type="number"
                        min="0"
                        max="100"
                        step="0.1"
                        value={row.grade}
                        onChange={(event) => updateRow('grade', event.target.value, row.id)}
                        aria-invalid={Boolean(row.validationError)}
                        disabled={!canEditCurrentGrades || !row.encodedByCurrentUser}
                        placeholder="—"
                      />
                      {row.validationError ? <p className="field-error">{row.validationError}</p> : null}
                    </td>
                    <td data-label="Status">
                      <span className={`status-pill ${row.status === 'Saved' ? 'status-pill--success' : row.grade !== '' ? 'status-pill--neutral' : 'status-pill--default'}`}>
                        {row.grade === '' ? 'Not encoded' : row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {rows.length > 0 && canEditCurrentGrades ? (
          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={handleSave}>
              Save Grades
            </button>
          </div>
        ) : null}
      </section>
    </div>
  )
}

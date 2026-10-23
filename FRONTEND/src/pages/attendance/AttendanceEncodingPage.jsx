import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useRoleAwareAutoLoad } from '../../hooks/useRoleAwareAutoLoad'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  bulkSaveAttendanceRecords,
  getAttendanceRecords,
  getSchoolDaySummary,
} from '../../services/attendanceService'
import { getAcademicYears, getEnrollments, getGradeLevels, getSections, getTeacherContext } from '../../services/academicsService'
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

async function getAllPages(fetchPage, params) {
  const itemsById = new Map()
  let page = 1
  let normalized

  do {
    normalized = normalizeListResponse(await fetchPage({ ...params, page }))
    normalized.items.forEach((item) => {
      if (item?.id != null) itemsById.set(String(item.id), item)
    })
    page += 1
  } while (normalized.next)

  return [...itemsById.values()]
}

const ATTENDANCE_OPTIONS = [
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
  { value: 'late', label: 'Late' },
  { value: 'excused', label: 'Excused' },
]

// status label helper removed (unused) to avoid lint noise

export function AttendanceEncodingPage() {
  const { user } = useAuth()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageAttendance = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN' || role === 'TEACHER'

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [teacherContext, setTeacherContext] = useState(null)
  const [filters, setFilters] = useState({
    academicYear: '',
    gradeLevel: '',
    section: '',
    attendanceDate: new Date().toISOString().slice(0, 10),
  })
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingClass, setLoadingClass] = useState(false)
  const [savingAttendance, setSavingAttendance] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [schoolDayMessage, setSchoolDayMessage] = useState('')
  const loadSequenceRef = useRef(0)

  const selectedAcademicYear = useMemo(() => {
    return academicYears.find((year) => String(year.id) === String(filters.academicYear)) || null
  }, [academicYears, filters.academicYear])

  function formatDateInput(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  function shiftAttendanceDateByDays(dateValue, days) {
    if (!dateValue) {
      return ''
    }

    const parsedDate = new Date(`${dateValue}T00:00:00`)
    parsedDate.setDate(parsedDate.getDate() + days)
    return formatDateInput(parsedDate)
  }

  function navigateAttendanceDate(days) {
    if (!filters.attendanceDate) {
      return
    }

    const nextDate = shiftAttendanceDateByDays(filters.attendanceDate, days)
    const nextFilters = {
      ...filters,
      attendanceDate: nextDate,
    }

    setFilters(nextFilters)
    loadClassData(nextFilters)
  }

  function updateAttendanceDate(newDate) {
    if (!newDate) {
      return
    }

    if (selectedAcademicYear && (newDate < selectedAcademicYear.start_date || newDate > selectedAcademicYear.end_date)) {
      setError(`The selected date must fall within the academic year ${selectedAcademicYear.name}.`)
      return
    }

    const nextFilters = {
      ...filters,
      attendanceDate: newDate,
    }

    setFilters(nextFilters)
    loadClassData(nextFilters)
  }

  const previousDayDate = shiftAttendanceDateByDays(filters.attendanceDate, -1)
  const nextDayDate = shiftAttendanceDateByDays(filters.attendanceDate, 1)
  const canNavigatePrevious = !selectedAcademicYear || !filters.attendanceDate || previousDayDate >= selectedAcademicYear.start_date
  const canNavigateNext = !selectedAcademicYear || !filters.attendanceDate || nextDayDate <= selectedAcademicYear.end_date

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')

      try {
        const context = role === 'TEACHER' ? await getTeacherContext() : null
        const [yearsData, levelsData, sectionsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
        ])

        if (!active) {
          return
        }

        if (context) setTeacherContext(context)

        const yearItems = normalizeListResponse(yearsData).items.filter((year) => year.is_active === true)
        setAcademicYears(yearItems)
        setFilters((currentFilters) => {
          if (!currentFilters.academicYear || yearItems.some((year) => String(year.id) === String(currentFilters.academicYear))) {
            return currentFilters
          }
          return { ...currentFilters, academicYear: '', gradeLevel: '', section: '' }
        })
        setGradeLevels(normalizeListResponse(levelsData).items)
        setSections(normalizeListResponse(sectionsData).items)
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

  const teacherClassOptions = useMemo(() => {
    if (!teacherContext) return []
    const options = new Map()
    const entries = [...(teacherContext.advisory_classes || []), ...(teacherContext.subject_assignments || [])]
    entries.forEach((entry) => {
      const key = `${entry.academic_year}-${entry.section}`
      const existing = options.get(key)
      options.set(key, {
        ...entry,
        role: existing ? 'Adviser and Subject Teacher' : entry.role,
      })
    })
    return [...options.values()]
  }, [teacherContext])

  const getDefaultAttendanceFilters = () => {
    if (role === 'TEACHER' && teacherClassOptions.length) {
      const assignment = teacherClassOptions[0]
      return {
        academicYear: String(assignment.academic_year),
        gradeLevel: String(assignment.grade_level),
        section: String(assignment.section),
        attendanceDate: filters.attendanceDate,
      }
    }
    const defaultSection = sections[0]
    if (!defaultSection) {
      return null
    }

    return {
      academicYear: String(defaultSection.academic_year),
      gradeLevel: String(defaultSection.grade_level),
      section: String(defaultSection.id),
      attendanceDate: filters.attendanceDate,
    }
  }

  useRoleAwareAutoLoad({
    enabled: canManageAttendance,
    loading,
    filters,
    setFilters,
    getDefaultFilters: getDefaultAttendanceFilters,
    onLoad: loadClassData,
    dependencies: [academicYears.length, gradeLevels.length, sections.length, filters.attendanceDate],
  })

  useEffect(() => {
    if (role !== 'TEACHER' || loading || !teacherClassOptions.length || filters.academicYear) return
    const nextFilters = getDefaultAttendanceFilters()
    if (nextFilters) {
      setFilters(nextFilters)
      loadClassData(nextFilters)
    }
  }, [role, loading, teacherClassOptions.length])

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
      const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
      return matchesYear && matchesLevel
    })
  }, [filters.academicYear, filters.gradeLevel, sections])

  function selectTeacherClass(value) {
    const assignment = teacherClassOptions.find((entry) => `${entry.academic_year}-${entry.section}` === value)
    if (!assignment) return
    const nextFilters = {
      ...filters,
      academicYear: String(assignment.academic_year),
      gradeLevel: String(assignment.grade_level),
      section: String(assignment.section),
    }
    setFilters(nextFilters)
    loadClassData(nextFilters)
  }

  async function loadClassData(nextFilters = filters) {
    if (!nextFilters.academicYear || !nextFilters.gradeLevel || !nextFilters.section) {
      setError('Select an academic year, grade level, and section before loading the class roster.')
      return
    }

    const requestId = loadSequenceRef.current + 1
    loadSequenceRef.current = requestId

    setLoadingClass(true)
    setError('')
    setSuccessMessage('')

    try {
      const enrollmentParams = {
        active_only: 'true',
        academic_year: nextFilters.academicYear,
        grade_level: nextFilters.gradeLevel,
        section: nextFilters.section,
        enrollment_status: 'active',
      }
      const attendanceParams = { attendance_date: nextFilters.attendanceDate }
      const [enrollments, existingRecords, schoolDaySummary] = await Promise.all([
        getAllPages(getEnrollments, enrollmentParams),
        getAllPages(getAttendanceRecords, attendanceParams),
        getSchoolDaySummary({ academic_year_id: nextFilters.academicYear, reporting_date: nextFilters.attendanceDate, today: nextFilters.attendanceDate }),
      ])

      if (requestId !== loadSequenceRef.current) {
        return
      }

      if (schoolDaySummary?.calendar_available) {
        setSchoolDayMessage(`School-day view: ${schoolDaySummary.school_days} expected school day(s) for ${schoolDaySummary.reporting_date}.`)
      } else {
        setSchoolDayMessage('No school-calendar days available for the selected academic year and date.')
      }

      const recordMap = existingRecords.reduce((accumulator, record) => {
        if (record && record.enrollment) {
          accumulator[record.enrollment] = record
        }
        return accumulator
      }, {})

      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      if (requestId !== loadSequenceRef.current) {
        return
      }

      const studentMap = studentProfiles.reduce((accumulator, student) => {
        if (student && student.id) accumulator[student.id] = student
        return accumulator
      }, {})

      const classRows = enrollments.map((enrollment) => {
        const record = recordMap[enrollment.id]
        const student = studentMap[enrollment.student]
        const classificationUnknown = Boolean(record && record.excused_absences == null)
        const attendanceStatus = classificationUnknown
          ? ''
          : record?.excused_absences > 0
            ? 'excused'
            : record?.days_present > 0
              ? 'present'
              : record?.absences > 0
                ? 'absent'
                : record?.times_tardy > 0
                  ? 'late'
                  : ''
        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          recordId: record?.id || null,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          strandName: enrollment.strand_name || '',
          status: attendanceStatus,
          originalSchoolDays: record ? Number(record.school_days ?? 0) : 1,
          originalDaysPresent: Number(record?.days_present || 0),
          originalAbsences: Number(record?.absences || 0),
          originalExcusedAbsences: record?.excused_absences == null ? null : Number(record.excused_absences),
          originalTimesTardy: Number(record?.times_tardy || 0),
          classificationUnknown,
          classificationExplicitlySelected: false,
          remarks: classificationUnknown
            ? 'Legacy excused classification is unclassified. Select Present, Absent, or Excused to classify it.'
            : record?.month ? 'Existing record loaded' : '',
          validationError: '',
        }
      })

      if (requestId !== loadSequenceRef.current) {
        return
      }

      setRows(classRows)
    } catch (err) {
      if (requestId !== loadSequenceRef.current) {
        return
      }
      setError(getApiErrorMessage(err))
      setRows([])
    } finally {
      if (requestId === loadSequenceRef.current) {
        setLoadingClass(false)
      }
    }
  }

  function updateRow(status, rowId) {
    const classificationStatus = status === 'present' || status === 'absent' || status === 'excused'
    setRows((currentRows) => currentRows.map((row) => (
      row.id === rowId ? {
        ...row,
        status,
        classificationExplicitlySelected: classificationStatus,
        remarks: row.classificationUnknown
          ? classificationStatus
            ? `Will classify as ${status}.`
            : 'Tardiness can be saved; excused classification remains unclassified.'
          : row.remarks,
        validationError: '',
      } : row
    )))
  }

  function applyBulk(status) {
    const classificationStatus = status === 'present' || status === 'absent' || status === 'excused'
    setRows((currentRows) => currentRows.map((row) => ({
      ...row,
      status,
      classificationExplicitlySelected: classificationStatus,
      remarks: row.classificationUnknown
        ? classificationStatus
          ? `Will classify as ${status}.`
          : 'Tardiness can be saved; excused classification remains unclassified.'
        : row.remarks,
      validationError: '',
    })))
  }

  async function handleSave() {
    if (!canManageAttendance) {
      setError('You do not have permission to encode attendance for this class.')
      return
    }
    if (rows.some((row) => !row.status)) {
      setError('Select an attendance status for every student before saving.')
      setRows((currentRows) => currentRows.map((row) => ({
        ...row,
        validationError: row.status ? '' : 'Select an attendance status.',
      })))
      return
    }
    if (savingAttendance || !rows.length) {
      return
    }

    setError('')
    setSuccessMessage('')
    setSavingAttendance(true)

    try {
      const payload = rows.map((row) => ({
        ...(row.recordId ? { id: row.recordId } : {}),
        enrollment: row.enrollmentId,
        attendance_date: filters.attendanceDate,
        month: filters.attendanceDate,
        school_days: row.originalSchoolDays,
        days_present: row.status === 'late' ? row.originalDaysPresent : row.status === 'present' ? 1 : 0,
        absences: row.status === 'late' ? row.originalAbsences : row.status === 'absent' ? 1 : 0,
        excused_absences: row.status === 'late'
          ? (row.recordId ? row.originalExcusedAbsences : 0)
          : row.status === 'excused' ? 1 : 0,
        times_tardy: row.status === 'late'
          ? Math.max(row.originalTimesTardy, 1)
          : row.originalTimesTardy,
      }))
      const response = await bulkSaveAttendanceRecords(payload)
      const savedByEnrollment = new Map(response.results.map((record) => [
        String(record.enrollment),
        record,
      ]))

      setRows((currentRows) => currentRows.map((row) => {
        const saved = savedByEnrollment.get(String(row.enrollmentId))
        return saved ? {
          ...row,
          recordId: saved.id,
          originalSchoolDays: Number(saved.school_days ?? 0),
          originalDaysPresent: Number(saved.days_present || 0),
          originalAbsences: Number(saved.absences || 0),
          originalExcusedAbsences: saved.excused_absences == null ? null : Number(saved.excused_absences),
          originalTimesTardy: Number(saved.times_tardy || 0),
          classificationUnknown: saved.excused_absences == null,
          classificationExplicitlySelected: false,
          remarks: saved.excused_absences == null
            ? 'Tardiness saved; excused classification remains unclassified.'
            : 'Saved',
        } : row
      }))
      setSuccessMessage(`Attendance saved successfully for ${response.count} student${response.count === 1 ? '' : 's'}.`)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSavingAttendance(false)
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading attendance workspace..." />
  }

  return (
    <div className="page-stack attendance-encoding-page">
      <PageHeader
        eyebrow="Attendance workflow"
        title="Attendance encoding"
        description="Open the assigned class, mark the student status for today, and save the roster in one guided flow."
        actions={(
          <Link className="action-button action-button--secondary" to="/attendance">
            Back to attendance
          </Link>
        )}
      />

      {!canManageAttendance ? (
        <div className="status-banner status-banner--warning">You do not currently have permission to encode attendance.</div>
      ) : null}

      <section className="students-panel attendance-encoding-panel">
        <div className="form-section-card">
          <div className="workflow-step">Select the class and date you are recording.</div>
          <div className="workflow-step">Mark attendance for students in the roster.</div>
          <div className="workflow-step">Save the attendance entry when the list is complete.</div>
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
            <label>
              <span>Academic year</span>
              <select value={filters.academicYear} onChange={(event) => setFilters({ ...filters, academicYear: event.target.value })}>
                <option value="">Select academic year</option>
                {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
              </select>
            </label>
            <label>
              <span>Grade level</span>
              <select value={filters.gradeLevel} onChange={(event) => setFilters({ ...filters, gradeLevel: event.target.value })}>
                <option value="">Select grade level</option>
                {gradeLevels.map((gradeLevel) => <option key={gradeLevel.id} value={gradeLevel.id}>{gradeLevel.name}</option>)}
              </select>
            </label>
              </>
            ) : null}
            {role !== 'TEACHER' ? (
              <label>
                <span>Section</span>
                <select value={filters.section} onChange={(event) => setFilters({ ...filters, section: event.target.value })}>
                  <option value="">Select section</option>
                  {filteredSections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
                </select>
              </label>
            ) : null}
            <div className="date-navigation-group">
              <button
                type="button"
                className="action-button action-button--secondary"
                aria-label="Previous Day"
                disabled={!canNavigatePrevious}
                onClick={() => navigateAttendanceDate(-1)}
              >
                ← Previous Day
              </button>
              <label className="date-selector-label">
                <span>Date</span>
                <input type="date" value={filters.attendanceDate} onChange={(event) => updateAttendanceDate(event.target.value)} />
              </label>
              <button
                type="button"
                className="action-button action-button--secondary"
                aria-label="Next Day"
                disabled={!canNavigateNext}
                onClick={() => navigateAttendanceDate(1)}
              >
                Next Day →
              </button>
            </div>
          </div>

          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={loadClassData} disabled={loadingClass}>
              {loadingClass ? 'Loading...' : 'Load class roster'}
            </button>
            {rows.length > 0 ? (
              <>
                <button type="button" className="action-button action-button--secondary" onClick={() => applyBulk('present')}>Mark all present</button>
                <button type="button" className="action-button action-button--secondary" onClick={() => applyBulk('absent')}>Mark all absent</button>
                <button type="button" className="action-button action-button--secondary" onClick={() => applyBulk('')}>Clear attendance</button>
              </>
            ) : null}
          </div>
        </div>

        {schoolDayMessage ? <div className="status-banner status-banner--info">{schoolDayMessage}</div> : null}
        {error ? <ErrorBanner message={error} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}

        {rows.length === 0 ? (
          <EmptyState title="Ready for attendance entry" message="Load a class roster to start recording attendance for the selected date." />
        ) : null}

        {rows.length > 0 ? (
          <div className="table-card grade-encoding-table-wrapper">
            <table className="encoding-table" aria-label="Attendance encoding table">
              <thead>
                <tr>
                  <th scope="col">Student ID</th>
                  <th scope="col">Student name / strand</th>
                  <th scope="col">Attendance status</th>
                  <th scope="col">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td data-label="Student ID">{row.studentId}</td>
                    <td data-label="Student name / strand">{row.studentName}{row.strandName ? <small>Strand: {row.strandName}</small> : null}</td>
                    <td data-label="Attendance status">
                      <select value={row.status} onChange={(event) => updateRow(event.target.value, row.id)} aria-label={`Attendance status for ${row.studentName}`}>
                        <option value="">Select status</option>
                        {ATTENDANCE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                      </select>
                    </td>
                    <td data-label="Remarks">
                      {row.validationError || (row.classificationUnknown && !row.classificationExplicitlySelected
                        ? row.remarks
                        : row.classificationUnknown && row.status === 'late'
                          ? 'Tardiness can be saved; excused classification remains unclassified.'
                          : row.remarks || 'Select a status to encode attendance.')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {rows.length > 0 ? (
          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={handleSave} disabled={savingAttendance}>
              {savingAttendance ? 'Saving attendance...' : 'Save attendance'}
            </button>
          </div>
        ) : null}
      </section>
    </div>
  )
}

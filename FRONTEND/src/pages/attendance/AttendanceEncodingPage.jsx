import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  createAttendanceRecord,
  getAttendanceRecords,
  updateAttendanceRecord,
} from '../../services/attendanceService'
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

const ATTENDANCE_OPTIONS = [
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
  { value: 'late', label: 'Late' },
  { value: 'excused', label: 'Excused' },
]

function getStatusLabel(status) {
  return ATTENDANCE_OPTIONS.find((entry) => entry.value === status)?.label || status || 'Pending'
}

export function AttendanceEncodingPage() {
  const { user } = useAuth()
  const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
  const canManageAttendance = role === 'SUPER_ADMIN' || role === 'SCHOOL_ADMIN' || role === 'TEACHER'

  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [filters, setFilters] = useState({
    academicYear: '',
    gradeLevel: '',
    section: '',
    attendanceDate: new Date().toISOString().slice(0, 10),
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
        const [yearsData, levelsData, sectionsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
        ])

        if (!active) {
          return
        }

        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(levelsData).items)
        setSections(normalizeListResponse(sectionsData).items)
      } catch (err) {
        if (!active) {
          return
        }
        setError(getApiErrorMessage(err))
      } finally {
        if (!active) {
          return
        }
        setLoading(false)
      }
    }

    loadReferences()
    return () => {
      active = false
    }
  }, [])

  const filteredSections = useMemo(() => {
    return sections.filter((section) => {
      const matchesYear = !filters.academicYear || String(section.academic_year) === String(filters.academicYear)
      const matchesLevel = !filters.gradeLevel || String(section.grade_level) === String(filters.gradeLevel)
      return matchesYear && matchesLevel
    })
  }, [filters.academicYear, filters.gradeLevel, sections])

  async function loadClassData() {
    if (!filters.academicYear || !filters.gradeLevel || !filters.section) {
      setError('Select an academic year, grade level, and section before loading the class roster.')
      return
    }

    setLoadingClass(true)
    setError('')
    setSuccessMessage('')

    try {
      const enrollmentsData = await getEnrollments({ academic_year: filters.academicYear, grade_level: filters.gradeLevel, section: filters.section, enrollment_status: 'active' })
      const attendanceData = await getAttendanceRecords({ month: filters.attendanceDate, enrollment__student: undefined })

      const enrollments = normalizeListResponse(enrollmentsData).items
      const existingRecords = normalizeListResponse(attendanceData).items
      const recordMap = existingRecords.reduce((accumulator, record) => {
        if (record.enrollment) {
          accumulator[record.enrollment] = record
        }
        return accumulator
      }, {})

      const studentProfiles = await Promise.all(enrollments.map((enrollment) => getStudentById(enrollment.student)))
      const studentMap = studentProfiles.reduce((accumulator, student) => {
        accumulator[student.id] = student
        return accumulator
      }, {})

      const classRows = enrollments.map((enrollment) => {
        const record = recordMap[enrollment.id]
        const student = studentMap[enrollment.student]
        const attendanceStatus = record?.days_present > 0 ? 'present' : record?.absences > 0 ? 'absent' : ''
        return {
          id: enrollment.id,
          enrollmentId: enrollment.id,
          recordId: record?.id || null,
          studentId: student?.lrn || enrollment.student,
          studentName: student ? `${student.first_name || ''} ${student.last_name || ''}`.trim() : `Student ${enrollment.student}`,
          status: attendanceStatus,
          remarks: record?.month ? 'Existing record loaded' : '',
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

  function updateRow(status, rowId) {
    setRows((currentRows) => currentRows.map((row) => (
      row.id === rowId ? { ...row, status, validationError: '' } : row
    )))
  }

  function applyBulk(status) {
    setRows((currentRows) => currentRows.map((row) => ({ ...row, status })))
  }

  async function handleSave() {
    if (!canManageAttendance) {
      setError('You do not have permission to encode attendance for this class.')
      return
    }

    setError('')
    setSuccessMessage('')

    try {
      for (const row of rows) {
        const payload = {
          enrollment: row.enrollmentId,
          month: filters.attendanceDate,
          school_days: 1,
          days_present: row.status === 'present' ? 1 : 0,
          absences: row.status === 'absent' ? 1 : 0,
          times_tardy: row.status === 'late' ? 1 : 0,
        }

        if (row.recordId) {
          await updateAttendanceRecord(row.recordId, payload)
        } else {
          await createAttendanceRecord(payload)
        }
      }

      setSuccessMessage('Attendance saved successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  if (loading) {
    return <LoadingSpinner label="Loading attendance workspace..." />
  }

  return (
    <div className="page-stack attendance-encoding-page">
      <PageHeader
        eyebrow="Attendance"
        title="Attendance encoding"
        description="Select a class, mark the attendance status for each student, and save the roster for the selected date."
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
        <div className="grade-encoding-form">
          <div className="form-grid">
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
            <label>
              <span>Section</span>
              <select value={filters.section} onChange={(event) => setFilters({ ...filters, section: event.target.value })}>
                <option value="">Select section</option>
                {filteredSections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
              </select>
            </label>
            <label>
              <span>Date</span>
              <input type="date" value={filters.attendanceDate} onChange={(event) => setFilters({ ...filters, attendanceDate: event.target.value })} />
            </label>
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
                  <th scope="col">Student name</th>
                  <th scope="col">Attendance status</th>
                  <th scope="col">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td data-label="Student ID">{row.studentId}</td>
                    <td data-label="Student name">{row.studentName}</td>
                    <td data-label="Attendance status">
                      <select value={row.status} onChange={(event) => updateRow(event.target.value, row.id)} aria-label={`Attendance status for ${row.studentName}`}>
                        <option value="">Select status</option>
                        {ATTENDANCE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                      </select>
                    </td>
                    <td data-label="Remarks">{row.remarks || 'Select a status to encode attendance.'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {rows.length > 0 ? (
          <div className="grade-encoding-actions">
            <button type="button" className="action-button" onClick={handleSave}>Save attendance</button>
          </div>
        ) : null}
      </section>
    </div>
  )
}

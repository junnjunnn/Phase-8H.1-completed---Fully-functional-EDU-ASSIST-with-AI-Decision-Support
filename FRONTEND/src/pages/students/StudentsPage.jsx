import { MagnifyingGlassIcon, PlusIcon, UserPlusIcon } from '@heroicons/react/24/outline'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import { createEnrollment, createStudent, getAcademicYears, getGradeLevels, getSections, getStudents } from '../../services/studentService'

function statusBadgeClass(status) {
  const normalized = (status || '').toLowerCase()
  if (normalized.includes('active')) {
    return 'status-pill status-pill--success'
  }
  if (normalized.includes('inactive') || normalized.includes('suspended')) {
    return 'status-pill status-pill--warning'
  }
  if (normalized.includes('graduated') || normalized.includes('completed')) {
    return 'status-pill status-pill--neutral'
  }
  return 'status-pill status-pill--default'
}

export function StudentsPage() {
  const { user } = useAuth()
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState('last_name')
  const [sortDirection, setSortDirection] = useState('asc')
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null })
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [registerForm, setRegisterForm] = useState({
    lrn: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: '',
    birth_date: '',
    student_status: 'active',
    academic_year: '',
    grade_level: '',
    section: '',
    enrollment_status: 'active',
  })
  const [registerErrors, setRegisterErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [registerMessage, setRegisterMessage] = useState('')
  const [selectedYear, setSelectedYear] = useState('')
  const [selectedGrade, setSelectedGrade] = useState('')
  const canManageStudents = user?.role_name === 'SUPER_ADMIN' || user?.role_name === 'SCHOOL_ADMIN'

  const canCreateStudent = canManageStudents
  const canEnrollStudent = canManageStudents

  const sortedStudents = useMemo(() => {
    const rows = [...students]
    rows.sort((a, b) => {
      const left = a[sortField] ?? ''
      const right = b[sortField] ?? ''
      const comparison = String(left).localeCompare(String(right), undefined, { sensitivity: 'base' })
      return sortDirection === 'asc' ? comparison : -comparison
    })
    return rows
  }, [students, sortField, sortDirection])

  useEffect(() => {
    let active = true

    async function loadStudents() {
      setLoading(true)
      setError('')
      try {
        const data = await getStudents({ search })
        if (!active) {
          return
        }
        setStudents(data.results || [])
        setPagination({ count: data.count || 0, next: data.next, previous: data.previous })
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

    loadStudents()
    return () => {
      active = false
    }
  }, [search])

  useEffect(() => {
    async function loadReferenceData() {
      try {
        const [years, grades, allSections] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
        ])
        setAcademicYears(years.results || years || [])
        setGradeLevels(grades.results || grades || [])
        setSections(allSections.results || allSections || [])
      } catch (err) {
        console.warn('Unable to load student reference data', err)
      }
    }

    loadReferenceData()
  }, [])

  function toggleSort(field) {
    if (sortField === field) {
      setSortDirection((value) => (value === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortField(field)
    setSortDirection('asc')
  }

  function updateRegisterField(event) {
    const { name, value } = event.target
    setRegisterForm((current) => ({ ...current, [name]: value }))
    setRegisterErrors((current) => ({ ...current, [name]: '' }))

    if (name === 'academic_year') {
      setSelectedYear(value)
      setRegisterForm((current) => ({ ...current, grade_level: '', section: '' }))
    }
    if (name === 'grade_level') {
      setSelectedGrade(value)
      setRegisterForm((current) => ({ ...current, section: '' }))
    }
  }

  async function handleRegisterSubmit(event) {
    event.preventDefault()
    setRegisterMessage('')
    setRegisterErrors({})
    setSubmitting(true)

    const validationErrors = {}
    if (!registerForm.lrn.trim()) validationErrors.lrn = 'Student ID is required.'
    if (!registerForm.first_name.trim()) validationErrors.first_name = 'First name is required.'
    if (!registerForm.last_name.trim()) validationErrors.last_name = 'Last name is required.'
    if (!registerForm.academic_year) validationErrors.academic_year = 'Academic year is required.'
    if (!registerForm.grade_level) validationErrors.grade_level = 'Grade level is required.'
    if (!registerForm.section) validationErrors.section = 'Section is required.'

    if (Object.keys(validationErrors).length) {
      setRegisterErrors(validationErrors)
      setSubmitting(false)
      return
    }

    try {
      const student = await createStudent({
        lrn: registerForm.lrn.trim(),
        first_name: registerForm.first_name.trim(),
        middle_name: registerForm.middle_name.trim(),
        last_name: registerForm.last_name.trim(),
        gender: registerForm.gender.trim(),
        birth_date: registerForm.birth_date || null,
        student_status: registerForm.student_status || 'active',
      })

      await createEnrollment({
        student: student.id,
        academic_year: registerForm.academic_year,
        grade_level: registerForm.grade_level,
        section: registerForm.section,
        enrollment_status: registerForm.enrollment_status || 'active',
        enrollment_date: new Date().toISOString().slice(0, 10),
      })

      setRegisterMessage('Student registered and enrolled successfully.')
      setRegisterForm({
        lrn: '',
        first_name: '',
        middle_name: '',
        last_name: '',
        gender: '',
        birth_date: '',
        student_status: 'active',
        academic_year: '',
        grade_level: '',
        section: '',
        enrollment_status: 'active',
      })
      setShowRegisterModal(false)
      setError('')
      const refreshed = await getStudents({ search })
      setStudents(refreshed.results || [])
      setPagination({ count: refreshed.count || 0, next: refreshed.next, previous: refreshed.previous })
    } catch (err) {
      const apiMessage = getApiErrorMessage(err)
      if (apiMessage && apiMessage.includes('already exists')) {
        setRegisterErrors({ lrn: apiMessage })
      } else if (apiMessage && apiMessage.includes('section')) {
        setRegisterErrors({ section: apiMessage })
      } else {
        setRegisterErrors({ form: apiMessage })
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-stack students-page">
      <PageHeader eyebrow="Students" title="Student management" description="Browse student records from the backend." actions={canCreateStudent ? (
        <button type="button" className="action-button action-button--primary" onClick={() => setShowRegisterModal(true)}>
          <PlusIcon className="icon" /> Register student
        </button>
      ) : null} />

      <div className="panel-card students-panel">
        <div className="students-toolbar">
          <div className="search-input-group">
            <span className="search-icon" aria-hidden="true"><MagnifyingGlassIcon className="icon" /></span>
            <input
              aria-label="Search students"
              placeholder="Search by name or Student ID"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="students-meta">
            <p>{pagination.count} student{pagination.count === 1 ? '' : 's'} found</p>
          </div>
        </div>

        {error ? <ErrorBanner message={error} /> : null}
        {registerMessage ? <div className="status-banner status-banner--success">{registerMessage}</div> : null}
        {loading ? (
          <div className="students-skeleton-grid">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="students-skeleton-card" />
            ))}
          </div>
        ) : null}

        {!loading && !error && students.length === 0 ? (
          <EmptyState
            title={search ? 'No students match your search' : 'No students available'}
            message={search ? 'Try another name, LRN, or clear the search filter.' : 'There are no student records available in the system right now.'}
          />
        ) : null}

        {!loading && !error && students.length > 0 ? (
          <div className="students-table-wrapper">
            <table className="students-table">
              <thead>
                <tr>
                  <th scope="col"><button type="button" className="sort-button" onClick={() => toggleSort('last_name')}>Name</button></th>
                  <th scope="col"><button type="button" className="sort-button" onClick={() => toggleSort('lrn')}>Student ID</button></th>
                  <th scope="col">Grade/Section</th>
                  <th scope="col">School Year</th>
                  <th scope="col"><button type="button" className="sort-button" onClick={() => toggleSort('student_status')}>Status</button></th>
                  <th scope="col" className="sticky-column">Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedStudents.map((student) => (
                  <tr key={student.id}>
                    <td data-label="Name">
                      <div className="student-row-main">
                        <span className="student-name">{`${student.first_name || ''} ${student.last_name || ''}`.trim() || 'Unknown student'}</span>
                        <span className="student-meta">Grade {student.grade_level || '—'} · Section {student.section || '—'}</span>
                      </div>
                    </td>
                    <td data-label="Student ID">{student.lrn || '—'}</td>
                    <td data-label="Grade/Section">{student.current_enrollment?.grade_level ? `${student.current_enrollment.grade_level} · ${student.current_enrollment.section || '—'}` : '—'}</td>
                    <td data-label="School Year">{student.current_enrollment?.academic_year || '—'}</td>
                    <td data-label="Status">
                      <span className={statusBadgeClass(student.student_status)}>{student.student_status || 'Unknown'}</span>
                    </td>
                    <td className="action-cell" data-label="Action">
                      <Link
                        className="action-button action-button--primary"
                        to={`/students/${student.id}`}
                        aria-label={`View details for ${student.first_name || ''} ${student.last_name || ''}`.trim()}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {showRegisterModal && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShowRegisterModal(false)}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="register-student-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Student registration</p>
                <h2 id="register-student-title">Register a student</h2>
              </div>
              <button type="button" className="icon-button" aria-label="Close registration form" onClick={() => setShowRegisterModal(false)}>
                ×
              </button>
            </div>

            <form className="registration-form" onSubmit={handleRegisterSubmit}>
              {registerErrors.form ? <ErrorBanner message={registerErrors.form} /> : null}
              <div className="form-grid">
                <label>
                  <span>Student ID</span>
                  <input name="lrn" value={registerForm.lrn} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.lrn)} />
                  {registerErrors.lrn ? <small className="field-error">{registerErrors.lrn}</small> : null}
                </label>
                <label>
                  <span>First name</span>
                  <input name="first_name" value={registerForm.first_name} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.first_name)} />
                  {registerErrors.first_name ? <small className="field-error">{registerErrors.first_name}</small> : null}
                </label>
                <label>
                  <span>Middle name</span>
                  <input name="middle_name" value={registerForm.middle_name} onChange={updateRegisterField} />
                </label>
                <label>
                  <span>Last name</span>
                  <input name="last_name" value={registerForm.last_name} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.last_name)} />
                  {registerErrors.last_name ? <small className="field-error">{registerErrors.last_name}</small> : null}
                </label>
                <label>
                  <span>Sex</span>
                  <select name="gender" value={registerForm.gender} onChange={updateRegisterField}>
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </label>
                <label>
                  <span>Date of birth</span>
                  <input type="date" name="birth_date" value={registerForm.birth_date} onChange={updateRegisterField} />
                </label>
                <label>
                  <span>Academic year</span>
                  <select name="academic_year" value={registerForm.academic_year} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.academic_year)}>
                    <option value="">Select</option>
                    {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
                  </select>
                  {registerErrors.academic_year ? <small className="field-error">{registerErrors.academic_year}</small> : null}
                </label>
                <label>
                  <span>Grade level</span>
                  <select name="grade_level" value={registerForm.grade_level} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.grade_level)}>
                    <option value="">Select</option>
                    {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
                  </select>
                  {registerErrors.grade_level ? <small className="field-error">{registerErrors.grade_level}</small> : null}
                </label>
                <label>
                  <span>Section</span>
                  <select name="section" value={registerForm.section} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.section)}>
                    <option value="">Select</option>
                    {sections.filter((section) => {
                      const matchesYear = !selectedYear || String(section.academic_year) === String(selectedYear) || String(section.academic_year_id || section.academic_year) === String(selectedYear)
                      const matchesGrade = !selectedGrade || String(section.grade_level) === String(selectedGrade) || String(section.grade_level_id || section.grade_level) === String(selectedGrade)
                      return matchesYear && matchesGrade
                    }).map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
                  </select>
                  {registerErrors.section ? <small className="field-error">{registerErrors.section}</small> : null}
                </label>
                <label>
                  <span>Status</span>
                  <select name="enrollment_status" value={registerForm.enrollment_status} onChange={updateRegisterField}>
                    <option value="active">Enrolled</option>
                    <option value="transferred">Transferred</option>
                    <option value="inactive">Inactive</option>
                    <option value="graduated">Graduated</option>
                  </select>
                </label>
              </div>

              <div className="modal-actions">
                <button type="button" className="action-button action-button--neutral" onClick={() => setShowRegisterModal(false)}>Cancel</button>
                <button type="submit" className="action-button action-button--primary" disabled={submitting}>
                  {submitting ? <LoadingSpinner label="Saving..." /> : <><UserPlusIcon className="icon" /> Register student</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

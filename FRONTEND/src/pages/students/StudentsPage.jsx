import { MagnifyingGlassIcon, PlusIcon, UserPlusIcon } from '@heroicons/react/24/outline'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import { createEnrollment, createStudent, getAcademicYears, getGradeLevels, getSections, getStudents, updateStudent } from '../../services/studentService'

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

function getSectionLabel(section) {
  const capacity = Number(section.capacity || 0)
  const studentCount = Number(section.student_count || 0)
  const occupancy = capacity > 0 ? ` · ${studentCount}/${capacity}` : ''
  return `${section.name}${occupancy}`
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
  const [registrationStep, setRegistrationStep] = useState(1)
  const [registerForm, setRegisterForm] = useState({
    lrn: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: '',
    birth_date: '',
    student_status: 'active',
    student_type: 'Continuing',
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
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [editForm, setEditForm] = useState({ lrn: '', first_name: '', middle_name: '', last_name: '', gender: '', birth_date: '', student_status: 'active' })
  const [editErrors, setEditErrors] = useState({})
  const [editSaving, setEditSaving] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState(null)
  const canManageStudents = user?.role_name === 'SUPER_ADMIN' || user?.role_name === 'SCHOOL_ADMIN'

  const canCreateStudent = canManageStudents

  function resetRegisterForm() {
    setRegisterForm({
      lrn: '',
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: '',
      birth_date: '',
      student_status: 'active',
      student_type: 'Continuing',
      academic_year: '',
      grade_level: '',
      section: '',
      enrollment_status: 'active',
    })
    setRegisterErrors({})
    setSelectedYear('')
    setSelectedGrade('')
    setRegistrationStep(1)
  }

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

  function openEditModal(student) {
    setSelectedStudent(student)
    setEditForm({
      lrn: student.lrn || '',
      first_name: student.first_name || '',
      middle_name: student.middle_name || '',
      last_name: student.last_name || '',
      gender: student.gender || '',
      birth_date: student.birth_date || '',
      student_status: student.student_status || 'active',
    })
    setEditErrors({})
    setEditModalOpen(true)
  }

  async function handleEditSubmit(event) {
    event.preventDefault()
    setEditErrors({})
    setEditSaving(true)

    try {
      await updateStudent(selectedStudent.id, {
        lrn: editForm.lrn.trim(),
        first_name: editForm.first_name.trim(),
        middle_name: editForm.middle_name.trim(),
        last_name: editForm.last_name.trim(),
        gender: editForm.gender.trim(),
        birth_date: editForm.birth_date || null,
        student_status: editForm.student_status,
      })
      const refreshed = await getStudents({ search })
      setStudents(refreshed.results || [])
      setPagination({ count: refreshed.count || 0, next: refreshed.next, previous: refreshed.previous })
      setEditModalOpen(false)
      setSelectedStudent(null)
    } catch (err) {
      setEditErrors({ form: getApiErrorMessage(err) })
    } finally {
      setEditSaving(false)
    }
  }

  async function handleStatusAction(student, nextStatus) {
    setPendingAction({ student, nextStatus })
    setConfirmOpen(true)
  }

  async function confirmStatusChange() {
    if (!pendingAction) return
    try {
      await updateStudent(pendingAction.student.id, { student_status: pendingAction.nextStatus })
      const refreshed = await getStudents({ search })
      setStudents(refreshed.results || [])
      setPagination({ count: refreshed.count || 0, next: refreshed.next, previous: refreshed.previous })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setConfirmOpen(false)
      setPendingAction(null)
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
        student_type: 'Continuing',
        academic_year: '',
        grade_level: '',
        section: '',
        enrollment_status: 'active',
      })
      setSelectedYear('')
      setSelectedGrade('')
      setRegistrationStep(1)
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
      <PageHeader eyebrow="Student management" title="Students" description="Manage the current learner roster and move quickly into enrollment, profile review, or student status updates." actions={canCreateStudent ? (
        <button type="button" className="action-button action-button--primary" onClick={() => { resetRegisterForm(); setShowRegisterModal(true) }}>
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
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <Link
                          className="action-button action-button--primary"
                          to={`/students/${student.id}`}
                          aria-label={`View details for ${student.first_name || ''} ${student.last_name || ''}`.trim()}
                        >
                          View
                        </Link>
                        {canManageStudents ? (
                          <>
                            <button type="button" className="action-button action-button--neutral" onClick={() => openEditModal(student)}>Edit</button>
                            <button type="button" className="action-button action-button--neutral" onClick={() => handleStatusAction(student, student.student_status === 'archived' ? 'active' : 'archived')}>{student.student_status === 'archived' ? 'Restore' : 'Archive'}</button>
                          </>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title={pendingAction?.nextStatus === 'archived' ? 'Archive student' : 'Restore student'}
        message={pendingAction ? `Change the student status to ${pendingAction.nextStatus === 'archived' ? 'archived' : 'active'}?` : ''}
        confirmLabel={pendingAction?.nextStatus === 'archived' ? 'Archive' : 'Restore'}
        onConfirm={confirmStatusChange}
        onCancel={() => { setConfirmOpen(false); setPendingAction(null) }}
      />

      {editModalOpen && selectedStudent ? (
        <div className="modal-backdrop" role="presentation" onClick={() => setEditModalOpen(false)}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="edit-student-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Student details</p>
                <h2 id="edit-student-title">Edit student</h2>
              </div>
              <button type="button" className="icon-button" aria-label="Close edit form" onClick={() => setEditModalOpen(false)}>×</button>
            </div>
            <form className="registration-form" onSubmit={handleEditSubmit}>
              {editErrors.form ? <ErrorBanner message={editErrors.form} /> : null}
              <div className="form-grid">
                <label>
                  <span>Student ID</span>
                  <input value={editForm.lrn} onChange={(event) => setEditForm({ ...editForm, lrn: event.target.value })} />
                </label>
                <label>
                  <span>First name</span>
                  <input value={editForm.first_name} onChange={(event) => setEditForm({ ...editForm, first_name: event.target.value })} required />
                </label>
                <label>
                  <span>Middle name</span>
                  <input value={editForm.middle_name} onChange={(event) => setEditForm({ ...editForm, middle_name: event.target.value })} />
                </label>
                <label>
                  <span>Last name</span>
                  <input value={editForm.last_name} onChange={(event) => setEditForm({ ...editForm, last_name: event.target.value })} required />
                </label>
                <label>
                  <span>Gender</span>
                  <input value={editForm.gender} onChange={(event) => setEditForm({ ...editForm, gender: event.target.value })} />
                </label>
                <label>
                  <span>Date of birth</span>
                  <input type="date" value={editForm.birth_date} onChange={(event) => setEditForm({ ...editForm, birth_date: event.target.value })} />
                </label>
                <label>
                  <span>Status</span>
                  <select value={editForm.student_status} onChange={(event) => setEditForm({ ...editForm, student_status: event.target.value })}>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="archived">Archived</option>
                    <option value="graduated">Graduated</option>
                    <option value="transferred">Transferred</option>
                  </select>
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="action-button action-button--neutral" onClick={() => setEditModalOpen(false)}>Cancel</button>
                <button type="submit" className="action-button action-button--primary" disabled={editSaving}>{editSaving ? 'Saving...' : 'Save changes'}</button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

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
              <div className="form-stepper" aria-label="Registration steps">
                <button type="button" className={`step-pill ${registrationStep === 1 ? 'step-pill--active' : ''}`} onClick={() => setRegistrationStep(1)}>1. Student profile</button>
                <button type="button" className={`step-pill ${registrationStep === 2 ? 'step-pill--active' : ''}`} onClick={() => setRegistrationStep(2)}>2. Enrollment details</button>
              </div>
              {registrationStep === 1 ? (
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
                </div>
              ) : (
                <div className="form-grid">
                  <label>
                    <span>Enrollment type</span>
                    <select name="student_type" value={registerForm.student_type} onChange={updateRegisterField}>
                      <option value="Continuing">Continuing</option>
                      <option value="New">New</option>
                      <option value="Transferee">Transferee</option>
                    </select>
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
                      }).map((section) => <option key={section.id} value={section.id}>{getSectionLabel(section)}</option>)}
                    </select>
                    {selectedYear && selectedGrade && sections.filter((section) => {
                      const matchesYear = !selectedYear || String(section.academic_year) === String(selectedYear) || String(section.academic_year_id || section.academic_year) === String(selectedYear)
                      const matchesGrade = !selectedGrade || String(section.grade_level) === String(selectedGrade) || String(section.grade_level_id || section.grade_level) === String(selectedGrade)
                      return matchesYear && matchesGrade
                    }).length === 0 ? <small className="field-hint">No sections are available for the selected year and grade yet.</small> : null}
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
                  <div className="detail-card form-grid-full">
                    <p className="eyebrow">Enrollment summary</p>
                    <p>{registerForm.student_type} student · {academicYears.find((year) => String(year.id) === String(registerForm.academic_year))?.name || 'Academic year pending'} · {gradeLevels.find((grade) => String(grade.id) === String(registerForm.grade_level))?.name || 'Grade pending'}</p>
                  </div>
                </div>
              )}

              <div className="modal-actions">
                <button type="button" className="action-button action-button--neutral" onClick={() => { setShowRegisterModal(false); resetRegisterForm() }}>Cancel</button>
                {registrationStep === 2 ? (
                  <button type="button" className="action-button action-button--neutral" onClick={() => setRegistrationStep(1)}>Back</button>
                ) : null}
                {registrationStep === 1 ? (
                  <button type="button" className="action-button action-button--primary" onClick={() => setRegistrationStep(2)}>Continue</button>
                ) : (
                  <button type="submit" className="action-button action-button--primary" disabled={submitting}>
                    {submitting ? <LoadingSpinner label="Saving..." /> : <><UserPlusIcon className="icon" /> Register student</>}
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

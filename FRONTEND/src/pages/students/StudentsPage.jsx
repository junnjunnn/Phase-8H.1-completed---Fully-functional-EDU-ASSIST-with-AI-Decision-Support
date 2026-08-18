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
  const [registerForm, setRegisterForm] = useState({
    lrn: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    suffix: '',
    gender: '',
    birth_date: '',
    address: '',
    guardian_name: '',
    parent_contact: '',
    email: '',
    student_status: 'active',
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
  const currentRole = (user?.role_name || user?.role || user?.profile?.role_name || 'NONE').toUpperCase()
  const canManageStudents = ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'REGISTRAR'].includes(currentRole)

  const canCreateStudent = canManageStudents

  function resetRegisterForm() {
    setRegisterForm({
      lrn: '',
      first_name: '',
      middle_name: '',
      last_name: '',
      suffix: '',
      gender: '',
      birth_date: '',
      address: '',
      guardian_name: '',
      parent_contact: '',
      email: '',
      student_status: 'active',
    })
    setRegisterErrors({})
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
    if (!registerForm.gender.trim()) validationErrors.gender = 'Sex is required.'
    if (!registerForm.birth_date) validationErrors.birth_date = 'Birthdate is required.'
    if (!registerForm.address.trim()) validationErrors.address = 'Address is required.'
    if (!registerForm.guardian_name.trim()) validationErrors.guardian_name = 'Guardian is required.'
    if (!registerForm.parent_contact.trim()) validationErrors.parent_contact = 'Parent contact is required.'

    if (Object.keys(validationErrors).length) {
      setRegisterErrors(validationErrors)
      setSubmitting(false)
      return
    }

    try {
      await createStudent({
        lrn: registerForm.lrn.trim(),
        first_name: registerForm.first_name.trim(),
        middle_name: registerForm.middle_name.trim(),
        last_name: registerForm.last_name.trim(),
        suffix: registerForm.suffix.trim(),
        gender: registerForm.gender.trim(),
        birth_date: registerForm.birth_date || null,
        address: registerForm.address.trim(),
        guardian_name: registerForm.guardian_name.trim(),
        parent_contact: registerForm.parent_contact.trim(),
        email: registerForm.email.trim(),
        student_status: registerForm.student_status || 'active',
      })

      setRegisterMessage('Student registered successfully.')
      setRegisterForm({
        lrn: '',
        first_name: '',
        middle_name: '',
        last_name: '',
        suffix: '',
        gender: '',
        birth_date: '',
        address: '',
        guardian_name: '',
        parent_contact: '',
        email: '',
        student_status: 'active',
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
          <PlusIcon className="icon" /> Register New Student
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
                <h2 id="register-student-title">Register New Student</h2>
              </div>
              <button type="button" className="icon-button" aria-label="Close registration form" onClick={() => setShowRegisterModal(false)}>
                ×
              </button>
            </div>

            <form className="registration-form" onSubmit={handleRegisterSubmit}>
              {registerErrors.form ? <ErrorBanner message={registerErrors.form} /> : null}
              <div className="form-grid">
                <label>
                  <span>LRN</span>
                  <input name="lrn" value={registerForm.lrn} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.lrn)} />
                  {registerErrors.lrn ? <small className="field-error">{registerErrors.lrn}</small> : null}
                </label>
                <label>
                  <span>First Name</span>
                  <input name="first_name" value={registerForm.first_name} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.first_name)} />
                  {registerErrors.first_name ? <small className="field-error">{registerErrors.first_name}</small> : null}
                </label>
                <label>
                  <span>Middle Name</span>
                  <input name="middle_name" value={registerForm.middle_name} onChange={updateRegisterField} />
                </label>
                <label>
                  <span>Last Name</span>
                  <input name="last_name" value={registerForm.last_name} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.last_name)} />
                  {registerErrors.last_name ? <small className="field-error">{registerErrors.last_name}</small> : null}
                </label>
                <label>
                  <span>Suffix</span>
                  <input name="suffix" value={registerForm.suffix} onChange={updateRegisterField} placeholder="e.g. Jr., III" />
                </label>
                <label>
                  <span>Sex</span>
                  <select name="gender" value={registerForm.gender} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.gender)}>
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                  {registerErrors.gender ? <small className="field-error">{registerErrors.gender}</small> : null}
                </label>
                <label>
                  <span>Birthdate</span>
                  <input type="date" name="birth_date" value={registerForm.birth_date} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.birth_date)} />
                  {registerErrors.birth_date ? <small className="field-error">{registerErrors.birth_date}</small> : null}
                </label>
                <label className="form-grid-full">
                  <span>Address</span>
                  <input name="address" value={registerForm.address} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.address)} />
                  {registerErrors.address ? <small className="field-error">{registerErrors.address}</small> : null}
                </label>
                <label>
                  <span>Guardian</span>
                  <input name="guardian_name" value={registerForm.guardian_name} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.guardian_name)} />
                  {registerErrors.guardian_name ? <small className="field-error">{registerErrors.guardian_name}</small> : null}
                </label>
                <label>
                  <span>Parent Contact</span>
                  <input name="parent_contact" value={registerForm.parent_contact} onChange={updateRegisterField} aria-invalid={Boolean(registerErrors.parent_contact)} />
                  {registerErrors.parent_contact ? <small className="field-error">{registerErrors.parent_contact}</small> : null}
                </label>
                <label>
                  <span>Email (optional)</span>
                  <input type="email" name="email" value={registerForm.email} onChange={updateRegisterField} />
                </label>
              </div>

              <div className="modal-actions">
                <button type="button" className="action-button action-button--neutral" onClick={() => { setShowRegisterModal(false); resetRegisterForm() }}>Cancel</button>
                <button type="submit" className="action-button action-button--primary" disabled={submitting}>
                  {submitting ? <LoadingSpinner label="Saving..." /> : <><UserPlusIcon className="icon" /> Register New Student</>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

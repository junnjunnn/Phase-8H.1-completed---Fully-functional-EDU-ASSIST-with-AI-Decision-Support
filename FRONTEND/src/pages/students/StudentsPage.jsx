import { MagnifyingGlassIcon, PlusIcon, UserPlusIcon } from '@heroicons/react/24/outline'
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useSearchParams } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { PageHeader } from '../../components/common/PageHeader'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { useAuth } from '../../context/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import {
  confirmStudentImport,
  createEnrollment,
  createStudent,
  downloadStudentImportTemplate,
  getAcademicYears,
  getGradeLevels,
  getSections,
  getStudents,
  previewStudentImport,
  updateStudent,
} from '../../services/studentService'

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
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
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
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState(null)
  const [importPreview, setImportPreview] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [importError, setImportError] = useState('')
  const [importLoading, setImportLoading] = useState(false)
  const [confirmingImport, setConfirmingImport] = useState(false)
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [registerMessage, setRegisterMessage] = useState('')
  const [selectedYear, setSelectedYear] = useState('')
  const selectedGrade = searchParams.get('grade_level') || ''
  const selectedSection = searchParams.get('section') || ''
  const selectedStatus = searchParams.get('status') || 'active'
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
  const visibleSections = useMemo(() => {
    const relevantSections = selectedGrade
      ? sections.filter((section) => String(section.grade_level) === String(selectedGrade) || String(section.grade_level_id ?? section.grade_level) === String(selectedGrade))
      : sections

    return [...relevantSections].sort((left, right) => String(left.name).localeCompare(String(right.name)))
  }, [sections, selectedGrade])

  const hasActiveStudentFilters = Boolean(search || selectedGrade || selectedSection)

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
        const routeParams = new URLSearchParams(location.search)
        const data = await getStudents({
          search,
          status: selectedStatus,
          academic_year: routeParams.get('academic_year') || undefined,
          grade_level: routeParams.get('grade_level') || undefined,
          section: routeParams.get('section') || undefined,
        })
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
  }, [location.search, search, selectedStatus])

  useEffect(() => {
    async function loadReferenceData() {
      try {
        const [years, grades, allSections] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections({ active_only: 'true' }),
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

  function updateStudentFilters(changes) {
    const nextParams = new URLSearchParams(searchParams)
    Object.entries(changes).forEach(([key, value]) => {
      if (value) {
        nextParams.set(key, String(value))
      } else {
        nextParams.delete(key)
      }
    })
    setSearchParams(nextParams, { replace: true })
  }

  function handleGradeChange(event) {
    const nextGrade = event.target.value
    const nextSection = selectedSection && visibleSections.some((section) => String(section.id) === String(selectedSection) && String(section.grade_level) === String(nextGrade)) ? selectedSection : ''
    updateStudentFilters({ grade_level: nextGrade, section: nextSection })
  }

  function handleSectionChange(event) {
    updateStudentFilters({ section: event.target.value })
  }

  function clearStudentFilters() {
    updateStudentFilters({ grade_level: '', section: '' })
  }

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

  function openImportModal() {
    setImportFile(null)
    setImportPreview(null)
    setImportResult(null)
    setImportError('')
    setShowImportModal(true)
  }

  async function handleTemplateDownload() {
    setImportError('')
    try {
      await downloadStudentImportTemplate()
    } catch (err) {
      setImportError(getApiErrorMessage(err))
    }
  }

  async function handleImportPreview(event) {
    event.preventDefault()
    if (!importFile) {
      setImportError('Choose an .xlsx file before creating a preview.')
      return
    }
    setImportLoading(true)
    setImportError('')
    setImportResult(null)
    try {
      setImportPreview(await previewStudentImport(importFile))
    } catch (err) {
      setImportPreview(null)
      setImportError(getApiErrorMessage(err))
    } finally {
      setImportLoading(false)
    }
  }

  async function handleImportConfirm() {
    if (!importPreview?.import_token || !importPreview.valid_count || !importFile) {
      setImportError('There are no eligible records to import. Create a new preview.')
      return
    }
    setConfirmingImport(true)
    setImportError('')
    try {
      const result = await confirmStudentImport(importFile, importPreview.import_token)
      setImportResult(result)
      setImportPreview(null)
      setImportFile(null)
      if (result.imported_count) {
        const refreshed = await getStudents({ search })
        setStudents(refreshed.results || [])
        setPagination({ count: refreshed.count || 0, next: refreshed.next, previous: refreshed.previous })
      }
    } catch (err) {
      setImportError(getApiErrorMessage(err))
    } finally {
      setConfirmingImport(false)
    }
  }

  function closeImportModal() {
    if (importLoading || confirmingImport) return
    setShowImportModal(false)
    setImportFile(null)
    setImportPreview(null)
    setImportResult(null)
    setImportError('')
  }

  return (
    <div className="page-stack students-page">
      <PageHeader eyebrow="Student management" title="Students" description="Manage the current learner roster and move quickly into enrollment, profile review, or student status updates." actions={canCreateStudent ? (
        <div className="section-actions">
          <button type="button" className="action-button action-button--neutral" onClick={openImportModal}>
            Bulk registration (Excel)
          </button>
          <button type="button" className="action-button action-button--primary" onClick={() => { resetRegisterForm(); setShowRegisterModal(true) }}>
            <PlusIcon className="icon" /> Register New Student
          </button>
        </div>
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

        <div className="students-toolbar students-toolbar--filters">
          <label className="filter-field">
            <span>Status</span>
            <select value={selectedStatus} onChange={(event) => updateStudentFilters({ status: event.target.value })}>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
              <option value="all">All</option>
            </select>
          </label>
          <label className="filter-field">
            <span>Grade level</span>
            <select value={selectedGrade} onChange={handleGradeChange}>
              <option value="">All grades</option>
              {gradeLevels.map((grade) => (
                <option key={grade.id} value={grade.id}>{grade.name}</option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>Section</span>
            <select value={selectedSection} onChange={handleSectionChange} disabled={!visibleSections.length}>
              <option value="">All sections</option>
              {visibleSections.map((section) => (
                <option key={section.id} value={section.id}>{section.name}</option>
              ))}
            </select>
          </label>
          <button type="button" className="action-button action-button--outline" onClick={clearStudentFilters}>
            Clear filters
          </button>
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
            title={hasActiveStudentFilters ? 'No students match the current filters' : 'No students available'}
            message={hasActiveStudentFilters ? 'Try another search, change the grade/section filters, or clear the filters.' : 'There are no student records available in the system right now.'}
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

      {showImportModal && (
        <div className="modal-backdrop" role="presentation" onClick={closeImportModal}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="student-import-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Student registration</p>
                <h2 id="student-import-title">Bulk registration from Excel</h2>
              </div>
              <button type="button" className="icon-button" aria-label="Close bulk registration" onClick={closeImportModal}>×</button>
            </div>

            {importError ? <ErrorBanner message={importError} /> : null}
            <div className="section-description">
              This imports student records only. Enrollment into a section and academic year remains a separate workflow.
            </div>
            <div className="section-actions" style={{ margin: '1rem 0' }}>
              <button type="button" className="action-button action-button--neutral" onClick={handleTemplateDownload}>
                Download Excel template
              </button>
              <span className="small-muted">.xlsx only · maximum file size 2 MB · maximum 2,000 student rows</span>
            </div>

            {!importResult ? (
              <>
                <form className="registration-form" onSubmit={handleImportPreview}>
                  <label>
                    <span>Select student workbook (.xlsx)</span>
                    <input
                      type="file"
                      accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                      onChange={(event) => {
                        setImportFile(event.target.files?.[0] || null)
                        setImportPreview(null)
                        setImportError('')
                      }}
                      disabled={importLoading || confirmingImport}
                    />
                  </label>
                  <p className="small-muted">
                    Required columns: LRN, first name, last name, gender, birth date, address, guardian name, and parent contact.
                    Middle name, suffix, and email are optional. New registrations are set to Active.
                  </p>
                  <div className="modal-actions">
                    <button type="button" className="action-button action-button--neutral" onClick={closeImportModal} disabled={importLoading}>Cancel</button>
                    <button type="submit" className="action-button action-button--primary" disabled={!importFile || importLoading}>
                      {importLoading ? <LoadingSpinner label="Validating..." /> : 'Preview records'}
                    </button>
                  </div>
                </form>

                {importPreview ? (
                  <div className="registration-form">
                    <div className="record-summary-grid">
                      <article className="detail-card">
                        <p className="stat-label">Eligible to import</p>
                        <p className="stat-value">{importPreview.valid_count}</p>
                      </article>
                      <article className="detail-card">
                        <p className="stat-label">Rows needing correction</p>
                        <p className="stat-value">{importPreview.rejected_count}</p>
                      </article>
                    </div>
                    <p className="small-muted">
                      Review the row statuses before confirming. The workbook is re-uploaded and revalidated at confirmation; invalid or duplicate rows will not be imported.
                      {importPreview.expires_in_seconds ? ' The preview expires after 30 minutes.' : ''}
                    </p>
                    <div className="students-table-wrapper" style={{ maxHeight: '20rem', overflow: 'auto' }}>
                      <table className="students-table">
                        <thead>
                          <tr>
                            <th scope="col">Excel row</th>
                            <th scope="col">LRN</th>
                            <th scope="col">Student</th>
                            <th scope="col">Status and feedback</th>
                          </tr>
                        </thead>
                        <tbody>
                          {importPreview.rows.map((row) => (
                            <tr key={row.row}>
                              <td>{row.row}</td>
                              <td>{row.lrn || '—'}</td>
                              <td>{`${row.first_name || ''} ${row.last_name || ''}`.trim() || '—'}</td>
                              <td>
                                <strong>
                                  {row.status === 'valid' ? 'Valid' : row.status === 'duplicate_file' ? 'Duplicate LRN in file' : row.status === 'duplicate_existing' ? 'Already registered' : 'Invalid'}
                                </strong>
                                {row.errors.length ? <ul>{row.errors.map((message, index) => <li key={`${row.row}-${index}`}>{message}</li>)}</ul> : null}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="modal-actions">
                      <button type="button" className="action-button action-button--neutral" onClick={() => { setImportPreview(null); setImportFile(null) }}>Choose another file</button>
                      <button type="button" className="action-button action-button--primary" onClick={handleImportConfirm} disabled={!importPreview.valid_count || confirmingImport}>
                        {confirmingImport ? <LoadingSpinner label="Importing..." /> : `Confirm import of ${importPreview.valid_count} student${importPreview.valid_count === 1 ? '' : 's'}`}
                      </button>
                    </div>
                  </div>
                ) : null}
              </>
            ) : (
              <div className="registration-form">
                <div className={importResult.imported_count ? 'status-banner status-banner--success' : 'status-banner'}>
                  Import complete: {importResult.imported_count} student{importResult.imported_count === 1 ? '' : 's'} imported; {importResult.rejected_count} row{importResult.rejected_count === 1 ? '' : 's'} rejected.
                </div>
                {importResult.imported_rows.length ? <p>Imported Excel rows: {importResult.imported_rows.join(', ')}</p> : null}
                {importResult.rejected_rows.length ? (
                  <div className="students-table-wrapper" style={{ maxHeight: '20rem', overflow: 'auto' }}>
                    <table className="students-table">
                      <thead>
                        <tr><th scope="col">Excel row</th><th scope="col">Result</th></tr>
                      </thead>
                      <tbody>
                        {importResult.rejected_rows.map((row) => (
                          <tr key={row.row}>
                            <td>{row.row}</td>
                            <td><ul>{row.errors.map((message, index) => <li key={`${row.row}-${index}`}>{message}</li>)}</ul></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
                <div className="modal-actions">
                  <button type="button" className="action-button action-button--primary" onClick={closeImportModal}>Done</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

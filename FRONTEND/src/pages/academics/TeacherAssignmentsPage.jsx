import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { getApiErrorMessage } from '../../services/api'
import {
  getAcademicYears,
  getGradeLevels,
  getSections,
  getSubjects,
} from '../../services/academicsService'
import { getUsers as getUserProfiles } from '../../services/userService'
import apiClient from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function TeacherAssignmentsPage() {
  const [assignments, setAssignments] = useState([])
  const [teachers, setTeachers] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [teacherFilter, setTeacherFilter] = useState('')
  const [yearFilter, setYearFilter] = useState('')
  const [gradeFilter, setGradeFilter] = useState('')
  const [sectionFilter, setSectionFilter] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', teacher: '', academic_year: '', grade_level: '', section: '', subject: '', is_active: true })
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [pendingAssignment, setPendingAssignment] = useState(null)

  useEffect(() => {
    let active = true

    async function loadData() {
      setLoading(true)
      setError('')
      try {
        const [assignmentData, teacherData, yearData, gradeData, sectionData, subjectData] = await Promise.all([
          apiClient.get('/teacher-assignments/'),
          getUserProfiles(),
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getSubjects(),
        ])
        if (!active) return

        setAssignments(normalizeListResponse(assignmentData.data).items)
        setTeachers(normalizeListResponse(teacherData.data).items || [])
        setAcademicYears(normalizeListResponse(yearData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
        setSections(normalizeListResponse(sectionData).items)
        setSubjects(normalizeListResponse(subjectData).items)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadData()
    return () => { active = false }
  }, [])

  useEffect(() => {
    // Defer resetting page to avoid synchronous setState in effect
    const t = setTimeout(() => {
      setPage((p) => (p === 1 ? p : 1))
    }, 0)
    return () => clearTimeout(t)
  }, [search, teacherFilter, yearFilter, gradeFilter, sectionFilter, subjectFilter, statusFilter])

  const filteredAssignments = useMemo(() => {
    const term = search.trim().toLowerCase()
    return assignments.filter((assignment) => {
      const teacherName = `${assignment.teacher_name || assignment.teacher || ''}`.toLowerCase()
      const sectionName = `${assignment.section_name || assignment.section || ''}`.toLowerCase()
      const subjectName = `${assignment.subject_name || assignment.subject || ''}`.toLowerCase()
      const matchesSearch = !term || teacherName.includes(term) || sectionName.includes(term) || subjectName.includes(term)
      const matchesTeacher = !teacherFilter || String(assignment.teacher) === String(teacherFilter)
      const matchesYear = !yearFilter || String(assignment.academic_year) === String(yearFilter)
      const matchesGrade = !gradeFilter || String(assignment.grade_level) === String(gradeFilter)
      const matchesSection = !sectionFilter || String(assignment.section) === String(sectionFilter)
      const matchesSubject = !subjectFilter || String(assignment.subject) === String(subjectFilter)
      const matchesStatus = statusFilter === 'all' || String(assignment.is_active) === statusFilter
      return matchesSearch && matchesTeacher && matchesYear && matchesGrade && matchesSection && matchesSubject && matchesStatus
    })
  }, [assignments, search, teacherFilter, yearFilter, gradeFilter, sectionFilter, subjectFilter, statusFilter])

  const pageSize = 8
  const pagedAssignments = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredAssignments.slice(start, start + pageSize)
  }, [filteredAssignments, page])

  const totalPages = Math.max(1, Math.ceil(filteredAssignments.length / pageSize))

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setSubmitting(true)

    try {
      const payload = {
        teacher: Number(form.teacher),
        academic_year: Number(form.academic_year),
        grade_level: Number(form.grade_level),
        section: Number(form.section),
        subject: Number(form.subject),
        is_active: form.is_active !== false,
      }
      if (form.id) {
        await apiClient.patch(`/teacher-assignments/${form.id}/`, payload)
      } else {
        await apiClient.post('/teacher-assignments/', payload)
      }
      const refreshed = await apiClient.get('/teacher-assignments/')
      setAssignments(normalizeListResponse(refreshed.data).items)
      setForm({ id: '', teacher: '', academic_year: '', grade_level: '', section: '', subject: '', is_active: true })
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  function startEdit(assignment) {
    setForm({
      id: assignment.id,
      teacher: assignment.teacher || '',
      academic_year: assignment.academic_year || '',
      grade_level: assignment.grade_level || '',
      section: assignment.section || '',
      subject: assignment.subject || '',
      is_active: assignment.is_active !== false,
    })
  }

  function cancelEdit() {
    setForm({ id: '', teacher: '', academic_year: '', grade_level: '', section: '', subject: '', is_active: true })
  }

  async function toggleAssignmentStatus(assignment) {
    setPendingAssignment(assignment)
    setConfirmOpen(true)
  }

  async function confirmToggle() {
    if (!pendingAssignment) return
    try {
      await apiClient.patch(`/teacher-assignments/${pendingAssignment.id}/`, { is_active: !pendingAssignment.is_active })
      const refreshed = await apiClient.get('/teacher-assignments/')
      setAssignments(normalizeListResponse(refreshed.data).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setConfirmOpen(false)
      setPendingAssignment(null)
    }
  }

  const visibleSections = sections.filter((section) => {
    const matchesYear = !form.academic_year || String(section.academic_year) === String(form.academic_year)
    const matchesGrade = !form.grade_level || String(section.grade_level) === String(form.grade_level)
    return matchesYear && matchesGrade
  })

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Teacher assignments" title="Assign teachers to classes and subjects" description="Create, edit, and manage assignments for academic years, sections, and subjects." />
      {error ? <ErrorBanner message={error} /> : null}
      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Assignments</p>
          <p className="stat-value">{assignments.length}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Teachers</p>
          <p className="stat-value">{teachers.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Create or edit assignment</p>
            <h2>{form.id ? 'Update assignment' : 'Assign teacher to section and subject'}</h2>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          {formError ? <ErrorBanner message={formError} /> : null}
          <label>
            <span>Teacher</span>
            <select value={form.teacher} onChange={(event) => setForm({ ...form, teacher: event.target.value })} required>
              <option value="">Select teacher</option>
              {teachers.filter((teacher) => teacher.profile?.role_name === 'TEACHER' || teacher.role_name === 'TEACHER').map((teacher) => (
                <option key={teacher.id} value={teacher.id}>{teacher.first_name} {teacher.last_name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Academic year</span>
            <select value={form.academic_year} onChange={(event) => setForm({ ...form, academic_year: event.target.value, grade_level: '', section: '', subject: '' })} required>
              <option value="">Select</option>
              {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={form.grade_level} onChange={(event) => setForm({ ...form, grade_level: event.target.value, section: '', subject: '' })} required>
              <option value="">Select</option>
              {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
            </select>
          </label>
          <label>
            <span>Section</span>
            <select value={form.section} onChange={(event) => setForm({ ...form, section: event.target.value })} required>
              <option value="">Select</option>
              {visibleSections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
            </select>
          </label>
          <label>
            <span>Subject</span>
            <select value={form.subject} onChange={(event) => setForm({ ...form, subject: event.target.value })} required>
              <option value="">Select</option>
              {subjects.filter((subject) => !form.grade_level || String(subject.grade_level) === String(form.grade_level)).map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={submitting}>{submitting ? 'Saving...' : form.id ? 'Update assignment' : 'Create assignment'}</button>
            {form.id ? <button type="button" className="action-button action-button--neutral" onClick={cancelEdit}>Cancel</button> : null}
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Assigned classes</p>
            <h2>Teacher assignment roster</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search assignments" placeholder="Search teacher or section" value={search} onChange={(event) => setSearch(event.target.value)} />
          </div>
        </div>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Teacher</span>
            <select value={teacherFilter} onChange={(event) => setTeacherFilter(event.target.value)}>
              <option value="">All teachers</option>
              {teachers.filter((teacher) => teacher.profile?.role_name === 'TEACHER' || teacher.role_name === 'TEACHER').map((teacher) => (
                <option key={teacher.id} value={teacher.id}>{teacher.first_name} {teacher.last_name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Academic year</span>
            <select value={yearFilter} onChange={(event) => setYearFilter(event.target.value)}>
              <option value="">All years</option>
              {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={gradeFilter} onChange={(event) => setGradeFilter(event.target.value)}>
              <option value="">All grades</option>
              {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
            </select>
          </label>
          <label>
            <span>Section</span>
            <select value={sectionFilter} onChange={(event) => setSectionFilter(event.target.value)}>
              <option value="">All sections</option>
              {sections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}
            </select>
          </label>
          <label>
            <span>Subject</span>
            <select value={subjectFilter} onChange={(event) => setSubjectFilter(event.target.value)}>
              <option value="">All subjects</option>
              {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
        {!loading && filteredAssignments.length === 0 ? <EmptyState title="No assignments" message="No teacher assignments match the current filters." /> : null}
        {!loading && filteredAssignments.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Teacher</th>
                  <th scope="col">Academic year</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Section</th>
                  <th scope="col">Subject</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedAssignments.map((assignment) => (
                  <tr key={assignment.id}>
                    <td>{assignment.teacher_name || assignment.teacher || '—'}</td>
                    <td>{assignment.academic_year_name || assignment.academic_year || '—'}</td>
                    <td>{assignment.grade_level_name || assignment.grade_level || '—'}</td>
                    <td>{assignment.section_name || assignment.section || '—'}</td>
                    <td>{assignment.subject_name || assignment.subject || '—'}</td>
                    <td>{assignment.is_active ? 'Active' : 'Inactive'}</td>
                    <td>
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <button type="button" className="action-button action-button--neutral" onClick={() => startEdit(assignment)}>Edit</button>
                        <button type="button" className="action-button action-button--neutral" onClick={() => toggleAssignmentStatus(assignment)}>{assignment.is_active ? 'Archive' : 'Restore'}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--neutral" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>Previous</button>
              <span style={{ alignSelf: 'center' }}>Page {page} of {totalPages}</span>
              <button type="button" className="action-button action-button--neutral" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>Next</button>
            </div>
          </div>
        ) : null}
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title={pendingAssignment?.is_active ? 'Archive assignment' : 'Restore assignment'}
        message={pendingAssignment ? `This will ${pendingAssignment.is_active ? 'archive' : 'restore'} the selected teacher assignment.` : ''}
        confirmLabel={pendingAssignment?.is_active ? 'Archive' : 'Restore'}
        onConfirm={confirmToggle}
        onCancel={() => { setConfirmOpen(false); setPendingAssignment(null) }}
      />
    </div>
  )
}

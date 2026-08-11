import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { getApiErrorMessage } from '../../services/api'
import { getAcademicYears, getGradeLevels, getSections } from '../../services/academicsService'
import { createEnrollment, getStudents } from '../../services/studentService'
import apiClient from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function EnrollmentPage() {
  const [enrollments, setEnrollments] = useState([])
  const [students, setStudents] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [yearFilter, setYearFilter] = useState('')
  const [gradeFilter, setGradeFilter] = useState('')
  const [sectionFilter, setSectionFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ student: '', academic_year: '', grade_level: '', section: '', enrollment_status: 'active' })
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [pendingEnrollment, setPendingEnrollment] = useState(null)

  useEffect(() => {
    let active = true

    async function loadData() {
      setLoading(true)
      setError('')
      try {
        const [enrollmentData, studentData, yearData, gradeData, sectionData] = await Promise.all([
          apiClient.get('/enrollments/'),
          getStudents(),
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
        ])
        if (!active) return
        setEnrollments(normalizeListResponse(enrollmentData.data).items)
        setStudents(normalizeListResponse(studentData).items || [])
        setAcademicYears(normalizeListResponse(yearData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
        setSections(normalizeListResponse(sectionData).items)
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
    const t = setTimeout(() => setPage((p) => (p === 1 ? p : 1)), 0)
    return () => clearTimeout(t)
  }, [search, yearFilter, gradeFilter, sectionFilter, statusFilter])

  const filteredEnrollments = useMemo(() => {
    const term = search.trim().toLowerCase()
    return enrollments.filter((enrollment) => {
      const studentName = `${enrollment.student_name || ''}`.toLowerCase()
      const matchesSearch = !term || studentName.includes(term)
      const matchesYear = !yearFilter || String(enrollment.academic_year) === String(yearFilter)
      const matchesGrade = !gradeFilter || String(enrollment.grade_level) === String(gradeFilter)
      const matchesSection = !sectionFilter || String(enrollment.section) === String(sectionFilter)
      const matchesStatus = statusFilter === 'all' || String(enrollment.enrollment_status || 'active') === statusFilter
      return matchesSearch && matchesYear && matchesGrade && matchesSection && matchesStatus
    })
  }, [enrollments, search, yearFilter, gradeFilter, sectionFilter, statusFilter])

  const pageSize = 8
  const pagedEnrollments = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredEnrollments.slice(start, start + pageSize)
  }, [filteredEnrollments, page])

  const totalPages = Math.max(1, Math.ceil(filteredEnrollments.length / pageSize))

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')
    setSubmitting(true)
    try {
      await createEnrollment({
        student: Number(form.student),
        academic_year: Number(form.academic_year),
        grade_level: Number(form.grade_level),
        section: Number(form.section),
        enrollment_status: form.enrollment_status,
        enrollment_date: new Date().toISOString().slice(0, 10),
      })
      const refreshed = await apiClient.get('/enrollments/')
      setEnrollments(normalizeListResponse(refreshed.data).items)
      setForm({ student: '', academic_year: '', grade_level: '', section: '', enrollment_status: 'active' })
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleStatusToggle() {
    if (!pendingEnrollment) return
    try {
      await apiClient.patch(`/enrollments/${pendingEnrollment.id}/`, { enrollment_status: pendingEnrollment.enrollment_status === 'active' ? 'inactive' : 'active' })
      const refreshed = await apiClient.get('/enrollments/')
      setEnrollments(normalizeListResponse(refreshed.data).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setConfirmOpen(false)
      setPendingEnrollment(null)
    }
  }

  const visibleSections = sections.filter((section) => {
    const matchesYear = !form.academic_year || String(section.academic_year) === String(form.academic_year)
    const matchesGrade = !form.grade_level || String(section.grade_level) === String(form.grade_level)
    return matchesYear && matchesGrade
  })

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Enrollment management" title="Manage student enrollments" description="Follow a guided enrollment workflow to assign students, validate sections, and keep the roster current." />
      {error ? <ErrorBanner message={error} /> : null}

      <section className="detail-card workflow-guide-card">
        <div className="section-header">
          <div>
            <p className="eyebrow">Workflow guidance</p>
            <h3>Keep section placement consistent</h3>
          </div>
        </div>
        <ul className="workflow-guide-list">
          <li>Select the student, year, grade level, and section in sequence to keep placement accurate.</li>
          <li>Use the roster filters to isolate a section or enrollment status before making updates.</li>
          <li>Review the status changes as part of the same workflow so the records stay aligned.</li>
        </ul>
        <div className="workflow-guide-actions">
          <span className="action-chip">Enrollment workflow</span>
          <span className="action-chip">Section assignment</span>
        </div>
      </section>

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Enrollments</p>
          <p className="stat-value">{enrollments.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Create enrollment</p>
            <h2>Assign a student to a section</h2>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          {formError ? <ErrorBanner message={formError} /> : null}
          <label>
            <span>Student</span>
            <select value={form.student} onChange={(event) => setForm({ ...form, student: event.target.value })} required>
              <option value="">Select student</option>
              {students.map((student) => <option key={student.id} value={student.id}>{student.first_name} {student.last_name}</option>)}
            </select>
          </label>
          <label>
            <span>Academic year</span>
            <select value={form.academic_year} onChange={(event) => setForm({ ...form, academic_year: event.target.value, grade_level: '', section: '' })} required>
              <option value="">Select</option>
              {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={form.grade_level} onChange={(event) => setForm({ ...form, grade_level: event.target.value, section: '' })} required>
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
            <span>Status</span>
            <select value={form.enrollment_status} onChange={(event) => setForm({ ...form, enrollment_status: event.target.value })}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="transferred">Transferred</option>
              <option value="graduated">Graduated</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={submitting}>{submitting ? 'Saving...' : 'Create enrollment'}</button>
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Current enrollments</p>
            <h2>Enrollment roster</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search enrollments" placeholder="Search student" value={search} onChange={(event) => setSearch(event.target.value)} />
          </div>
        </div>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
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
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="transferred">Transferred</option>
              <option value="graduated">Graduated</option>
            </select>
          </label>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
        {!loading && filteredEnrollments.length === 0 ? <EmptyState title="No enrollments" message="No student enrollments match the current filters." /> : null}
        {!loading && filteredEnrollments.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Student</th>
                  <th scope="col">Academic year</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Section</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedEnrollments.map((enrollment) => (
                  <tr key={enrollment.id}>
                    <td>{enrollment.student_name || enrollment.student || '—'}</td>
                    <td>{enrollment.academic_year_name || enrollment.academic_year || '—'}</td>
                    <td>{enrollment.grade_level_name || enrollment.grade_level || '—'}</td>
                    <td>{enrollment.section_name || enrollment.section || '—'}</td>
                    <td>{enrollment.enrollment_status || 'active'}</td>
                    <td>
                      <button type="button" className="action-button action-button--neutral" onClick={() => { setPendingEnrollment(enrollment); setConfirmOpen(true) }}>Update</button>
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
        title="Update enrollment status"
        message={pendingEnrollment ? `Toggle the status for ${pendingEnrollment.student_name || 'this enrollment'}?` : ''}
        confirmLabel="Continue"
        onConfirm={handleStatusToggle}
        onCancel={() => { setConfirmOpen(false); setPendingEnrollment(null) }}
      />
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { ExcelImportPanel } from '../../components/common/ExcelImportPanel'
import { getApiErrorMessage } from '../../services/api'
import {
  getAcademicYears,
  getGradeLevels,
  getSections,
  getSubjects,
} from '../../services/academicsService'
import { getUsers as getUserProfiles } from '../../services/userService'
import { subscribeSubjectsUpdated, unsubscribeSubjectsUpdated } from '../../services/referenceService'
import apiClient from '../../services/api'
import { useAuth } from '../../context/AuthContext'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function TeacherAssignmentsPage() {
  const { user } = useAuth()
  const [assignments, setAssignments] = useState([])
  const [teachers, setTeachers] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [subjects, setSubjects] = useState([])
  const [historicalSubject, setHistoricalSubject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [teacherFilter, setTeacherFilter] = useState('')
  const [yearFilter, setYearFilter] = useState('')
  const [gradeFilter, setGradeFilter] = useState('')
  const [sectionFilter, setSectionFilter] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [subjectSearch, setSubjectSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', assignment_type: 'SUBJECT', teacher: '', grade_level: '', section: '', subjects: [], is_active: true })
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
          getUserProfiles({ active_only: 'true', role_name: 'TEACHER' }),
          getAcademicYears({ status: 'all' }),
          getGradeLevels({ active_only: 'true' }),
          getSections({ active_only: 'true' }),
          Promise.resolve([]),
        ])
        if (!active) return

        setAssignments(normalizeListResponse(assignmentData.data).items)
        const teacherPayload = teacherData?.data ?? teacherData
        const teacherItems = normalizeListResponse(teacherPayload).items || []
        setTeachers(teacherItems)
        const yearItems = normalizeListResponse(yearData).items
        setAcademicYears(yearItems)
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
    let active = true

    async function reloadSubjects() {
      if (!form.grade_level) {
        setSubjects([])
        return
      }
      try {
        const subjectData = await getSubjects({ active_only: 'true', grade_level: form.grade_level })
        if (!active) {
          return
        }
        const items = normalizeListResponse(subjectData).items
        setSubjects(historicalSubject && !items.some((subject) => String(subject.id) === String(historicalSubject.id))
          ? [...items, historicalSubject]
          : items)
      } catch (err) {
        if (!active) {
          return
        }
        setSubjects(historicalSubject ? [historicalSubject] : [])
        setFormError(getApiErrorMessage(err))
      }
    }

    function handleSubjectsUpdated() {
      reloadSubjects()
    }

    reloadSubjects()
    subscribeSubjectsUpdated(handleSubjectsUpdated)
    return () => {
      active = false
      unsubscribeSubjectsUpdated(handleSubjectsUpdated)
    }
  }, [form.grade_level, form.section, historicalSubject])

  useEffect(() => {
    if (!form.section || sections.some((section) => String(section.id) === String(form.section))) {
      return
    }
    setHistoricalSubject(null)
    setSubjectSearch('')
    setForm((current) => ({ ...current, section: '', grade_level: '', subjects: [] }))
  }, [form.section, sections])

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
      const subjectCodes = `${assignment.official_subject_code || ''} ${assignment.subject_code || ''}`.toLowerCase()
      const matchesSearch = !term || teacherName.includes(term) || sectionName.includes(term) || subjectName.includes(term) || subjectCodes.includes(term)
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
  const activeYearCount = academicYears.filter((year) => year.is_active).length

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError('')

    const selectedSection = sections.find((section) => String(section.id) === String(form.section))
    if (!selectedSection || !form.teacher || (form.assignment_type === 'SUBJECT' && form.subjects.length === 0)) {
      const missingFields = []
      if (!selectedSection) missingFields.push('section')
      if (!form.teacher) missingFields.push('teacher')
      if (form.assignment_type === 'SUBJECT' && form.subjects.length === 0) missingFields.push('at least one subject')
      setFormError(`Complete these required fields: ${missingFields.join(', ')}.`)
      return
    }

    setSubmitting(true)

    try {
      const payload = {
        teacher: Number(form.teacher),
        grade_level: Number(selectedSection.grade_level),
        section: Number(form.section),
        ...(form.id && form.assignment_type === 'SUBJECT' ? { subject: Number(form.subjects[0]) } : {}),
        ...(!form.id && form.assignment_type === 'SUBJECT' ? { subjects: form.subjects.map(Number) } : {}),
        ...(form.assignment_type === 'ADVISER' ? { subject: null } : {}),
        assignment_type: form.assignment_type,
        is_active: form.is_active !== false,
      }
      if (form.id) {
        await apiClient.patch(`/teacher-assignments/${form.id}/`, payload)
      } else {
        await apiClient.post('/teacher-assignments/', payload)
      }
      const refreshed = await apiClient.get('/teacher-assignments/')
      setAssignments(normalizeListResponse(refreshed.data).items)
      setHistoricalSubject(null)
      setForm({ id: '', assignment_type: 'SUBJECT', teacher: '', grade_level: '', section: '', subjects: [], is_active: true })
    } catch (err) {
      setFormError(getApiErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  function startEdit(assignment) {
    setSections((current) => current.some((section) => String(section.id) === String(assignment.section))
      ? current
      : [...current, {
        id: assignment.section,
        name: assignment.section_name || 'Archived section',
        grade_level: assignment.grade_level,
        grade_level_name: assignment.grade_level_name || 'Historical grade level',
        academic_year: assignment.academic_year,
        academic_year_name: assignment.academic_year_name || 'Historical academic year',
        is_active: false,
      }])
    setTeachers((current) => current.some((teacher) => String(teacher.id) === String(assignment.teacher))
      ? current
      : [...current, { id: assignment.teacher, username: assignment.teacher_name || 'Historical teacher', is_active: false, role_name: 'TEACHER' }])
    setHistoricalSubject(assignment.subject
      ? {
        id: assignment.subject,
        name: assignment.subject_name || 'Archived subject',
        code: assignment.subject_code || '',
        official_subject_code: assignment.official_subject_code || '',
        is_active: false,
        grade_levels: [assignment.grade_level],
      }
      : null)
    setForm({
      id: assignment.id,
      teacher: assignment.teacher || '',
      grade_level: assignment.grade_level || '',
      section: assignment.section || '',
      subjects: assignment.subject ? [assignment.subject] : [],
      assignment_type: assignment.assignment_type || (assignment.is_adviser ? 'ADVISER' : 'SUBJECT'),
      is_active: assignment.is_active !== false,
    })
  }

  function cancelEdit() {
    setHistoricalSubject(null)
    setForm({ id: '', assignment_type: 'SUBJECT', teacher: '', grade_level: '', section: '', subjects: [], is_active: true })
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
    const isCurrentHistoricalSection = form.id && String(section.id) === String(form.section)
    return section.is_active !== false || isCurrentHistoricalSection
  })
  const selectableTeachers = teachers.filter((teacher) => teacher.is_active !== false || (form.id && String(teacher.id) === String(form.teacher)))
  const selectedSection = sections.find((section) => String(section.id) === String(form.section))
  const selectedGradeLevel = gradeLevels.find((grade) => String(grade.id) === String(selectedSection?.grade_level))
  const selectedSchoolLevel = selectedSection?.grade_level_school_level || selectedGradeLevel?.school_level || '—'
  const visibleSubjects = subjects.filter((subject) => {
    const isCurrentHistoricalSubject = form.id && String(subject.id) === String(form.subjects[0])
    const isApplicable = (subject.grade_levels || [subject.grade_level]).map(String).includes(String(form.grade_level))
    const matchesSectionStrand = !subject.strand || !selectedSection?.strand || String(subject.strand) === String(selectedSection.strand)
    return form.grade_level && (subject.is_active !== false || isCurrentHistoricalSubject) && (isApplicable || isCurrentHistoricalSubject) && (matchesSectionStrand || isCurrentHistoricalSubject)
  })
  const normalizedSubjectSearch = subjectSearch.trim().toLowerCase()
  const searchedSubjects = visibleSubjects.filter((subject) => {
    if (!normalizedSubjectSearch) return true
    return `${subject.name || ''} ${subject.official_subject_code || ''} ${subject.code || ''}`.toLowerCase().includes(normalizedSubjectSearch)
  })
  const selectedSubjects = visibleSubjects.filter((subject) =>
    form.subjects.map(String).includes(String(subject.id)),
  )

  return (
    <div className="page-stack teacher-assignments-page">
      <PageHeader eyebrow="Teacher assignments" title="Assign teachers to sections" description="Choose a section first, then select its teacher and, for subject assignments, applicable subjects." />

      {['SUPER_ADMIN', 'SCHOOL_ADMIN'].includes(user?.role || user?.role_name || user?.profile?.role_name) ? (
        <ExcelImportPanel
          title="Teacher and adviser assignments"
          templateUrl="/teacher-assignments/import/template/"
          previewUrl="/teacher-assignments/import/preview/"
          confirmUrl="/teacher-assignments/import/confirm/"
          filename="edu-assist-teacher-assignment-import-template.xlsx"
          instructions="Imported teachers must already be active. Teacher accounts created by bulk registration need an administrator-set password and activation first."
          onCompleted={async () => {
            const refreshed = await apiClient.get('/teacher-assignments/')
            setAssignments(normalizeListResponse(refreshed.data).items)
          }}
        />
      ) : null}

      {error ? <ErrorBanner message={error} /> : null}
      {activeYearCount !== 1 ? (
        <div className="status-banner status-banner--warning">
          {activeYearCount === 0
            ? 'No active academic year is configured. '
            : 'More than one active academic year is configured. '}
          Ask an administrator to configure <Link to="/academic-years">Academic Year Management</Link> before creating assignments.
        </div>
      ) : null}
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

      <details className="academic-editor-panel" open={Boolean(form.id)}>
        <summary className="academic-editor-summary">
          <span>
            <span className="eyebrow">Assignment details</span>
            <strong>{form.id ? 'Update assignment' : 'Assign teacher to section and subject'}</strong>
          </span>
          <span className="academic-editor-prompt">{form.id ? 'Close form' : 'Open form'}</span>
        </summary>
        <form className="form-grid assignment-form-grid" onSubmit={handleSubmit}>
          {formError ? <div className="form-grid-full"><ErrorBanner message={formError} /></div> : null}
          <label className="assignment-section-field">
            <span>Section and school level</span>
            <select
              value={form.section}
              aria-describedby="assignment-school-level-help"
              onChange={(event) => {
                const section = visibleSections.find((item) => String(item.id) === event.target.value)
                setHistoricalSubject(null)
                setSubjectSearch('')
                setSubjects([])
                setForm((current) => ({
                  ...current,
                  teacher: '',
                  section: section ? String(section.id) : '',
                  grade_level: section ? String(section.grade_level) : '',
                  subjects: [],
                }))
                setFormError('')
              }}
              required
            >
              <option value="">Select section</option>
              {visibleSections.map((section) => {
                const gradeName = section.grade_level_name || getNameById(gradeLevels, section.grade_level)
                const schoolLevel = section.grade_level_school_level
                  || gradeLevels.find((grade) => String(grade.id) === String(section.grade_level))?.school_level
                const curriculum = [section.strand_name, section.specialization_name].filter(Boolean).join(' · ')
                return (
                  <option key={section.id} value={section.id}>
                    {[schoolLevel, gradeName, section.name, section.academic_year_name, curriculum].filter(Boolean).join(' · ')}
                    {section.is_active === false ? ' (Archived)' : ''}
                  </option>
                )
              })}
            </select>
            <small id="assignment-school-level-help" className="small-muted">
              School level is determined by the selected section's grade level; it is not the assignment type.
            </small>
          </label>
          {selectedSection ? (
            <div className="assignment-context-card" role="group" aria-label="Selected section context">
              <div><span>School level</span><strong>{selectedSchoolLevel}</strong></div>
              <div><span>Grade level</span><strong>{selectedSection.grade_level_name || selectedGradeLevel?.name || '—'}</strong></div>
              <div><span>Section</span><strong>{selectedSection.name}</strong></div>
              <div><span>Academic year</span><strong>{selectedSection.academic_year_name || '—'}</strong></div>
              <div><span>Strand</span><strong>{selectedSection.strand_name || (selectedSchoolLevel === 'Senior High School' ? 'Shared across strands' : 'Not applicable')}</strong></div>
              <div><span>Specialization</span><strong>{selectedSection.specialization_name || 'Not applicable'}</strong></div>
            </div>
          ) : null}
          <label>
            <span>Teacher</span>
            <select value={form.teacher} onChange={(event) => setForm({ ...form, teacher: event.target.value })} required disabled={!form.section}>
              <option value="">Select teacher</option>
              {selectableTeachers.filter((teacher) => teacher.profile?.role_name === 'TEACHER' || teacher.role_name === 'TEACHER').map((teacher) => {
                const displayName = `${(teacher.first_name || '').trim()} ${(teacher.last_name || '').trim()}`.trim() || teacher.username || 'Unknown'
                return (<option key={teacher.id} value={teacher.id}>{displayName}{teacher.is_active === false ? ' (Archived)' : ''}</option>)
              })}
            </select>
          </label>
          <label>
            <span>Assignment type</span>
            <select value={form.assignment_type} onChange={(event) => setForm({ ...form, assignment_type: event.target.value, subjects: [] })} required disabled={Boolean(form.id)}>
              <option value="SUBJECT">Subject Teacher</option>
              <option value="ADVISER">Class Adviser</option>
            </select>
            <small className="small-muted">Choose Subject Teacher or Class Adviser. Do not enter a school level here.</small>
            {form.id ? <small className="small-muted">Create a separate assignment to change assignment type.</small> : null}
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
          {form.assignment_type === 'SUBJECT' ? <div className="form-field assignment-subjects-field">
            <span className="form-field__label">Subjects</span>
            {selectedSection && !selectedSection.strand && selectedSchoolLevel === 'Senior High School' ? (
              <p className="small-muted">This is a shared section. Common and strand-specific subjects may be assigned; strand-specific eligibility is enforced against each student's enrollment strand.</p>
            ) : null}
            {!form.section ? <p className="small-muted">Select a section to view applicable subjects.</p> : null}
            {form.grade_level && !visibleSubjects.length ? <p className="small-muted">No active subjects are available for this grade level.</p> : null}
            {form.section && visibleSubjects.length > 0 ? (
              <label>
                <span>Search eligible subjects</span>
                <input
                  type="search"
                  value={subjectSearch}
                  onChange={(event) => setSubjectSearch(event.target.value)}
                  placeholder="Search by subject name, official code, or system ID"
                  aria-label="Search eligible subjects by name or code"
                />
              </label>
            ) : null}
            <div className="section-actions">
              <button type="button" className="action-button action-button--neutral" onClick={() => setForm({ ...form, subjects: visibleSubjects.map((subject) => subject.id) })} disabled={!form.section || !visibleSubjects.length}>Select all</button>
              <button type="button" className="action-button action-button--neutral" onClick={() => setForm({ ...form, subjects: [] })} disabled={!form.section}>Clear selection</button>
              <span>{form.subjects.length} selected</span>
            </div>
            {selectedSubjects.length > 0 ? (
              <div>
                <span className="form-field__label">Selected subjects</span>
                <div className="selection-summary">
                  {selectedSubjects.map((subject) => (
                    <label key={subject.id}>
                      <input
                        type="checkbox"
                        checked
                        onChange={() => setForm((current) => ({
                          ...current,
                          subjects: current.subjects.filter((id) => String(id) !== String(subject.id)),
                        }))}
                      />
                      {subject.name}{subject.strand_name ? ` · ${subject.strand_name}` : ' · Common subject'}{subject.official_subject_code ? ` (Official: ${subject.official_subject_code})` : ''}{subject.code ? ` (System ID: ${subject.code})` : ''}
                    </label>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="selection-summary">
              {searchedSubjects.map((subject) => <label key={subject.id}><input type="checkbox" checked={form.subjects.map(String).includes(String(subject.id))} onChange={(event) => setForm({ ...form, subjects: event.target.checked ? [...new Set([...form.subjects, subject.id])] : form.subjects.filter((id) => String(id) !== String(subject.id)) })} /> {subject.name}{subject.strand_name ? ` · ${subject.strand_name}` : ' · Common subject'}{subject.official_subject_code ? ` (Official: ${subject.official_subject_code})` : ''}{subject.code ? ` (System ID: ${subject.code})` : ''}{subject.is_active === false ? ' (Archived)' : ''}</label>)}
            </div>
            {form.section && visibleSubjects.length > 0 && searchedSubjects.length === 0 ? (
              <p className="small-muted">No eligible subjects match this search. Clear the search to see all subjects for this section.</p>
            ) : null}
          </div> : null}
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={submitting || (!form.id && activeYearCount !== 1)}>{submitting ? 'Saving...' : form.id ? 'Update assignment' : 'Create assignment'}</button>
            {form.id ? <button type="button" className="action-button action-button--neutral" onClick={cancelEdit}>Cancel</button> : null}
          </div>
        </form>
      </details>

      <div className="panel-card record-panel academic-record-list">
        <div className="section-header">
          <div>
            <p className="eyebrow">Assigned classes</p>
            <h2>Teacher assignment roster</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search assignments" placeholder="Search teacher or section" value={search} onChange={(event) => setSearch(event.target.value)} />
          </div>
        </div>

        <div className="form-grid academic-filters assignment-filters">
          <label>
            <span>Teacher</span>
            <select value={teacherFilter} onChange={(event) => setTeacherFilter(event.target.value)}>
              <option value="">All teachers</option>
              {selectableTeachers.filter((teacher) => teacher.profile?.role_name === 'TEACHER' || teacher.role_name === 'TEACHER').map((teacher) => {
                const displayName = `${(teacher.first_name || '').trim()} ${(teacher.last_name || '').trim()}`.trim() || teacher.username || 'Unknown'
                return (<option key={teacher.id} value={teacher.id}>{displayName}</option>)
              })}
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
              {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}{subject.official_subject_code ? ` (Official: ${subject.official_subject_code})` : ''}{subject.code ? ` (System ID: ${subject.code})` : ''}</option>)}
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
                    <td>
                      {assignment.subject_name || assignment.subject || '—'}
                      {assignment.official_subject_code || assignment.subject_code ? (
                        <small>
                          {assignment.official_subject_code ? `Official: ${assignment.official_subject_code}` : ''}
                          {assignment.official_subject_code && assignment.subject_code ? ' · ' : ''}
                          {assignment.subject_code ? `System ID: ${assignment.subject_code}` : ''}
                        </small>
                      ) : null}
                    </td>
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

import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { createSubject, getAcademicDivisions, getGradeLevels, getStrands, getSubjects, updateSubject } from '../../services/academicsService'
import { SubjectFormFields } from '../../components/academics/SubjectFormFields'
import { notifySubjectsUpdated } from '../../services/referenceService'
import { ExcelImportPanel } from '../../components/common/ExcelImportPanel'
import { useAuth } from '../../context/AuthContext'
import { buildSubjectPayload, createEmptySubjectForm, getSubjectFieldErrors, validateSubjectForm } from '../../services/subjectForm'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function getNameById(items, id) {
  const match = items.find((item) => String(item.id) === String(id))
  return match?.name || match?.code || '—'
}

export function SubjectsPage() {
  const { user } = useAuth()
  const [gradeLevels, setGradeLevels] = useState([])
  const [academicDivisions, setAcademicDivisions] = useState([])
  const [strands, setStrands] = useState([])
  const [strandLoadStatus, setStrandLoadStatus] = useState('loading')
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [subjectStatusMessage, setSubjectStatusMessage] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [educationLevelFilter, setEducationLevelFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState(createEmptySubjectForm())
  const [subjectErrors, setSubjectErrors] = useState({})
  const [subjectFormError, setSubjectFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')
      setStrandLoadStatus('loading')
      try {
        const results = await Promise.allSettled([
          getGradeLevels(),
          getStrands({ active_only: 'true' }),
          getAcademicDivisions(),
          getSubjects({ status: 'all' }),
        ])
        if (!active) return
        const failures = []
        const [gradeResult, strandResult, divisionResult, subjectResult] = results

        if (gradeResult.status === 'fulfilled') {
          setGradeLevels(normalizeListResponse(gradeResult.value).items)
        } else {
          failures.push(getApiErrorMessage(gradeResult.reason))
        }

        if (strandResult.status === 'fulfilled') {
          const strandData = strandResult.value
          const strandItems = Array.isArray(strandData)
            ? strandData
            : Array.isArray(strandData?.results)
              ? strandData.results
              : null
          if (strandItems) {
            setStrands(strandItems)
            setStrandLoadStatus('loaded')
          } else {
            setStrands([])
            setStrandLoadStatus('error')
            failures.push('The strand service returned an unexpected response.')
          }
        } else {
          setStrands([])
          setStrandLoadStatus('error')
          failures.push(getApiErrorMessage(strandResult.reason))
        }

        if (divisionResult.status === 'fulfilled') {
          setAcademicDivisions(Array.isArray(divisionResult.value) ? divisionResult.value : [])
        } else {
          failures.push(getApiErrorMessage(divisionResult.reason))
        }

        if (subjectResult.status === 'fulfilled') {
          setSubjects(normalizeListResponse(subjectResult.value).items)
        } else {
          failures.push(getApiErrorMessage(subjectResult.reason))
        }

        setError(failures.join(' '))
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
        setStrandLoadStatus('error')
      } finally {
        if (active) setLoading(false)
      }
    }

    loadReferences()
    return () => { active = false }
  }, [])

  const filteredSubjects = useMemo(() => {
    const term = search.trim().toLowerCase()
    return subjects.filter((subject) => {
      const applicableGradeIds = subject.grade_levels?.length ? subject.grade_levels : (subject.grade_level ? [subject.grade_level] : [])
      const applicableGradeNames = subject.grade_level_names?.length
        ? subject.grade_level_names.join(' ')
        : applicableGradeIds.map((id) => getNameById(gradeLevels, id)).join(' ')
      const matchesSearch = !term || subject.name.toLowerCase().includes(term) || subject.code.toLowerCase().includes(term) || (subject.official_subject_code || '').toLowerCase().includes(term) || subject.category.toLowerCase().includes(term) || (subject.subject_type || '').toLowerCase().includes(term) || applicableGradeNames.toLowerCase().includes(term) || getNameById(strands, subject.strand).toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(subject.is_active) === statusFilter
      const selectedDivision = academicDivisions.find((division) => division.value === educationLevelFilter)
      const divisionGradeIds = selectedDivision?.grade_levels?.map((grade) => String(grade.id)) || []
      const matchesEducationLevel = educationLevelFilter === 'all'
        || (subject.academic_division && subject.academic_division === educationLevelFilter)
        || applicableGradeIds.some((id) => divisionGradeIds.includes(String(id)))
        || (!applicableGradeIds.length && subject.grade_level_school_level === selectedDivision?.label)
      return matchesSearch && matchesStatus && matchesEducationLevel
    })
  }, [subjects, search, statusFilter, educationLevelFilter, gradeLevels, strands, academicDivisions])

  const pagedSubjects = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredSubjects.slice(start, start + pageSize)
  }, [filteredSubjects, page])

  const totalPages = Math.max(1, Math.ceil(filteredSubjects.length / pageSize))

  async function handleSave(event) {
    event.preventDefault()
    const validationErrors = validateSubjectForm(form, academicDivisions)
    setSubjectErrors(validationErrors)
    setSubjectFormError('')
    if (Object.keys(validationErrors).length) {
      return
    }
    setSaving(true)
    try {
      const payload = buildSubjectPayload(form)
      if (form.id) {
        await updateSubject(form.id, payload)
      } else {
        await createSubject(payload)
      }
      const refreshed = await getSubjects({ status: statusFilter })
      setSubjects(normalizeListResponse(refreshed).items)
      notifySubjectsUpdated()
      setForm(createEmptySubjectForm(educationLevelFilter === 'all' ? '' : educationLevelFilter))
      setSubjectErrors({})
      setSubjectFormError('')
    } catch (err) {
      const { fieldErrors, formError } = getSubjectFieldErrors(err)
      setSubjectErrors(fieldErrors)
      setSubjectFormError(formError)
    } finally {
      setSaving(false)
    }
  }

  function editSubject(subject) {
    setForm({
      id: subject.id,
      code: subject.code || '',
      official_subject_code: subject.official_subject_code || '',
      name: subject.name || '',
      subject_type: subject.subject_type || 'STANDARD',
      category: subject.category || 'Learning Area',
      academic_division: subject.academic_division || '',
      grade_level: subject.grade_level || '',
      grade_levels: subject.grade_levels || (subject.grade_level ? [subject.grade_level] : []),
      strand: subject.strand || '',
      is_active: subject.is_active !== false,
      initial_academic_division: subject.academic_division || '',
      initial_grade_levels: [...(subject.grade_levels || (subject.grade_level ? [subject.grade_level] : []))],
      initial_strand: subject.strand || '',
    })
    setSubjectErrors({})
    setSubjectFormError('')
    setEducationLevelFilter(subject.academic_division || 'all')
    setPage(1)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function resetForm() {
    setForm(createEmptySubjectForm(educationLevelFilter === 'all' ? '' : educationLevelFilter))
    setSubjectErrors({})
    setSubjectFormError('')
  }

  function selectSchoolCategory(value) {
    if (value === educationLevelFilter && form.academic_division === (value === 'all' ? '' : value)) return
    setEducationLevelFilter(value)
    setPage(1)
    setForm((current) => ({
      ...current,
      academic_division: value === 'all' ? '' : value,
      grade_level: '',
      grade_levels: [],
      category: value === 'SENIOR_HIGH_SCHOOL' ? 'Core' : 'Learning Area',
      strand: '',
      official_subject_code: value === 'SENIOR_HIGH_SCHOOL'
        ? current.official_subject_code
        : '',
    }))
    setSubjectErrors({})
    setSubjectFormError('')
  }

  function clearSubjectErrors(fields) {
    setSubjectErrors((current) => Object.fromEntries(
      Object.entries(current).filter(([field]) => !fields.includes(field)),
    ))
    setSubjectFormError('')
  }

  async function changeStatusFilter(value) {
    setStatusFilter(value)
    setPage(1)
    setError('')
    try {
      const refreshed = await getSubjects({ status: value })
      setSubjects(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleStatus(subject) {
    setError('')
    setSubjectStatusMessage('')
    try {
      const updatedSubject = await updateSubject(subject.id, { is_active: !subject.is_active })
      setSubjects((current) => current.map((item) => item.id === updatedSubject.id ? updatedSubject : item))
      setSubjectStatusMessage(`Subject "${subject.name}" ${subject.is_active ? 'archived' : 'restored'}.`)
      notifySubjectsUpdated()
      const refreshed = await getSubjects({ status: statusFilter })
      setSubjects(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack subjects-page">
      <PageHeader eyebrow="Subjects" title="Manage subjects" description="Manage subjects and their grade-level and strand links; these mappings are configurable references." />

      {['SUPER_ADMIN', 'SCHOOL_ADMIN'].includes(user?.role || user?.role_name || user?.profile?.role_name) ? (
        <ExcelImportPanel
          title="Subject registration"
          templateUrl="/subjects/import/template/"
          previewUrl="/subjects/import/preview/"
          confirmUrl="/subjects/import/confirm/"
          filename="edu-assist-subject-import-template.xlsx"
          instructions="Internal subject IDs are generated automatically. Official Subject Code is optional; duplicate-code validation applies to active SHS subjects with overlapping grades only. Only supplied grade-level and strand codes are associated. Existing subjects and inferred curriculum mappings are never overwritten."
          onCompleted={async () => {
            const refreshed = await getSubjects({ status: statusFilter })
            setSubjects(normalizeListResponse(refreshed).items)
            notifySubjectsUpdated()
          }}
        />
      ) : null}

      {error ? <ErrorBanner message={error} /> : null}
      {subjectStatusMessage ? <p className="status-banner status-banner--success" role="status">{subjectStatusMessage}</p> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Subjects</p>
          <p className="stat-value">{subjects.length}</p>
        </article>
      </div>

      <div className="section-actions subject-school-category-filter" role="group" aria-label="Filter subjects by school category">
        <span className="form-field__label">Filter subjects by school category</span>
        <button type="button" className={`action-button ${educationLevelFilter === 'all' ? 'action-button--primary' : 'action-button--secondary'}`} aria-pressed={educationLevelFilter === 'all'} disabled={Boolean(form.id)} onClick={() => selectSchoolCategory('all')}>All subjects</button>
        {academicDivisions.map((division) => (
          <button key={division.value} type="button" className={`action-button ${educationLevelFilter === division.value ? 'action-button--primary' : 'action-button--secondary'}`} aria-pressed={educationLevelFilter === division.value} disabled={Boolean(form.id)} onClick={() => selectSchoolCategory(division.value)}>
            {division.label}
          </button>
        ))}
      </div>

      <details className="academic-editor-panel" open={Boolean(form.id)}>
        <summary className="academic-editor-summary">
          <span>
            <span className="eyebrow">Subject details</span>
            <strong>{form.id ? 'Edit subject' : 'Add new subject'}</strong>
          </span>
          <span className="academic-editor-prompt">{form.id ? 'Close form' : 'Open form'}</span>
        </summary>

        <form className="form-grid subject-form-grid subject-editor-grid" onSubmit={handleSave} noValidate>
          {subjectFormError ? <p className="subject-form-error form-grid-full" role="alert">{subjectFormError}</p> : null}
          <SubjectFormFields
            form={form}
            setForm={setForm}
            academicDivisions={academicDivisions}
            strands={strands}
            strandLoadStatus={strandLoadStatus}
            errors={subjectErrors}
            clearErrors={clearSubjectErrors}
          />
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : form.id ? 'Update subject' : 'Create subject'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={() => resetForm()}>Cancel</button> : null}
          </div>
        </form>
      </details>

      <div className="panel-card record-panel academic-record-list">
        <div className="section-header subject-list-header">
          <div>
            <p className="eyebrow">Subject records</p>
            <h2>Subject list</h2>
            <p className="subject-list-count">{filteredSubjects.length} subject{filteredSubjects.length === 1 ? '' : 's'} found</p>
          </div>
          <div className="search-input-group subject-filters academic-filters">
            <input aria-label="Search subjects" placeholder="Search subjects" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select value={statusFilter} onChange={(event) => changeStatusFilter(event.target.value)}>
              <option value="all">All statuses</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </div>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}

        {!loading && filteredSubjects.length === 0 ? (
          <EmptyState title="No subjects found" message="Add a subject or adjust your filters." />
        ) : null}

        {!loading && filteredSubjects.length > 0 ? (
          <>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">System-generated subject ID</th>
                    <th scope="col">Official Subject Code</th>
                    <th scope="col">Name</th>
                    <th scope="col">Applicable Grade Levels</th>
                    <th scope="col">Subject type</th>
                    <th scope="col">Classification</th>
                    <th scope="col">Strand</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedSubjects.map((subject) => (
                    <tr key={subject.id}>
                      <td>{subject.code || '—'}</td>
                      <td>{subject.official_subject_code || '—'}</td>
                      <td>{subject.name || '—'}</td>
                      <td>{[...new Set(subject.grade_level_names?.length ? subject.grade_level_names : (subject.grade_level_name ? [subject.grade_level_name] : []))].filter(Boolean).join(', ') || 'No grade levels configured'}</td>
                      <td>{subject.subject_type === 'SCHOOL_SPECIFIC' ? 'School-specific' : 'Standard curriculum'}</td>
                      <td>{subject.category || '—'}</td>
                      <td>{subject.strand_name || 'No Strand assigned'}</td>
                      <td><span className={subject.is_active ? 'status-pill status-pill--success' : 'status-pill status-pill--neutral'}>{subject.is_active ? 'Active' : 'Archived'}</span></td>
                      <td>
                        <div className="section-actions" style={{ justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <button type="button" className="action-button action-button--secondary" onClick={() => editSubject(subject)}>Edit</button>
                          <button type="button" className="action-button action-button--outline" onClick={() => toggleStatus(subject)}>{subject.is_active ? 'Archive' : 'Restore'}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--secondary" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={page === 1}>Previous</button>
              <span>Page {page} of {totalPages}</span>
              <button type="button" className="action-button action-button--secondary" onClick={() => setPage((value) => Math.min(totalPages, value + 1))} disabled={page === totalPages}>Next</button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}

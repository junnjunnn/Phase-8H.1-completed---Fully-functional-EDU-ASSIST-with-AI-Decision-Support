import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import {
  createAcademicYear,
  createGradeLevel,
  createSection,
  createSubject,
  getAcademicDivisions,
  getAcademicYears,
  getGradeLevels,
  getSections,
  getSpecializations,
  getStrands,
  getSubjects,
  restoreGradeLevel,
  updateAcademicYear,
  updateGradeLevel,
  updateSection,
  updateSubject,
} from '../../services/academicsService'
import { notifySubjectsUpdated, subscribeSubjectsUpdated, unsubscribeSubjectsUpdated } from '../../services/referenceService'
import AdviserSelect from '../../components/AdviserSelect'
import { SubjectFormFields } from '../../components/academics/SubjectFormFields'
import { buildSubjectPayload, createEmptySubjectForm, getSubjectFieldErrors, validateSubjectForm } from '../../services/subjectForm'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function getNameById(items, id) {
  const match = items.find((item) => String(item.id) === String(id))
  return match?.name || match?.code || '—'
}

export function AcademicStructurePage() {
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [strands, setStrands] = useState([])
  const [strandLoadStatus, setStrandLoadStatus] = useState('loading')
  const [specializations, setSpecializations] = useState([])
  const [subjects, setSubjects] = useState([])
  const [academicDivisions, setAcademicDivisions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [subjectStatusMessage, setSubjectStatusMessage] = useState('')
  const [yearForm, setYearForm] = useState({ id: '', name: '', start_date: '', end_date: '', is_active: false })
  const [gradeForm, setGradeForm] = useState({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
  const [sectionForm, setSectionForm] = useState({ id: '', grade_level: '', strand: '', specialization: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '' })
  const [subjectForm, setSubjectForm] = useState(createEmptySubjectForm())
  const [subjectErrors, setSubjectErrors] = useState({})
  const [subjectFormError, setSubjectFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const [yearSearch, setYearSearch] = useState('')
  const [yearStatusFilter, setYearStatusFilter] = useState('all')
  const [gradeSearch, setGradeSearch] = useState('')
  const [gradeStatusFilter, setGradeStatusFilter] = useState('all')
  const [sectionSearch, setSectionSearch] = useState('')
  const [sectionStatusFilter, setSectionStatusFilter] = useState('all')
  const [subjectSearch, setSubjectSearch] = useState('')
  const [subjectStatusFilter, setSubjectStatusFilter] = useState('all')
  const [yearPage, setYearPage] = useState(1)
  const [gradePage, setGradePage] = useState(1)
  const [sectionPage, setSectionPage] = useState(1)
  const [subjectPage, setSubjectPage] = useState(1)
  const pageSize = 6

  const filteredSections = useMemo(() => {
    return sections.filter((section) => section.is_active !== false)
  }, [sections])

  const filteredAcademicYears = useMemo(() => {
    const term = yearSearch.trim().toLowerCase()
    return academicYears.filter((year) => {
      const matchesSearch = !term || year.name.toLowerCase().includes(term)
      const matchesStatus = yearStatusFilter === 'all' || String(year.is_active) === yearStatusFilter
      return matchesSearch && matchesStatus
    })
  }, [academicYears, yearSearch, yearStatusFilter])

  const filteredGradeLevels = useMemo(() => {
    const term = gradeSearch.trim().toLowerCase()
    return gradeLevels.filter((grade) => {
      const matchesSearch = !term || grade.name.toLowerCase().includes(term) || grade.code.toLowerCase().includes(term)
      const matchesStatus = gradeStatusFilter === 'all' || String(grade.is_active) === gradeStatusFilter
      return matchesSearch && matchesStatus
    })
  }, [gradeLevels, gradeSearch, gradeStatusFilter])

  const filteredSectionRows = useMemo(() => {
    const term = sectionSearch.trim().toLowerCase()
    return sections.filter((section) => {
      const matchesSearch = !term || section.name.toLowerCase().includes(term) || (section.academic_year_name || '').toLowerCase().includes(term) || (section.grade_level_name || '').toLowerCase().includes(term)
      const matchesStatus = sectionStatusFilter === 'all' || String(section.is_active) === sectionStatusFilter
      return matchesSearch && matchesStatus
    })
  }, [sections, sectionSearch, sectionStatusFilter])

  const filteredSubjectRows = useMemo(() => {
    const term = subjectSearch.trim().toLowerCase()
    return subjects.filter((subject) => {
      const matchesSearch = !term || subject.name.toLowerCase().includes(term) || subject.code.toLowerCase().includes(term) || (subject.official_subject_code || '').toLowerCase().includes(term)
      const matchesStatus = subjectStatusFilter === 'all' || String(subject.is_active) === subjectStatusFilter
      return matchesSearch && matchesStatus
    })
  }, [subjects, subjectSearch, subjectStatusFilter])

  const pagedAcademicYears = useMemo(() => {
    const start = (yearPage - 1) * pageSize
    return filteredAcademicYears.slice(start, start + pageSize)
  }, [filteredAcademicYears, yearPage])

  const pagedGradeLevels = useMemo(() => {
    const start = (gradePage - 1) * pageSize
    return filteredGradeLevels.slice(start, start + pageSize)
  }, [filteredGradeLevels, gradePage])

  const pagedSections = useMemo(() => {
    const start = (sectionPage - 1) * pageSize
    return filteredSectionRows.slice(start, start + pageSize)
  }, [filteredSectionRows, sectionPage])

  const pagedSubjects = useMemo(() => {
    const start = (subjectPage - 1) * pageSize
    return filteredSubjectRows.slice(start, start + pageSize)
  }, [filteredSubjectRows, subjectPage])

  const academicYearPages = Math.max(1, Math.ceil(filteredAcademicYears.length / pageSize))
  const gradeLevelPages = Math.max(1, Math.ceil(filteredGradeLevels.length / pageSize))
  const sectionPages = Math.max(1, Math.ceil(filteredSectionRows.length / pageSize))
  const subjectPages = Math.max(1, Math.ceil(filteredSubjectRows.length / pageSize))
  const selectedSectionGrade = gradeLevels.find((grade) => String(grade.id) === String(sectionForm.grade_level))
  const activeYearCount = academicYears.filter((year) => year.is_active).length
  const selectableSectionGrades = gradeLevels.filter((grade) =>
    grade.is_active !== false || (sectionForm.id && String(grade.id) === String(sectionForm.grade_level)),
  )
  const selectableSectionStrands = strands.filter((strand) =>
    strand.is_active || (sectionForm.id && String(strand.id) === String(sectionForm.strand)),
  )
  const selectableSectionSpecializations = specializations.filter((specialization) =>
    (specialization.is_active && String(specialization.strand) === String(sectionForm.strand)) ||
    (sectionForm.id && String(specialization.id) === String(sectionForm.specialization)),
  )
  const sectionRequiresSpecialization = selectableSectionStrands.find(
    (strand) => String(strand.id) === String(sectionForm.strand),
  )?.code === 'TVL'

  useEffect(() => {
    async function loadReferenceData() {
      setLoading(true)
      setError('')
      setStrandLoadStatus('loading')
      try {
        const results = await Promise.allSettled([
          getAcademicYears({ status: 'all' }),
          getGradeLevels({ status: 'all' }),
          getSections({ status: 'all' }),
          getStrands({ active_only: 'true' }),
          getSpecializations(),
          getAcademicDivisions(),
          getSubjects({ status: 'all' }),
        ])
        const failures = []
        const [yearsResult, gradeResult, sectionResult, strandResult, specializationResult, divisionResult, subjectResult] = results

        if (yearsResult.status === 'fulfilled') {
          setAcademicYears(normalizeListResponse(yearsResult.value).items)
        } else {
          failures.push(getApiErrorMessage(yearsResult.reason))
        }

        if (gradeResult.status === 'fulfilled') {
          setGradeLevels(normalizeListResponse(gradeResult.value).items)
        } else {
          failures.push(getApiErrorMessage(gradeResult.reason))
        }

        if (sectionResult.status === 'fulfilled') {
          setSections(normalizeListResponse(sectionResult.value).items)
        } else {
          failures.push(getApiErrorMessage(sectionResult.reason))
        }

        if (strandResult.status === 'rejected') {
          setStrands([])
          setStrandLoadStatus('error')
          failures.push(getApiErrorMessage(strandResult.reason))
        } else {
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
        }

        if (specializationResult.status === 'fulfilled') {
          setSpecializations(normalizeListResponse(specializationResult.value).items)
        } else {
          failures.push(getApiErrorMessage(specializationResult.reason))
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
        setStrandLoadStatus('error')
        setError(getApiErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    loadReferenceData()
  }, [])

  useEffect(() => {
    let active = true

    async function reloadSubjects() {
      try {
        const refreshed = await getSubjects({ status: subjectStatusFilter })
        if (!active) {
          return
        }
        setSubjects(normalizeListResponse(refreshed).items)
      } catch {
        setError('Could not refresh the subject list. Please try again.')
      }
    }

    function handleSubjectsUpdated() {
      reloadSubjects()
    }

    subscribeSubjectsUpdated(handleSubjectsUpdated)
    return () => {
      active = false
      unsubscribeSubjectsUpdated(handleSubjectsUpdated)
    }
  }, [subjectStatusFilter])

  async function handleYearSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (yearForm.id) {
        await updateAcademicYear(yearForm.id, yearForm)
      } else {
        await createAcademicYear(yearForm)
      }
      const refreshed = await getAcademicYears({ status: 'all' })
      const refreshedYears = normalizeListResponse(refreshed).items
      setAcademicYears(refreshedYears)
      setYearForm({ id: '', name: '', start_date: '', end_date: '', is_active: false })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleGradeSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (gradeForm.id) {
        await updateGradeLevel(gradeForm.id, gradeForm)
      } else {
        await createGradeLevel(gradeForm)
      }
      const refreshed = await getGradeLevels({ status: 'all' })
      setGradeLevels(normalizeListResponse(refreshed).items)
      setGradeForm({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleSectionSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        grade_level: sectionForm.grade_level,
        name: sectionForm.name,
        capacity: Number(sectionForm.capacity || 0),
        description: sectionForm.description,
        adviser: sectionForm.adviser || null,
        strand: sectionForm.strand || null,
        specialization: sectionForm.specialization || null,
      }
      if (sectionForm.id) {
        await updateSection(sectionForm.id, payload)
      } else {
        await createSection(payload)
      }
      const refreshed = await getSections({ status: 'all' })
      setSections(normalizeListResponse(refreshed).items)
      resetSectionForm()
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function resetSectionForm() {
    setSectionForm({ id: '', grade_level: '', strand: '', specialization: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '' })
  }

  async function handleSubjectSubmit(event) {
    event.preventDefault()
    const validationErrors = validateSubjectForm(subjectForm, academicDivisions)
    setSubjectErrors(validationErrors)
    setSubjectFormError('')
    if (Object.keys(validationErrors).length) return

    setSaving(true)
    try {
      const payload = buildSubjectPayload(subjectForm)
      if (subjectForm.id) {
        await updateSubject(subjectForm.id, payload)
      } else {
        await createSubject(payload)
      }
      const refreshed = await getSubjects({ status: subjectStatusFilter })
      setSubjects(normalizeListResponse(refreshed).items)
      notifySubjectsUpdated()
      resetSubjectForm()
    } catch (err) {
      const { fieldErrors, formError } = getSubjectFieldErrors(err)
      setSubjectErrors(fieldErrors)
      setSubjectFormError(formError)
    } finally {
      setSaving(false)
    }
  }

  function resetSubjectForm() {
    setSubjectForm(createEmptySubjectForm())
    setSubjectErrors({})
    setSubjectFormError('')
  }

  async function changeSubjectStatusFilter(value) {
    setSubjectStatusFilter(value)
    setSubjectPage(1)
    setError('')
    try {
      const refreshed = await getSubjects({ status: value })
      setSubjects(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  function clearSubjectErrors(fields) {
    setSubjectErrors((current) => Object.fromEntries(
      Object.entries(current).filter(([field]) => !fields.includes(field)),
    ))
    setSubjectFormError('')
  }

  function startYearEdit(year) {
    setYearForm({ id: year.id, name: year.name, start_date: year.start_date || '', end_date: year.end_date || '', is_active: Boolean(year.is_active) })
  }

  function startGradeEdit(grade) {
    setGradeForm({ id: grade.id, name: grade.name, code: grade.code, school_level: grade.school_level || 'Elementary', order: Number(grade.order || 1), is_active: Boolean(grade.is_active) })
  }

  function startSectionEdit(section) {
    if (section.specialization && !specializations.some((item) => String(item.id) === String(section.specialization))) {
      setSpecializations((current) => [
        ...current,
        { id: section.specialization, strand: section.strand, name: section.specialization_name || 'Historical specialization', is_active: false },
      ])
    }
    setSectionForm({
      id: section.id,
      grade_level: section.grade_level || '',
      strand: section.strand || '',
      specialization: section.specialization || '',
      name: section.name || '',
      capacity: Number(section.capacity || 0),
      description: section.description || '',
      adviser: section.adviser || '',
      adviser_name: section.adviser_name || '',
    })
  }

  function startSubjectEdit(subject) {
    setSubjectForm({
      id: subject.id,
      code: subject.code || '',
      official_subject_code: subject.official_subject_code || '',
      name: subject.name || '',
      category: subject.category || 'Learning Area',
      academic_division: subject.academic_division || '',
      grade_level: subject.grade_level || '',
      grade_levels: subject.grade_levels || (subject.grade_level ? [subject.grade_level] : []),
      strand: subject.strand || '',
      is_active: subject.is_active !== false,
      subject_type: subject.subject_type || 'STANDARD',
      initial_academic_division: subject.academic_division || '',
      initial_grade_levels: [...(subject.grade_levels || (subject.grade_level ? [subject.grade_level] : []))],
      initial_strand: subject.strand || '',
    })
    setSubjectErrors({})
    setSubjectFormError('')
  }

  async function toggleAcademicYearStatus(year) {
    try {
      await updateAcademicYear(year.id, { is_active: !year.is_active })
      const refreshed = await getAcademicYears({ status: 'all' })
      const refreshedYears = normalizeListResponse(refreshed).items
      setAcademicYears(refreshedYears)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleGradeStatus(grade) {
    try {
      if (grade.is_active) {
        await updateGradeLevel(grade.id, { is_active: false })
      } else {
        await restoreGradeLevel(grade.id)
      }
      const refreshed = await getGradeLevels({ status: 'all' })
      setGradeLevels(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleSectionStatus(section) {
    try {
      await updateSection(section.id, { is_active: !section.is_active })
      const refreshed = await getSections({ status: 'all' })
      setSections(normalizeListResponse(refreshed).items)
      if (String(sectionForm.id) === String(section.id)) resetSectionForm()
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleSubjectStatus(subject) {
    setError('')
    setSubjectStatusMessage('')
    try {
      const updatedSubject = await updateSubject(subject.id, { is_active: !subject.is_active })
      setSubjects((current) => current.map((item) => item.id === updatedSubject.id ? updatedSubject : item))
      setSubjectStatusMessage(`Subject "${subject.name}" ${subject.is_active ? 'archived' : 'restored'}.`)
      notifySubjectsUpdated()
      const refreshed = await getSubjects({ status: subjectStatusFilter })
      setSubjects(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Academic Management" title="Academic structure management" description="Configure academic years, grade levels, and sections for the school." />

      {error ? <ErrorBanner message={error} /> : null}
      {subjectStatusMessage ? <p className="status-banner status-banner--success" role="status">{subjectStatusMessage}</p> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic years</p>
          <p className="stat-value">{academicYears.length}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Grade levels</p>
          <p className="stat-value">{gradeLevels.length}</p>
        </article>
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Sections</p>
          <p className="stat-value">{filteredSections.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic years</p>
            <h2>Manage school years</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleYearSubmit}>
          <label>
            <span>School year</span>
            <input value={yearForm.name} onChange={(event) => setYearForm({ ...yearForm, name: event.target.value })} required />
          </label>
          <label>
            <span>Start date</span>
            <input type="date" value={yearForm.start_date} onChange={(event) => setYearForm({ ...yearForm, start_date: event.target.value })} required />
          </label>
          <label>
            <span>End date</span>
            <input type="date" value={yearForm.end_date} onChange={(event) => setYearForm({ ...yearForm, end_date: event.target.value })} required />
          </label>
          <label>
            <span>Active</span>
            <select value={yearForm.is_active ? 'true' : 'false'} onChange={(event) => setYearForm({ ...yearForm, is_active: event.target.value === 'true' })}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>
          <div className="section-actions">
            <button type="submit" className="action-button" disabled={saving}>{saving ? 'Saving...' : yearForm.id ? 'Update year' : 'Create year'}</button>
            {yearForm.id ? <button type="button" className="action-button action-button--neutral" onClick={() => setYearForm({ id: '', name: '', start_date: '', end_date: '', is_active: false })}>Cancel</button> : null}
          </div>
        </form>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Search</span>
            <input value={yearSearch} onChange={(event) => { setYearSearch(event.target.value); setYearPage(1) }} placeholder="Search academic year" />
          </label>
          <label>
            <span>Status</span>
            <select value={yearStatusFilter} onChange={(event) => { setYearStatusFilter(event.target.value); setYearPage(1) }}>
              <option value="all">All</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
        {!loading && filteredAcademicYears.length === 0 ? <EmptyState title="No academic years" message="No academic years match the current filters." /> : null}
        {!loading && filteredAcademicYears.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">School year</th>
                  <th scope="col">Status</th>
                  <th scope="col">Start</th>
                  <th scope="col">End</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedAcademicYears.map((year) => (
                  <tr key={year.id}>
                    <td>{year.name}</td>
                    <td>{year.is_active ? 'Active' : 'Archived'}</td>
                    <td>{year.start_date}</td>
                    <td>{year.end_date}</td>
                    <td>
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <button type="button" className="action-button action-button--neutral" onClick={() => startYearEdit(year)}>Edit</button>
                        <button type="button" className="action-button action-button--neutral" onClick={() => toggleAcademicYearStatus(year)}>{year.is_active ? 'Archive' : 'Restore'}</button>
                        {!year.is_active ? <button type="button" className="action-button" onClick={() => toggleAcademicYearStatus({ ...year, is_active: false })}>Activate</button> : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--neutral" onClick={() => setYearPage((current) => Math.max(1, current - 1))} disabled={yearPage === 1}>Previous</button>
              <span style={{ alignSelf: 'center' }}>Page {yearPage} of {academicYearPages}</span>
              <button type="button" className="action-button action-button--neutral" onClick={() => setYearPage((current) => Math.min(academicYearPages, current + 1))} disabled={yearPage === academicYearPages}>Next</button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Grade levels</p>
            <h2>Manage grade levels</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleGradeSubmit}>
          <label>
            <span>Name</span>
            <input value={gradeForm.name} onChange={(event) => setGradeForm({ ...gradeForm, name: event.target.value })} required />
          </label>
          <label>
            <span>Code</span>
            <input value={gradeForm.code} onChange={(event) => setGradeForm({ ...gradeForm, code: event.target.value })} required />
          </label>
          <label>
            <span>School level</span>
            <select value={gradeForm.school_level} onChange={(event) => setGradeForm({ ...gradeForm, school_level: event.target.value })}>
              <option value="Elementary">Elementary</option>
              <option value="Junior High School">Junior High School</option>
              <option value="Senior High School">Senior High School</option>
            </select>
          </label>
          <label>
            <span>Order</span>
            <input type="number" value={gradeForm.order} onChange={(event) => setGradeForm({ ...gradeForm, order: Number(event.target.value) })} required />
          </label>
          <label>
            <span>Active</span>
            <select value={gradeForm.is_active ? 'true' : 'false'} onChange={(event) => setGradeForm({ ...gradeForm, is_active: event.target.value === 'true' })}>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>
          <div className="section-actions">
            <button type="submit" className="action-button" disabled={saving}>{saving ? 'Saving...' : gradeForm.id ? 'Update grade' : 'Create grade'}</button>
            {gradeForm.id ? <button type="button" className="action-button action-button--neutral" onClick={() => setGradeForm({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })}>Cancel</button> : null}
          </div>
        </form>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Search</span>
            <input value={gradeSearch} onChange={(event) => { setGradeSearch(event.target.value); setGradePage(1) }} placeholder="Search grade level" />
          </label>
          <label>
            <span>Status</span>
            <select value={gradeStatusFilter} onChange={(event) => { setGradeStatusFilter(event.target.value); setGradePage(1) }}>
              <option value="all">All</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
        </div>

        {!loading && filteredGradeLevels.length === 0 ? <EmptyState title="No grade levels" message="No grade levels match the current filters." /> : null}
        {!loading && filteredGradeLevels.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">System-generated subject ID</th>
                  <th scope="col">Official Subject Code</th>
                  <th scope="col">Order</th>
                  <th scope="col">School level</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedGradeLevels.map((grade) => (
                  <tr key={grade.id}>
                    <td>{grade.name}</td>
                    <td>{grade.code}</td>
                    <td>{grade.order || 1}</td>
                    <td>{grade.school_level}</td>
                    <td>{grade.is_active ? 'Active' : 'Archived'}</td>
                    <td>
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <button type="button" className="action-button action-button--neutral" onClick={() => startGradeEdit(grade)}>Edit</button>
                        <button type="button" className="action-button action-button--neutral" onClick={() => toggleGradeStatus(grade)}>{grade.is_active ? 'Archive' : 'Restore'}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--neutral" onClick={() => setGradePage((current) => Math.max(1, current - 1))} disabled={gradePage === 1}>Previous</button>
              <span style={{ alignSelf: 'center' }}>Page {gradePage} of {gradeLevelPages}</span>
              <button type="button" className="action-button action-button--neutral" onClick={() => setGradePage((current) => Math.min(gradeLevelPages, current + 1))} disabled={gradePage === gradeLevelPages}>Next</button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Sections</p>
            <h2>Manage sections</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleSectionSubmit}>
          {!sectionForm.id && activeYearCount !== 1 ? (
            <div className="status-banner status-banner--warning form-grid-full">
              {activeYearCount === 0
                ? 'No active academic year is configured. '
                : 'More than one active academic year is configured. '}
              <Link to="/academic-years">Configure Academic Year Management before creating sections.</Link>
            </div>
          ) : null}
          <label>
            <span>Grade level</span>
            <select value={sectionForm.grade_level} onChange={(event) => {
              const grade = gradeLevels.find((item) => String(item.id) === event.target.value)
              setSectionForm((current) => ({
                ...current,
                grade_level: event.target.value,
                strand: grade?.school_level === 'Senior High School' ? current.strand : '',
                specialization: grade?.school_level === 'Senior High School' ? current.specialization : '',
              }))
            }} required>
              <option value="">Select</option>
              {selectableSectionGrades.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}{grade.is_active === false ? ' (Archived)' : ''}</option>)}
            </select>
          </label>
          {selectedSectionGrade?.school_level === 'Senior High School' ? (
            <>
              <label>
                <span>Section strand (optional)</span>
                <select value={sectionForm.strand} onChange={(event) => setSectionForm({ ...sectionForm, strand: event.target.value, specialization: '' })}>
                  <option value="">Shared section - no single strand</option>
                  {selectableSectionStrands.map((strand) => <option key={strand.id} value={strand.id}>{strand.name}{strand.is_active === false ? ' (Archived)' : ''}</option>)}
                </select>
                <small className="small-muted">Leave blank when students from multiple strands share this section.</small>
              </label>
              <label>
                <span>Specialization{sectionRequiresSpecialization ? ' *' : ''}</span>
                <select value={sectionForm.specialization} onChange={(event) => setSectionForm({ ...sectionForm, specialization: event.target.value })} disabled={!sectionForm.strand} required={sectionRequiresSpecialization}>
                  <option value="">{sectionForm.strand ? 'Select specialization' : 'Not applicable to a shared section'}</option>
                  {selectableSectionSpecializations.map((specialization) => <option key={specialization.id} value={specialization.id}>{specialization.name}{specialization.is_active === false ? ' (Archived)' : ''}</option>)}
                </select>
              </label>
            </>
          ) : null}
          <label>
            <span>Section name</span>
            <input value={sectionForm.name} onChange={(event) => setSectionForm({ ...sectionForm, name: event.target.value })} required />
          </label>
          <label>
            <span>Capacity</span>
            <input type="number" min="1" value={sectionForm.capacity} onChange={(event) => setSectionForm({ ...sectionForm, capacity: Number(event.target.value) })} required />
          </label>
          <label>
            <span>Adviser</span>
            <AdviserSelect
              value={sectionForm.adviser || ''}
              initialLabel={sectionForm.adviser_name || ''}
              onChange={(id) => setSectionForm({ ...sectionForm, adviser: id })}
            />
            <div style={{ marginTop: '0.25rem' }} className="small-muted">Leave empty to keep unassigned</div>
          </label>
          <label className="form-grid-full">
            <span>Description</span>
            <textarea value={sectionForm.description} onChange={(event) => setSectionForm({ ...sectionForm, description: event.target.value })} />
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={saving || (!sectionForm.id && activeYearCount !== 1)}>{saving ? 'Saving...' : sectionForm.id ? 'Update section' : 'Create section'}</button>
            {sectionForm.id ? <button type="button" className="action-button action-button--neutral" onClick={resetSectionForm}>Cancel</button> : null}
          </div>
        </form>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Search</span>
            <input value={sectionSearch} onChange={(event) => { setSectionSearch(event.target.value); setSectionPage(1) }} placeholder="Search section" />
          </label>
          <label>
            <span>Status</span>
            <select value={sectionStatusFilter} onChange={(event) => { setSectionStatusFilter(event.target.value); setSectionPage(1) }}>
              <option value="all">All</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
        </div>

        {!loading && filteredSectionRows.length === 0 ? <EmptyState title="No sections" message="No sections match the current filters." /> : null}
        {!loading && filteredSectionRows.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Section</th>
                  <th scope="col">Year</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Section strand</th>
                  <th scope="col">Capacity</th>
                  <th scope="col">Adviser</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedSections.map((section) => (
                  <tr key={section.id}>
                    <td>{section.name}</td>
                    <td>{section.academic_year_name || section.academic_year || '—'}</td>
                    <td>{section.grade_level_name || section.grade_level || '—'}</td>
                    <td>{section.strand_name || (section.grade_level_school_level === 'Senior High School' ? 'Shared section' : 'Not applicable')}</td>
                    <td>{section.capacity || 0}</td>
                    <td>{section.adviser_name || section.adviser || 'Unassigned'}</td>
                    <td>{section.is_active ? 'Active' : 'Archived'}</td>
                    <td>
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <button type="button" className="action-button action-button--neutral" onClick={() => startSectionEdit(section)}>Edit</button>
                        <button type="button" className="action-button action-button--neutral" onClick={() => toggleSectionStatus(section)}>{section.is_active ? 'Archive' : 'Restore'}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--neutral" onClick={() => setSectionPage((current) => Math.max(1, current - 1))} disabled={sectionPage === 1}>Previous</button>
              <span style={{ alignSelf: 'center' }}>Page {sectionPage} of {sectionPages}</span>
              <button type="button" className="action-button action-button--neutral" onClick={() => setSectionPage((current) => Math.min(sectionPages, current + 1))} disabled={sectionPage === sectionPages}>Next</button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Subjects</p>
            <h2>Manage learning areas and specializations</h2>
          </div>
        </div>

        <form className="form-grid subject-editor-grid" onSubmit={handleSubjectSubmit} noValidate>
          {subjectFormError ? <p className="subject-form-error form-grid-full" role="alert">{subjectFormError}</p> : null}
          <SubjectFormFields
            form={subjectForm}
            setForm={setSubjectForm}
            academicDivisions={academicDivisions}
            strands={strands}
            strandLoadStatus={strandLoadStatus}
            errors={subjectErrors}
            clearErrors={clearSubjectErrors}
          />
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : subjectForm.id ? 'Update subject' : 'Create subject'}</button>
            {subjectForm.id ? <button type="button" className="action-button action-button--neutral" onClick={resetSubjectForm}>Cancel</button> : null}
          </div>
        </form>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Search</span>
            <input value={subjectSearch} onChange={(event) => { setSubjectSearch(event.target.value); setSubjectPage(1) }} placeholder="Search subject" />
          </label>
          <label>
            <span>Status</span>
            <select value={subjectStatusFilter} onChange={(event) => changeSubjectStatusFilter(event.target.value)}>
              <option value="all">All</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
        </div>

        {!loading && filteredSubjectRows.length === 0 ? <EmptyState title="No subjects" message="No subjects match the current filters." /> : null}
        {!loading && filteredSubjectRows.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">System-generated subject ID</th>
                  <th scope="col">Official Subject Code</th>
                  <th scope="col">Name</th>
                  <th scope="col">Category</th>
                  <th scope="col">Applicable Grade Levels</th>
                  <th scope="col">Strand</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedSubjects.map((subject) => (
                  <tr key={subject.id}>
                    <td>{subject.code}</td>
                    <td>{subject.official_subject_code || '—'}</td>
                    <td>{subject.name}</td>
                    <td>{subject.category}</td>
                    <td>{[...new Set(subject.grade_level_names?.length ? subject.grade_level_names : (subject.grade_level_name ? [subject.grade_level_name] : []))].filter(Boolean).join(', ') || 'No grade levels configured'}</td>
                    <td>{subject.strand_name || 'No Strand assigned'}</td>
                    <td>{subject.is_active ? 'Active' : 'Archived'}</td>
                    <td>
                      <div className="section-actions" style={{ gap: '0.5rem' }}>
                        <button type="button" className="action-button action-button--neutral" onClick={() => startSubjectEdit(subject)}>Edit</button>
                        <button type="button" className="action-button action-button--neutral" onClick={() => toggleSubjectStatus(subject)}>{subject.is_active ? 'Archive' : 'Restore'}</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="section-actions" style={{ justifyContent: 'flex-end', marginTop: '1rem' }}>
              <button type="button" className="action-button action-button--neutral" onClick={() => setSubjectPage((current) => Math.max(1, current - 1))} disabled={subjectPage === 1}>Previous</button>
              <span style={{ alignSelf: 'center' }}>Page {subjectPage} of {subjectPages}</span>
              <button type="button" className="action-button action-button--neutral" onClick={() => setSubjectPage((current) => Math.min(subjectPages, current + 1))} disabled={subjectPage === subjectPages}>Next</button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import {
  createAcademicYear,
  createGradeLevel,
  createSection,
  createSubject,
  getAcademicYears,
  getGradeLevels,
  getSections,
  getStrands,
  getSubjects,
  updateAcademicYear,
  updateGradeLevel,
  updateSection,
  updateSubject,
} from '../../services/academicsService'
import { getUsers as getUserProfiles } from '../../services/userService'

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
  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [yearForm, setYearForm] = useState({ id: '', name: '', start_date: '', end_date: '', is_active: false })
  const [gradeForm, setGradeForm] = useState({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
  const [sectionForm, setSectionForm] = useState({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', is_active: true })
  const [subjectForm, setSubjectForm] = useState({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })
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
      const matchesSearch = !term || subject.name.toLowerCase().includes(term) || subject.code.toLowerCase().includes(term)
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

  useEffect(() => {
    async function loadReferenceData() {
      setLoading(true)
      setError('')
      try {
        const [yearsData, gradeData, sectionData, strandData, subjectData, teacherData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getStrands(),
          getSubjects(),
          getUserProfiles(),
        ])
        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
        setSections(normalizeListResponse(sectionData).items)
        setStrands(normalizeListResponse(strandData).items)
        setSubjects(normalizeListResponse(subjectData).items)
        setTeachers(normalizeListResponse(teacherData).items || [])
      } catch (err) {
        setError(getApiErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    loadReferenceData()
  }, [])

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
      const refreshed = await getAcademicYears()
      setAcademicYears(normalizeListResponse(refreshed).items)
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
      const refreshed = await getGradeLevels()
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
        ...sectionForm,
        capacity: Number(sectionForm.capacity || 0),
        adviser: sectionForm.adviser || null,
      }
      if (sectionForm.id) {
        await updateSection(sectionForm.id, payload)
      } else {
        await createSection(payload)
      }
      const refreshed = await getSections()
      setSections(normalizeListResponse(refreshed).items)
      setSectionForm({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleSubjectSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...subjectForm,
        grade_level: subjectForm.grade_level || null,
        strand: subjectForm.strand || null,
      }
      if (subjectForm.id) {
        await updateSubject(subjectForm.id, payload)
      } else {
        await createSubject(payload)
      }
      const refreshed = await getSubjects()
      setSubjects(normalizeListResponse(refreshed).items)
      setSubjectForm({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function startYearEdit(year) {
    setYearForm({ id: year.id, name: year.name, start_date: year.start_date || '', end_date: year.end_date || '', is_active: Boolean(year.is_active) })
  }

  function startGradeEdit(grade) {
    setGradeForm({ id: grade.id, name: grade.name, code: grade.code, school_level: grade.school_level || 'Elementary', order: Number(grade.order || 1), is_active: Boolean(grade.is_active) })
  }

  function startSectionEdit(section) {
    setSectionForm({
      id: section.id,
      academic_year: section.academic_year || '',
      grade_level: section.grade_level || '',
      name: section.name || '',
      capacity: Number(section.capacity || 0),
      description: section.description || '',
      adviser: section.adviser || '',
      is_active: section.is_active !== false,
    })
  }

  function startSubjectEdit(subject) {
    setSubjectForm({
      id: subject.id,
      code: subject.code || '',
      name: subject.name || '',
      category: subject.category || 'Learning Area',
      grade_level: subject.grade_level || '',
      strand: subject.strand || '',
      is_active: subject.is_active !== false,
    })
  }

  async function toggleAcademicYearStatus(year) {
    try {
      await updateAcademicYear(year.id, { is_active: !year.is_active })
      const refreshed = await getAcademicYears()
      setAcademicYears(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleGradeStatus(grade) {
    try {
      await updateGradeLevel(grade.id, { is_active: !grade.is_active })
      const refreshed = await getGradeLevels()
      setGradeLevels(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleSectionStatus(section) {
    try {
      await updateSection(section.id, { is_active: !section.is_active })
      const refreshed = await getSections()
      setSections(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  async function toggleSubjectStatus(subject) {
    try {
      await updateSubject(subject.id, { is_active: !subject.is_active })
      const refreshed = await getSubjects()
      setSubjects(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Academic Management" title="Academic structure management" description="Configure academic years, grade levels, and sections for the school." />

      {error ? <ErrorBanner message={error} /> : null}

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
                  <th scope="col">Code</th>
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
          <label>
            <span>Academic year</span>
            <select value={sectionForm.academic_year} onChange={(event) => setSectionForm({ ...sectionForm, academic_year: event.target.value })} required>
              <option value="">Select</option>
              {academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={sectionForm.grade_level} onChange={(event) => setSectionForm({ ...sectionForm, grade_level: event.target.value })} required>
              <option value="">Select</option>
              {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
            </select>
          </label>
          <label>
            <span>Section name</span>
            <input value={sectionForm.name} onChange={(event) => setSectionForm({ ...sectionForm, name: event.target.value })} required />
          </label>
          <label>
            <span>Capacity</span>
            <input type="number" value={sectionForm.capacity} onChange={(event) => setSectionForm({ ...sectionForm, capacity: Number(event.target.value) })} />
          </label>
          <label>
            <span>Adviser</span>
            <select value={sectionForm.adviser} onChange={(event) => setSectionForm({ ...sectionForm, adviser: event.target.value })}>
              <option value="">Unassigned</option>
              {teachers.filter((teacher) => teacher.profile?.role_name === 'TEACHER' || teacher.role_name === 'TEACHER').map((teacher) => (
                <option key={teacher.id} value={teacher.id}>{teacher.first_name} {teacher.last_name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={sectionForm.is_active ? 'true' : 'false'} onChange={(event) => setSectionForm({ ...sectionForm, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
          <label className="form-grid-full">
            <span>Description</span>
            <textarea value={sectionForm.description} onChange={(event) => setSectionForm({ ...sectionForm, description: event.target.value })} />
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={saving}>{saving ? 'Saving...' : sectionForm.id ? 'Update section' : 'Create section'}</button>
            {sectionForm.id ? <button type="button" className="action-button action-button--neutral" onClick={() => setSectionForm({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', is_active: true })}>Cancel</button> : null}
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

        <form className="form-grid" onSubmit={handleSubjectSubmit}>
          <label>
            <span>Subject code</span>
            <input value={subjectForm.code} onChange={(event) => setSubjectForm({ ...subjectForm, code: event.target.value })} required />
          </label>
          <label>
            <span>Subject name</span>
            <input value={subjectForm.name} onChange={(event) => setSubjectForm({ ...subjectForm, name: event.target.value })} required />
          </label>
          <label>
            <span>Category</span>
            <select value={subjectForm.category} onChange={(event) => setSubjectForm({ ...subjectForm, category: event.target.value })}>
              <option value="Learning Area">Learning Area</option>
              <option value="Core">Core</option>
              <option value="Applied">Applied</option>
              <option value="Specialized">Specialized</option>
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={subjectForm.grade_level} onChange={(event) => setSubjectForm({ ...subjectForm, grade_level: event.target.value })}>
              <option value="">All grades</option>
              {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
            </select>
          </label>
          <label>
            <span>Strand</span>
            <select value={subjectForm.strand} onChange={(event) => setSubjectForm({ ...subjectForm, strand: event.target.value })}>
              <option value="">No strand</option>
              {strands.map((strand) => <option key={strand.id} value={strand.id}>{strand.name}</option>)}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={subjectForm.is_active ? 'true' : 'false'} onChange={(event) => setSubjectForm({ ...subjectForm, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button" disabled={saving}>{saving ? 'Saving...' : subjectForm.id ? 'Update subject' : 'Create subject'}</button>
            {subjectForm.id ? <button type="button" className="action-button action-button--neutral" onClick={() => setSubjectForm({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })}>Cancel</button> : null}
          </div>
        </form>

        <div className="form-grid" style={{ marginBottom: '1rem' }}>
          <label>
            <span>Search</span>
            <input value={subjectSearch} onChange={(event) => { setSubjectSearch(event.target.value); setSubjectPage(1) }} placeholder="Search subject" />
          </label>
          <label>
            <span>Status</span>
            <select value={subjectStatusFilter} onChange={(event) => { setSubjectStatusFilter(event.target.value); setSubjectPage(1) }}>
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
                  <th scope="col">Code</th>
                  <th scope="col">Name</th>
                  <th scope="col">Category</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Status</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody>
                {pagedSubjects.map((subject) => (
                  <tr key={subject.id}>
                    <td>{subject.code}</td>
                    <td>{subject.name}</td>
                    <td>{subject.category}</td>
                    <td>{getNameById(gradeLevels, subject.grade_level)}</td>
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

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import AdviserSelect from '../../components/AdviserSelect'
import { ExcelImportPanel } from '../../components/common/ExcelImportPanel'
import { getApiErrorMessage } from '../../services/api'
import { createSection, getAcademicYears, getGradeLevels, getSections, getSpecializations, getStrands, updateSection } from '../../services/academicsService'
import { useAuth } from '../../context/AuthContext'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function getNameById(items, id) {
  const match = items.find((item) => String(item.id) === String(id))
  return match?.name || match?.code || '—'
}

export function SectionsPage() {
  const { user } = useAuth()
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [strands, setStrands] = useState([])
  const [specializations, setSpecializations] = useState([])
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('true')
  const [gradeFilter, setGradeFilter] = useState('')
  const [strandFilter, setStrandFilter] = useState('')
  const [specializationFilter, setSpecializationFilter] = useState('')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', grade_level: '', strand: '', specialization: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '' })
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  function resetForm() {
    setForm({ id: '', grade_level: '', strand: '', specialization: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '' })
  }

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')
      try {
        const [yearsData, gradeData, strandsData, specializationsData, sectionsData] = await Promise.all([
          getAcademicYears({ status: 'all' }),
          getGradeLevels({ status: 'all' }),
          getStrands(),
          getSpecializations(),
          getSections({ status: 'all' }),
        ])
        if (!active) return
        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
        setStrands(normalizeListResponse(strandsData).items)
        setSpecializations(normalizeListResponse(specializationsData).items)
        setSections(normalizeListResponse(sectionsData).items)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadReferences()
    return () => { active = false }
  }, [])

  const filteredSections = useMemo(() => {
    const term = search.trim().toLowerCase()
    return sections.filter((section) => {
      const matchesSearch = !term || section.name.toLowerCase().includes(term) || getNameById(academicYears, section.academic_year).toLowerCase().includes(term) || getNameById(gradeLevels, section.grade_level).toLowerCase().includes(term) || getNameById(strands, section.strand).toLowerCase().includes(term) || getNameById(specializations, section.specialization).toLowerCase().includes(term) || (section.adviser || '').toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(section.is_active) === statusFilter
      const matchesGrade = !gradeFilter || String(section.grade_level) === gradeFilter
      const isSharedShsSection = !section.strand &&
        gradeLevels.find((grade) => String(grade.id) === String(section.grade_level))?.school_level === 'Senior High School'
      const matchesStrand = !strandFilter || isSharedShsSection || String(section.strand) === strandFilter
      const matchesSpecialization = !specializationFilter || String(section.specialization) === specializationFilter
      return matchesSearch && matchesStatus && matchesGrade && matchesStrand && matchesSpecialization
    })
  }, [sections, search, statusFilter, gradeFilter, strandFilter, specializationFilter, academicYears, gradeLevels, strands, specializations])

  const pagedSections = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredSections.slice(start, start + pageSize)
  }, [filteredSections, page])

  const totalPages = Math.max(1, Math.ceil(filteredSections.length / pageSize))
  const selectedGrade = gradeLevels.find((grade) => String(grade.id) === String(form.grade_level))
  const activeYearCount = academicYears.filter((year) => year.is_active).length
  const selectableGradeLevels = gradeLevels.filter((grade) =>
    grade.is_active !== false || (form.id && String(grade.id) === String(form.grade_level)),
  )
  const selectableStrands = strands.filter((strand) =>
    strand.is_active || (form.id && String(strand.id) === String(form.strand)),
  )
  const selectableSpecializations = specializations.filter((specialization) =>
    (specialization.is_active && String(specialization.strand) === String(form.strand)) ||
    (form.id && String(specialization.id) === String(form.specialization)),
  )
  const requiresSpecialization = selectableStrands.find((strand) => String(strand.id) === String(form.strand))?.code === 'TVL'

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        grade_level: form.grade_level,
        name: form.name,
        capacity: Number(form.capacity || 0),
        description: form.description,
        adviser: form.adviser || null,
        strand: form.strand || null,
        specialization: form.specialization || null,
      }
      if (form.id) {
        await updateSection(form.id, payload)
      } else {
        await createSection(payload)
      }
      const refreshed = await getSections({ status: 'all' })
      setSections(normalizeListResponse(refreshed).items)
      resetForm()
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function editSection(section) {
    if (section.specialization && !specializations.some((item) => String(item.id) === String(section.specialization))) {
      setSpecializations((current) => [
        ...current,
        { id: section.specialization, strand: section.strand, name: section.specialization_name || 'Historical specialization', is_active: false },
      ])
    }
    setForm({
      id: section.id,
      grade_level: section.grade_level || '',
      strand: section.strand || '',
      specialization: section.specialization || '',
      name: section.name || '',
      capacity: section.capacity ?? 40,
      description: section.description || '',
      adviser: section.adviser || '',
      adviser_name: section.adviser_name || '',
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function toggleStatus(section) {
    setError('')
    try {
      await updateSection(section.id, { is_active: !section.is_active })
      const refreshed = await getSections({ status: 'all' })
      setSections(normalizeListResponse(refreshed).items)
      if (String(form.id) === String(section.id)) resetForm()
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack sections-page">
      <PageHeader eyebrow="Sections" title="Manage sections" description="Organize sections by grade level, adviser, and capacity. The active academic year is assigned automatically." />

      {['SUPER_ADMIN', 'SCHOOL_ADMIN'].includes(user?.role || user?.role_name || user?.profile?.role_name) ? (
        <ExcelImportPanel
          title="Section configuration"
          templateUrl="/sections/import/template/"
          previewUrl="/sections/import/preview/"
          confirmUrl="/sections/import/confirm/"
          filename="edu-assist-section-import-template.xlsx"
          instructions="Imports create new sections only. Adviser assignments are handled separately through the teacher-assignment import and existing adviser rules."
          onCompleted={async () => {
            const refreshed = await getSections({ status: 'all' })
            setSections(normalizeListResponse(refreshed).items)
          }}
        />
      ) : null}

      {error ? <ErrorBanner message={error} /> : null}
      {!form.id && activeYearCount !== 1 ? (
        <div className="status-banner status-banner--warning">
          {activeYearCount === 0
            ? 'No active academic year is configured. '
            : 'More than one active academic year is configured. '}
          <Link to="/academic-years">Ask an administrator to configure Academic Year Management.</Link>
        </div>
      ) : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Sections</p>
          <p className="stat-value">{sections.length}</p>
        </article>
      </div>

      <details className="academic-editor-panel" open={Boolean(form.id)}>
        <summary className="academic-editor-summary">
          <span>
            <span className="eyebrow">Section details</span>
            <strong>{form.id ? 'Edit section' : 'Add new section'}</strong>
          </span>
          <span className="academic-editor-prompt">{form.id ? 'Close form' : 'Open form'}</span>
        </summary>

        <form className="form-grid" onSubmit={handleSave}>
          <label>
            <span>Grade level</span>
            <select value={form.grade_level} onChange={(event) => {
              const grade = gradeLevels.find((item) => String(item.id) === event.target.value)
              setForm((current) => ({
                ...current,
                grade_level: event.target.value,
                strand: grade?.school_level === 'Senior High School' ? current.strand : '',
                specialization: grade?.school_level === 'Senior High School' ? current.specialization : '',
              }))
            }} required>
              <option value="">Select grade level</option>
              {selectableGradeLevels.map((grade) => (
                <option key={grade.id} value={grade.id}>{grade.name}{grade.is_active === false ? ' (Archived)' : ''}</option>
              ))}
            </select>
          </label>
          {selectedGrade?.school_level === 'Senior High School' ? (
            <>
              <label>
                <span>Section strand (optional)</span>
                <select value={form.strand} onChange={(event) => setForm({ ...form, strand: event.target.value, specialization: '' })}>
                  <option value="">Shared section - no single strand</option>
                  {selectableStrands.map((strand) => (
                    <option key={strand.id} value={strand.id}>{strand.name}{strand.is_active === false ? ' (Archived)' : ''}</option>
                  ))}
                </select>
                <small className="small-muted">Leave blank when students from multiple strands share this section.</small>
              </label>
              <label>
                <span>Specialization{requiresSpecialization ? ' *' : ''}</span>
                <select value={form.specialization} onChange={(event) => setForm({ ...form, specialization: event.target.value })} disabled={!form.strand} required={requiresSpecialization}>
                  <option value="">{form.strand ? 'Select specialization' : 'Not applicable to a shared section'}</option>
                  {selectableSpecializations.map((specialization) => (
                    <option key={specialization.id} value={specialization.id}>{specialization.name}{specialization.is_active === false ? ' (Archived)' : ''}</option>
                  ))}
                </select>
              </label>
            </>
          ) : null}
          <label>
            <span>Section name</span>
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            <span>Capacity guideline</span>
            <input type="number" min="1" value={form.capacity} onChange={(event) => setForm({ ...form, capacity: Number(event.target.value) })} required />
            <small className="small-muted">This is a planning guideline, not an enrollment limit. Enrollment may continue above it according to school policy.</small>
          </label>
          <label>
            <span>Adviser</span>
            <AdviserSelect value={form.adviser || ''} initialLabel={form.adviser_name || ''} onChange={(id) => setForm({ ...form, adviser: id })} />
          </label>
          <label>
            <span>Description</span>
            <input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving || (!form.id && activeYearCount !== 1)}>{saving ? 'Saving...' : form.id ? 'Update section' : 'Create section'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={resetForm}>Cancel</button> : null}
          </div>
        </form>
      </details>

      <div className="panel-card record-panel academic-record-list">
        <div className="section-header">
          <div>
            <p className="eyebrow">Section records</p>
            <h2>Section list</h2>
          </div>
          <div className="search-input-group academic-filters section-filters">
            <input aria-label="Search sections" placeholder="Search sections" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select aria-label="Filter by grade level" value={gradeFilter} onChange={(event) => { setGradeFilter(event.target.value); setPage(1) }}>
              <option value="">All grade levels</option>
              {gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}
            </select>
            <select aria-label="Filter by strand" value={strandFilter} onChange={(event) => { setStrandFilter(event.target.value); setSpecializationFilter(''); setPage(1) }}>
              <option value="">All strands</option>
              {strands.filter((strand) => strand.is_active).map((strand) => <option key={strand.id} value={strand.id}>{strand.name}</option>)}
            </select>
            <select aria-label="Filter by specialization" value={specializationFilter} onChange={(event) => { setSpecializationFilter(event.target.value); setPage(1) }}>
              <option value="">All specializations</option>
              {specializations.filter((specialization) => specialization.is_active && (!strandFilter || String(specialization.strand) === strandFilter)).map((specialization) => <option key={specialization.id} value={specialization.id}>{specialization.name}</option>)}
            </select>
            <select aria-label="Filter by status" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
              <option value="all">All statuses</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </div>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}

        {!loading && filteredSections.length === 0 ? (
          <EmptyState title="No sections found" message="Add a section or adjust your filters." />
        ) : null}

        {!loading && filteredSections.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{filteredSections.length} section{filteredSections.length === 1 ? '' : 's'} found</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Section</th>
                    <th scope="col">Academic year</th>
                    <th scope="col">Grade level</th>
                    <th scope="col">Strand</th>
                    <th scope="col">Specialization</th>
                    <th scope="col">Enrollment / capacity guideline</th>
                    <th scope="col">Adviser</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedSections.map((section) => (
                    <tr key={section.id}>
                      <td>{section.name || '—'}</td>
                      <td>{getNameById(academicYears, section.academic_year)}</td>
                      <td>{getNameById(gradeLevels, section.grade_level)}</td>
                      <td>{section.strand ? getNameById(strands, section.strand) : gradeLevels.find((grade) => String(grade.id) === String(section.grade_level))?.school_level === 'Senior High School' ? 'Shared section' : 'Not applicable'}</td>
                      <td>{section.specialization ? getNameById(specializations, section.specialization) : 'Not applicable'}</td>
                      <td>Enrolled: {section.student_count ?? 0} / {section.capacity ?? '—'} (Guideline)</td>
                      <td>{section.adviser_name || section.adviser || '—'}</td>
                      <td><span className={section.is_active ? 'status-pill status-pill--success' : 'status-pill status-pill--neutral'}>{section.is_active ? 'Active' : 'Archived'}</span></td>
                      <td>
                        <div className="section-actions" style={{ justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <button type="button" className="action-button action-button--secondary" onClick={() => editSection(section)}>Edit</button>
                          <button type="button" className="action-button action-button--outline" onClick={() => toggleStatus(section)}>{section.is_active ? 'Archive' : 'Restore'}</button>
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

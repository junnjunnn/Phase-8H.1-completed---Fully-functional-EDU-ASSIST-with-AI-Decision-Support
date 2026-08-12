import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { createSection, getAcademicYears, getGradeLevels, getSections, updateSection } from '../../services/academicsService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function getNameById(items, id) {
  const match = items.find((item) => String(item.id) === String(id))
  return match?.name || match?.code || '—'
}

export function SectionsPage() {
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '', is_active: true })
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')
      try {
        const [yearsData, gradeData, sectionsData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
        ])
        if (!active) return
        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
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
      const matchesSearch = !term || section.name.toLowerCase().includes(term) || getNameById(academicYears, section.academic_year).toLowerCase().includes(term) || getNameById(gradeLevels, section.grade_level).toLowerCase().includes(term) || (section.adviser || '').toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(section.is_active) === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [sections, search, statusFilter, academicYears, gradeLevels])

  const pagedSections = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredSections.slice(start, start + pageSize)
  }, [filteredSections, page])

  const totalPages = Math.max(1, Math.ceil(filteredSections.length / pageSize))

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...form,
        capacity: Number(form.capacity || 0),
        adviser: form.adviser || null,
      }
      if (form.id) {
        await updateSection(form.id, payload)
      } else {
        await createSection(payload)
      }
      const refreshed = await getSections()
      setSections(normalizeListResponse(refreshed).items)
      setForm({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '', is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function editSection(section) {
    setForm({
      id: section.id,
      academic_year: section.academic_year || '',
      grade_level: section.grade_level || '',
      name: section.name || '',
      capacity: section.capacity ?? 40,
      description: section.description || '',
      adviser: section.adviser || '',
      adviser_name: section.adviser_name || '',
      is_active: section.is_active !== false,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function toggleStatus(section) {
    setError('')
    try {
      await updateSection(section.id, { is_active: !section.is_active })
      const refreshed = await getSections()
      setSections(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack sections-page">
      <PageHeader eyebrow="Sections" title="Manage sections" description="Organize sections with associated year, grade level, adviser, and capacity." />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Sections</p>
          <p className="stat-value">{sections.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Section details</p>
            <h2>{form.id ? 'Edit section' : 'Add new section'}</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleSave}>
          <label>
            <span>Academic year</span>
            <select value={form.academic_year} onChange={(event) => setForm({ ...form, academic_year: event.target.value })} required>
              <option value="">Select year</option>
              {academicYears.map((year) => (
                <option key={year.id} value={year.id}>{year.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={form.grade_level} onChange={(event) => setForm({ ...form, grade_level: event.target.value })} required>
              <option value="">Select grade level</option>
              {gradeLevels.map((grade) => (
                <option key={grade.id} value={grade.id}>{grade.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Section name</span>
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            <span>Capacity</span>
            <input type="number" min="1" value={form.capacity} onChange={(event) => setForm({ ...form, capacity: Number(event.target.value) })} required />
          </label>
          <label>
            <span>Adviser</span>
            <AdviserSelect value={form.adviser || ''} initialLabel={form.adviser_name || ''} onChange={(id) => setForm({ ...form, adviser: id })} />
          </label>
          <label>
            <span>Description</span>
            <input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : form.id ? 'Update section' : 'Create section'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={() => setForm({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', adviser_name: '', is_active: true })}>Cancel</button> : null}
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Section records</p>
            <h2>Section list</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search sections" placeholder="Search sections" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
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
                    <th scope="col">Capacity</th>
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
                      <td>{section.capacity ?? '—'}</td>
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

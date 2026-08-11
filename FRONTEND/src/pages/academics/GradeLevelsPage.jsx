import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { createGradeLevel, getGradeLevels, updateGradeLevel } from '../../services/academicsService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function GradeLevelsPage() {
  const [gradeLevels, setGradeLevels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  useEffect(() => {
    let active = true

    async function loadGradeLevels() {
      setLoading(true)
      setError('')
      try {
        const data = await getGradeLevels()
        if (!active) return
        setGradeLevels(normalizeListResponse(data).items)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadGradeLevels()
    return () => { active = false }
  }, [])

  const filteredGradeLevels = useMemo(() => {
    const term = search.trim().toLowerCase()
    return gradeLevels.filter((grade) => {
      const matchesSearch = !term || grade.name.toLowerCase().includes(term) || grade.code.toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(grade.is_active) === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [gradeLevels, search, statusFilter])

  const pagedGradeLevels = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredGradeLevels.slice(start, start + pageSize)
  }, [filteredGradeLevels, page])

  const totalPages = Math.max(1, Math.ceil(filteredGradeLevels.length / pageSize))

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (form.id) {
        await updateGradeLevel(form.id, form)
      } else {
        await createGradeLevel(form)
      }
      const refreshed = await getGradeLevels()
      setGradeLevels(normalizeListResponse(refreshed).items)
      setForm({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function editGrade(grade) {
    setForm({
      id: grade.id,
      name: grade.name || '',
      code: grade.code || '',
      school_level: grade.school_level || 'Elementary',
      order: grade.order || 1,
      is_active: grade.is_active !== false,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function toggleStatus(grade) {
    setError('')
    try {
      await updateGradeLevel(grade.id, { is_active: !grade.is_active })
      const refreshed = await getGradeLevels()
      setGradeLevels(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack grade-levels-page">
      <PageHeader eyebrow="Grade Levels" title="Manage grade levels" description="Define grade level records for your academic structure." />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Grade levels</p>
          <p className="stat-value">{gradeLevels.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Grade level details</p>
            <h2>{form.id ? 'Edit grade level' : 'Add new grade level'}</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleSave}>
          <label>
            <span>Name</span>
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            <span>Code</span>
            <input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} required />
          </label>
          <label>
            <span>School level</span>
            <select value={form.school_level} onChange={(event) => setForm({ ...form, school_level: event.target.value })}>
              <option value="Elementary">Elementary</option>
              <option value="Junior High School">Junior High School</option>
              <option value="Senior High School">Senior High School</option>
            </select>
          </label>
          <label>
            <span>Order</span>
            <input type="number" min="1" value={form.order} onChange={(event) => setForm({ ...form, order: Number(event.target.value) })} required />
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : form.id ? 'Update grade level' : 'Create grade level'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={() => setForm({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })}>Cancel</button> : null}
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Grade level records</p>
            <h2>Grade level list</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search grade levels" placeholder="Search grade levels" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
              <option value="all">All statuses</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </div>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}

        {!loading && filteredGradeLevels.length === 0 ? (
          <EmptyState title="No grade levels found" message="Add a grade level or adjust your filters." />
        ) : null}

        {!loading && filteredGradeLevels.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{filteredGradeLevels.length} grade level{filteredGradeLevels.length === 1 ? '' : 's'} found</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Code</th>
                    <th scope="col">School level</th>
                    <th scope="col">Order</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedGradeLevels.map((grade) => (
                    <tr key={grade.id}>
                      <td>{grade.name || '—'}</td>
                      <td>{grade.code || '—'}</td>
                      <td>{grade.school_level || '—'}</td>
                      <td>{grade.order ?? '—'}</td>
                      <td><span className={grade.is_active ? 'status-pill status-pill--success' : 'status-pill status-pill--neutral'}>{grade.is_active ? 'Active' : 'Archived'}</span></td>
                      <td>
                        <div className="section-actions" style={{ justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <button type="button" className="action-button action-button--secondary" onClick={() => editGrade(grade)}>Edit</button>
                          <button type="button" className="action-button action-button--outline" onClick={() => toggleStatus(grade)}>{grade.is_active ? 'Archive' : 'Restore'}</button>
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

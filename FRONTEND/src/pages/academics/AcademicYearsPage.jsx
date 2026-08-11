import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { createAcademicYear, getAcademicYears, updateAcademicYear } from '../../services/academicsService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function AcademicYearsPage() {
  const [academicYears, setAcademicYears] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', name: '', start_date: '', end_date: '', is_active: true })
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  useEffect(() => {
    let active = true
    async function loadYears() {
      setLoading(true)
      setError('')
      try {
        const data = await getAcademicYears()
        if (!active) return
        setAcademicYears(normalizeListResponse(data).items)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }
    loadYears()
    return () => { active = false }
  }, [])

  const filteredYears = useMemo(() => {
    const term = search.trim().toLowerCase()
    return academicYears.filter((year) => {
      const matchesSearch = !term || (year.name || '').toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(year.is_active) === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [academicYears, search, statusFilter])

  const pagedYears = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredYears.slice(start, start + pageSize)
  }, [filteredYears, page])

  const totalPages = Math.max(1, Math.ceil(filteredYears.length / pageSize))

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (form.id) {
        await updateAcademicYear(form.id, form)
      } else {
        await createAcademicYear(form)
      }
      const refreshed = await getAcademicYears()
      setAcademicYears(normalizeListResponse(refreshed).items)
      setForm({ id: '', name: '', start_date: '', end_date: '', is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function toggleStatus(year) {
    try {
      await updateAcademicYear(year.id, { is_active: !year.is_active })
      const refreshed = await getAcademicYears()
      setAcademicYears(normalizeListResponse(refreshed).items)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  function editYear(year) {
    setForm({ id: year.id, name: year.name || '', start_date: year.start_date || '', end_date: year.end_date || '', is_active: year.is_active !== false })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="page-stack academic-years-page">
      <PageHeader eyebrow="Academic Years" title="Manage academic years" description="Create and maintain school years, including active and archived terms." />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Academic years</p>
          <p className="stat-value">{academicYears.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic year details</p>
            <h2>{form.id ? 'Update academic year' : 'Add new academic year'}</h2>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSave}>
          <label>
            <span>Name</span>
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            <span>Start date</span>
            <input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} required />
          </label>
          <label>
            <span>End date</span>
            <input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} required />
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : form.id ? 'Update academic year' : 'Create academic year'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={() => setForm({ id: '', name: '', start_date: '', end_date: '', is_active: true })}>Cancel</button> : null}
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic year list</p>
            <h2>Academic year records</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search academic years" placeholder="Search academic years" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
              <option value="all">All statuses</option>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </div>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}

        {!loading && filteredYears.length === 0 ? (
          <EmptyState title="No academic years found" message="Try a different search term or add a new academic year." />
        ) : null}

        {!loading && filteredYears.length > 0 ? (
          <>
            <div className="record-table-header">
              <p>{filteredYears.length} academic year{filteredYears.length === 1 ? '' : 's'} found</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Start date</th>
                    <th scope="col">End date</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedYears.map((year) => (
                    <tr key={year.id}>
                      <td>{year.name || '—'}</td>
                      <td>{year.start_date || '—'}</td>
                      <td>{year.end_date || '—'}</td>
                      <td><span className={year.is_active ? 'status-pill status-pill--success' : 'status-pill status-pill--neutral'}>{year.is_active ? 'Active' : 'Archived'}</span></td>
                      <td>
                        <div className="section-actions" style={{ justifyContent: 'flex-end', gap: '0.5rem' }}>
                          <button type="button" className="action-button action-button--secondary" onClick={() => editYear(year)}>Edit</button>
                          <button type="button" className="action-button action-button--outline" onClick={() => toggleStatus(year)}>{year.is_active ? 'Archive' : 'Restore'}</button>
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

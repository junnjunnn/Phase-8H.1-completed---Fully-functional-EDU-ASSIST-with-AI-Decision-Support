import { useEffect, useMemo, useState } from 'react'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { createSubject, getGradeLevels, getStrands, getSubjects, updateSubject } from '../../services/academicsService'
import { notifySubjectsUpdated } from '../../services/referenceService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function getNameById(items, id) {
  const match = items.find((item) => String(item.id) === String(id))
  return match?.name || match?.code || '—'
}

export function SubjectsPage() {
  const [gradeLevels, setGradeLevels] = useState([])
  const [strands, setStrands] = useState([])
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })
  const [saving, setSaving] = useState(false)

  const pageSize = 8

  useEffect(() => {
    let active = true

    async function loadReferences() {
      setLoading(true)
      setError('')
      try {
        const [gradeData, strandData, subjectData] = await Promise.all([
          getGradeLevels(),
          getStrands(),
          getSubjects(),
        ])
        if (!active) return
        setGradeLevels(normalizeListResponse(gradeData).items)
        setStrands(normalizeListResponse(strandData).items)
        setSubjects(normalizeListResponse(subjectData).items)
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

  const filteredSubjects = useMemo(() => {
    const term = search.trim().toLowerCase()
    return subjects.filter((subject) => {
      const matchesSearch = !term || subject.name.toLowerCase().includes(term) || subject.code.toLowerCase().includes(term) || subject.category.toLowerCase().includes(term) || getNameById(gradeLevels, subject.grade_level).toLowerCase().includes(term) || getNameById(strands, subject.strand).toLowerCase().includes(term)
      const matchesStatus = statusFilter === 'all' || String(subject.is_active) === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [subjects, search, statusFilter, gradeLevels, strands])

  const pagedSubjects = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredSubjects.slice(start, start + pageSize)
  }, [filteredSubjects, page])

  const totalPages = Math.max(1, Math.ceil(filteredSubjects.length / pageSize))

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...form,
        grade_level: form.grade_level || null,
        strand: form.strand || null,
      }
      if (form.id) {
        await updateSubject(form.id, payload)
      } else {
        await createSubject(payload)
      }
      const refreshed = await getSubjects()
      setSubjects(normalizeListResponse(refreshed).items)
      notifySubjectsUpdated()
      setForm({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function editSubject(subject) {
    setForm({
      id: subject.id,
      code: subject.code || '',
      name: subject.name || '',
      category: subject.category || 'Learning Area',
      grade_level: subject.grade_level || '',
      strand: subject.strand || '',
      is_active: subject.is_active !== false,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function toggleStatus(subject) {
    setError('')
    try {
      await updateSubject(subject.id, { is_active: !subject.is_active })
      const refreshed = await getSubjects()
      setSubjects(normalizeListResponse(refreshed).items)
      notifySubjectsUpdated()
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack subjects-page">
      <PageHeader eyebrow="Subjects" title="Manage subjects" description="Create and maintain subject records with grade level and strand assignments." />

      {error ? <ErrorBanner message={error} /> : null}

      <div className="record-summary-grid">
        <article className="detail-card stat-card-accent">
          <p className="stat-label">Subjects</p>
          <p className="stat-value">{subjects.length}</p>
        </article>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Subject details</p>
            <h2>{form.id ? 'Edit subject' : 'Add new subject'}</h2>
          </div>
        </div>

        <form className="form-grid" onSubmit={handleSave}>
          <label>
            <span>Subject code</span>
            <input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} required />
          </label>
          <label>
            <span>Subject name</span>
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
          </label>
          <label>
            <span>Category</span>
            <select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
              <option value="Learning Area">Learning Area</option>
              <option value="Core Subject">Core Subject</option>
            </select>
          </label>
          <label>
            <span>Grade level</span>
            <select value={form.grade_level} onChange={(event) => setForm({ ...form, grade_level: event.target.value })}>
              <option value="">Select grade level</option>
              {gradeLevels.map((grade) => (
                <option key={grade.id} value={grade.id}>{grade.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Strand</span>
            <select value={form.strand} onChange={(event) => setForm({ ...form, strand: event.target.value })}>
              <option value="">Select strand</option>
              {strands.map((strand) => (
                <option key={strand.id} value={strand.id}>{strand.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Status</span>
            <select value={form.is_active ? 'true' : 'false'} onChange={(event) => setForm({ ...form, is_active: event.target.value === 'true' })}>
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
          </label>
          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button action-button--primary" disabled={saving}>{saving ? 'Saving...' : form.id ? 'Update subject' : 'Create subject'}</button>
            {form.id ? <button type="button" className="action-button action-button--secondary" onClick={() => setForm({ id: '', code: '', name: '', category: 'Learning Area', grade_level: '', strand: '', is_active: true })}>Cancel</button> : null}
          </div>
        </form>
      </div>

      <div className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Subject records</p>
            <h2>Subject list</h2>
          </div>
          <div className="search-input-group">
            <input aria-label="Search subjects" placeholder="Search subjects" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} />
            <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}>
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
            <div className="record-table-header">
              <p>{filteredSubjects.length} subject{filteredSubjects.length === 1 ? '' : 's'} found</p>
            </div>
            <div className="table-card">
              <table className="records-table">
                <thead>
                  <tr>
                    <th scope="col">Code</th>
                    <th scope="col">Name</th>
                    <th scope="col">Category</th>
                    <th scope="col">Grade level</th>
                    <th scope="col">Strand</th>
                    <th scope="col">Status</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pagedSubjects.map((subject) => (
                    <tr key={subject.id}>
                      <td>{subject.code || '—'}</td>
                      <td>{subject.name || '—'}</td>
                      <td>{subject.category || '—'}</td>
                      <td>{getNameById(gradeLevels, subject.grade_level)}</td>
                      <td>{getNameById(strands, subject.strand)}</td>
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

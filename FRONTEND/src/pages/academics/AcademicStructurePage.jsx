import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import {
  createAcademicYear,
  createGradeLevel,
  createSection,
  getAcademicYears,
  getGradeLevels,
  getSections,
  updateAcademicYear,
  updateGradeLevel,
  updateSection,
} from '../../services/academicsService'
import { getUsers as getUserProfiles } from '../../services/userService'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

export function AcademicStructurePage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'SCHOOL_ADMIN'
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [yearForm, setYearForm] = useState({ id: '', name: '', start_date: '', end_date: '', is_active: false })
  const [gradeForm, setGradeForm] = useState({ id: '', name: '', code: '', school_level: 'Elementary', order: 1, is_active: true })
  const [sectionForm, setSectionForm] = useState({ id: '', academic_year: '', grade_level: '', name: '', capacity: 40, description: '', adviser: '', is_active: true })
  const [saving, setSaving] = useState(false)

  const filteredSections = useMemo(() => {
    return sections.filter((section) => section.is_active !== false)
  }, [sections])

  useEffect(() => {
    async function loadReferenceData() {
      setLoading(true)
      setError('')
      try {
        const [yearsData, gradeData, sectionData, teacherData] = await Promise.all([
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getUserProfiles(),
        ])
        setAcademicYears(normalizeListResponse(yearsData).items)
        setGradeLevels(normalizeListResponse(gradeData).items)
        setSections(normalizeListResponse(sectionData).items)
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
          </div>
        </form>

        {loading ? <div className="table-skeleton-grid"><div className="table-skeleton-card" /></div> : null}
        {!loading && academicYears.length === 0 ? <EmptyState title="No academic years" message="No academic years have been configured yet." /> : null}
        {!loading && academicYears.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">School year</th>
                  <th scope="col">Status</th>
                  <th scope="col">Start</th>
                  <th scope="col">End</th>
                </tr>
              </thead>
              <tbody>
                {academicYears.map((year) => (
                  <tr key={year.id}>
                    <td>{year.name}</td>
                    <td>{year.is_active ? 'Active' : 'Archived'}</td>
                    <td>{year.start_date}</td>
                    <td>{year.end_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
          </div>
        </form>

        {!loading && gradeLevels.length === 0 ? <EmptyState title="No grade levels" message="No grade levels have been configured yet." /> : null}
        {!loading && gradeLevels.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Code</th>
                  <th scope="col">School level</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {gradeLevels.map((grade) => (
                  <tr key={grade.id}>
                    <td>{grade.name}</td>
                    <td>{grade.code}</td>
                    <td>{grade.school_level}</td>
                    <td>{grade.is_active ? 'Active' : 'Inactive'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
          </div>
        </form>

        {!loading && filteredSections.length === 0 ? <EmptyState title="No sections" message="No sections have been configured yet." /> : null}
        {!loading && filteredSections.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th scope="col">Section</th>
                  <th scope="col">Year</th>
                  <th scope="col">Grade</th>
                  <th scope="col">Capacity</th>
                  <th scope="col">Adviser</th>
                </tr>
              </thead>
              <tbody>
                {filteredSections.map((section) => (
                  <tr key={section.id}>
                    <td>{section.name}</td>
                    <td>{section.academic_year_name || section.academic_year_name || section.academic_year || '—'}</td>
                    <td>{section.grade_level_name || section.grade_level_name || section.grade_level || '—'}</td>
                    <td>{section.capacity || 0}</td>
                    <td>{section.adviser_name || section.adviser || 'Unassigned'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </div>
  )
}

import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { exportReport, getReportCenter } from '../../services/reportService'

const categories = [
  { key: 'student', label: 'Student Reports', description: 'Master list, profiles, and enrollment visibility.' },
  { key: 'academic', label: 'Academic Reports', description: 'Performance summaries, pass/fail rates, and grade trends.' },
  { key: 'attendance', label: 'Attendance Reports', description: 'Attendance percentages, present/absent counts, and ranking.' },
  { key: 'behavior', label: 'Behavior Reports', description: 'Behavior averages, classifications, and intervention needs.' },
  { key: 'ai', label: 'AI Reports', description: 'Risk summaries, distributions, and prediction history.' },
  { key: 'intervention', label: 'Intervention Reports', description: 'Intervention progress and outcomes.' },
]

function getRoleLabel(role) {
  if (!role) return 'User'
  return String(role).replace('_', ' ')
}

function ChartCard({ title, data = [], color = '#113f8a' }) {
  const maxValue = Math.max(...data.map((item) => Number(item.value || 0)), 1)

  return (
    <article className="panel-card">
      <h3>{title}</h3>
      <div className="chart-card" aria-label={`${title} chart`}>
        {data.length === 0 ? (
          <p>No data available</p>
        ) : (
          data.map((entry) => (
            <div key={entry.label} className="chart-row">
              <div className="chart-row-labels">
                <span>{entry.label}</span>
                <strong>{entry.value}</strong>
              </div>
              <div className="chart-bar-track" aria-hidden="true">
                <div
                  className="chart-bar-fill"
                  style={{ width: `${(Number(entry.value || 0) / maxValue) * 100}%`, background: color }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </article>
  )
}

export function ReportsPage() {
  const { user } = useAuth()
  const location = useLocation()
  const [reportData, setReportData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeCategory, setActiveCategory] = useState('student')
  const [filters, setFilters] = useState({
    academic_year: '',
    grade_level: '',
    section: '',
    teacher: '',
    risk_level: '',
    status: '',
    search: '',
  })

  const visibleCategories = useMemo(() => {
    const role = user?.role_name || user?.role || user?.profile?.role_name || 'NONE'
    if (role === 'TEACHER') {
      return categories.filter((category) => category.key !== 'ai')
    }
    return categories
  }, [user])

  // Only update active category when it actually differs to avoid synchronous setState loops
  const _lastCategoryRef = useRef(null)
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const category = params.get('category')
    if (category && categories.some((item) => item.key === category)) {
      if (_lastCategoryRef.current !== category) {
        setActiveCategory(category)
        _lastCategoryRef.current = category
      }
    }
  }, [location.search])

  useEffect(() => {
    let active = true

    async function loadReportCenter() {
      setLoading(true)
      setError('')
      try {
        const data = await getReportCenter(filters)
        if (active) {
          setReportData(data)
        }
      } catch (err) {
        if (active) {
          setError(getApiErrorMessage(err))
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadReportCenter()
    return () => {
      active = false
    }
  }, [filters])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFilters((current) => ({ ...current, [name]: value }))
  }

  const handleExport = async (format) => {
    try {
      const result = await exportReport({ ...filters, format })
      const payload = result?.data || result || {}
      const responseFormat = String(result?.format || format || 'csv').toLowerCase()
      const fileName = result?.download_file || `report-export-${responseFormat || 'data'}-${new Date().toISOString().slice(0, 10)}.${responseFormat === 'pdf' ? 'pdf' : responseFormat === 'xlsx' ? 'xlsx' : 'csv'}`

      if (responseFormat === 'pdf') {
        window.alert(result.message || 'Use print preview to save as PDF.')
        window.print()
        return
      }

      const downloadData = payload?.data || payload
      const exportContent = responseFormat === 'csv'
        ? Object.entries(downloadData || {}).map(([key, value]) => `${key},${String(value ?? '')}`).join('\n')
        : JSON.stringify(downloadData, null, 2)

      const contentType = responseFormat === 'csv'
        ? 'text/csv;charset=utf-8'
        : responseFormat === 'xlsx'
          ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8'
          : 'application/json;charset=utf-8'

      const blob = new Blob([exportContent], { type: contentType })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      window.alert(result.message || `Report exported as ${fileName}`)
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  const studentReports = reportData?.student_reports || {}
  const academicReports = reportData?.academic_reports || {}
  const attendanceReports = reportData?.attendance_reports || {}
  const behaviorReports = reportData?.behavior_reports || {}
  const aiReports = reportData?.ai_reports || {}
  const interventionReports = reportData?.intervention_reports || {}

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Reports Center"
        title="Reports, analytics and exports"
        description="Use existing school data to review student outcomes, attendance, interventions, and AI risk trends."
        actions={[
          <button key="csv" type="button" className="btn btn-secondary" onClick={() => handleExport('csv')}>
            Export CSV
          </button>,
          <button key="print" type="button" className="btn btn-outline" onClick={() => window.print()}>
            Print
          </button>,
        ]}
      />

      <div className="panel-card">
        <p className="eyebrow">Role view</p>
        <p>
          {getRoleLabel(user?.role_name || user?.role || user?.profile?.role_name)} · {visibleCategories.length}{' '}
          report categories available
        </p>
      </div>

      <section className="panel-card" aria-label="Report filters">
        <div className="form-grid">
          <label>
            Search
            <input name="search" value={filters.search} onChange={handleChange} placeholder="Search student" />
          </label>
          <label>
            Academic Year
            <input name="academic_year" value={filters.academic_year} onChange={handleChange} placeholder="2024-2025" />
          </label>
          <label>
            Grade Level
            <input name="grade_level" value={filters.grade_level} onChange={handleChange} placeholder="Grade 10" />
          </label>
          <label>
            Section
            <input name="section" value={filters.section} onChange={handleChange} placeholder="Section A" />
          </label>
          <label>
            Teacher
            <input name="teacher" value={filters.teacher} onChange={handleChange} placeholder="Teacher ID" />
          </label>
          <label>
            Risk Level
            <select name="risk_level" value={filters.risk_level} onChange={handleChange}>
              <option value="">All</option>
              <option value="Low">Low</option>
              <option value="Moderate">Moderate</option>
              <option value="High">High</option>
            </select>
          </label>
          <label>
            Status
            <select name="status" value={filters.status} onChange={handleChange}>
              <option value="">All</option>
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>
          <label>
            Date From
            <input type="date" name="date_from" value={filters.date_from || ''} onChange={handleChange} />
          </label>
          <label>
            Date To
            <input type="date" name="date_to" value={filters.date_to || ''} onChange={handleChange} />
          </label>
        </div>
      </section>

      <section className="panel-card" aria-label="Report categories">
        <div className="chip-list">
          {visibleCategories.map((category) => (
            <button
              key={category.key}
              type="button"
              className={`chip ${activeCategory === category.key ? 'chip--active' : ''}`}
              onClick={() => setActiveCategory(category.key)}
            >
              {category.label}
            </button>
          ))}
        </div>
        <p>{visibleCategories.find((category) => category.key === activeCategory)?.description}</p>
      </section>

      {error ? <ErrorBanner message={error} /> : null}

      {loading ? (
        <div className="table-skeleton-grid">
          <div className="table-skeleton-card" />
        </div>
      ) : null}

      {!loading && !reportData ? (
        <EmptyState title="No report data" message="No report data is available for the selected filters." />
      ) : null}

      {!loading && reportData ? (
        <div>
          <section className="dashboard-summary-grid" aria-label="Report summaries">
            <article className="dashboard-metric-card">
              <p className="stat-label">Students</p>
              <p className="stat-value">{studentReports.student_count ?? 0}</p>
            </article>
            <article className="dashboard-metric-card">
              <p className="stat-label">Enrollments</p>
              <p className="stat-value">{studentReports.enrollment_count ?? 0}</p>
            </article>
            <article className="dashboard-metric-card">
              <p className="stat-label">Attendance %</p>
              <p className="stat-value">{attendanceReports.summary?.attendance_percentage ?? 0}%</p>
            </article>
            <article className="dashboard-metric-card">
              <p className="stat-label">Behavior average</p>
              <p className="stat-value">{behaviorReports.summary?.behavior_average ?? 0}</p>
            </article>
            <article className="dashboard-metric-card">
              <p className="stat-label">Predictions</p>
              <p className="stat-value">{aiReports.summary?.prediction_count ?? 0}</p>
            </article>
            <article className="dashboard-metric-card">
              <p className="stat-label">Interventions</p>
              <p className="stat-value">{interventionReports.summary?.total ?? 0}</p>
            </article>
          </section>

          {activeCategory === 'student' ? (
            <section className="panel-card">
              <h2>Student Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Student count</td>
                      <td>{studentReports.student_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Enrollment count</td>
                      <td>{studentReports.enrollment_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Academic years</td>
                      <td>{studentReports.academic_year_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Grade levels</td>
                      <td>{studentReports.grade_level_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Sections</td>
                      <td>{studentReports.section_count ?? 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeCategory === 'academic' ? (
            <section className="panel-card">
              <h2>Academic Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Average grade</td>
                      <td>{academicReports.summary?.average_grade ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Highest grade</td>
                      <td>{academicReports.summary?.highest_grade ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Lowest grade</td>
                      <td>{academicReports.summary?.lowest_grade ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Passing rate</td>
                      <td>{academicReports.summary?.passing_rate ?? 0}%</td>
                    </tr>
                    <tr>
                      <td>Failing rate</td>
                      <td>{academicReports.summary?.failing_rate ?? 0}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeCategory === 'attendance' ? (
            <section className="panel-card">
              <h2>Attendance Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Attendance percentage</td>
                      <td>{attendanceReports.summary?.attendance_percentage ?? 0}%</td>
                    </tr>
                    <tr>
                      <td>Present count</td>
                      <td>{attendanceReports.summary?.present_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Absent count</td>
                      <td>{attendanceReports.summary?.absent_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Late count</td>
                      <td>{attendanceReports.summary?.late_count ?? 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeCategory === 'behavior' ? (
            <section className="panel-card">
              <h2>Behavior Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Behavior average</td>
                      <td>{behaviorReports.summary?.behavior_average ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Assessments</td>
                      <td>{behaviorReports.summary?.assessment_count ?? 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeCategory === 'ai' ? (
            <section className="panel-card">
              <h2>AI Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>High risk</td>
                      <td>{aiReports.summary?.high_risk_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Moderate risk</td>
                      <td>{aiReports.summary?.moderate_risk_count ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Low risk</td>
                      <td>{aiReports.summary?.low_risk_count ?? 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {activeCategory === 'intervention' ? (
            <section className="panel-card">
              <h2>Intervention Reports</h2>
              <div className="table-card">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Total</td>
                      <td>{interventionReports.summary?.total ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Completed</td>
                      <td>{interventionReports.summary?.completed ?? 0}</td>
                    </tr>
                    <tr>
                      <td>In progress</td>
                      <td>{interventionReports.summary?.in_progress ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Planned</td>
                      <td>{interventionReports.summary?.planned ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Cancelled</td>
                      <td>{interventionReports.summary?.cancelled ?? 0}</td>
                    </tr>
                    <tr>
                      <td>Overdue</td>
                      <td>{interventionReports.summary?.overdue ?? 0}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          <section className="panel-card">
            <h2>Analytics</h2>
            <div className="dashboard-summary-grid">
              <ChartCard
                title="Risk distribution"
                data={(aiReports.distribution || []).map((entry) => ({ label: entry.risk_level, value: entry.count }))}
                color="#113f8a"
              />
              <ChartCard
                title="Attendance ranking"
                data={(attendanceReports.ranking || []).slice(0, 5).map((entry) => ({
                  label: `${entry.enrollment__student__first_name || ''} ${entry.enrollment__student__last_name || ''}`.trim() || 'Student',
                  value: entry.present || 0,
                }))}
                color="#0f766e"
              />
              <ChartCard
                title="Intervention activity"
                data={(interventionReports.teacher_activity || []).map((entry) => ({
                  label: entry.assigned_personnel__username || 'Unassigned',
                  value: entry.count,
                }))}
                color="#b45309"
              />
            </div>
          </section>
        </div>
      ) : null}
    </div>
  )
}

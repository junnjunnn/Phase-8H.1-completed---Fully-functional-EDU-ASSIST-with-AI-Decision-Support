import './ReportPrintDocument.css'

const reportTitles = {
  student: 'Student Reports',
  academic: 'Academic Reports',
  attendance: 'Attendance Reports',
  behavior: 'Behavior Reports',
  ai: 'AI Reports',
  intervention: 'Intervention Reports',
}

const reportMetrics = {
  student: [['Student count', 'student_count'], ['Enrollment count', 'enrollment_count'], ['Academic years', 'academic_year_count'], ['Grade levels', 'grade_level_count'], ['Sections', 'section_count']],
  academic: [['Average grade', 'average_grade'], ['Highest grade', 'highest_grade'], ['Lowest grade', 'lowest_grade'], ['Passing rate', 'passing_rate'], ['Failing rate', 'failing_rate']],
  attendance: [['Attendance percentage', 'attendance_percentage'], ['Present count', 'present_count'], ['Absent count', 'absent_count'], ['Late count', 'late_count']],
  behavior: [['Behavior average', 'behavior_average'], ['Assessments', 'assessment_count']],
  ai: [['High risk', 'high_risk_count'], ['Moderate risk', 'moderate_risk_count'], ['Low risk', 'low_risk_count'], ['Predictions', 'prediction_count']],
  intervention: [['Total', 'total'], ['Completed', 'completed'], ['In progress', 'in_progress'], ['Planned', 'planned'], ['Cancelled', 'cancelled'], ['Overdue', 'overdue']],
}

const filterLabels = { academic_year: 'Academic Year', grade_level: 'Grade Level', section: 'Section', subject: 'Subject', teacher: 'Teacher', risk_level: 'Risk Level', status: 'Status', date_from: 'Date From', date_to: 'Date To', search: 'Search' }

function formatPrintDate(date = new Date()) {
  return new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric' }).format(date)
}

function formatPrintTime(date = new Date()) {
  return new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(date)
}

function getFilterEntries(filters = {}) {
  return Object.entries(filters).filter(([, value]) => value).map(([key, value]) => ({ label: filterLabels[key] || key, value }))
}

export function ReportPrintDocument({ reportData, reportCategory, filters }) {
  if (!reportData) return null

  const reportSections = {
    student: reportData.student_reports || {},
    academic: reportData.academic_reports?.summary || {},
    attendance: reportData.attendance_reports?.summary || {},
    behavior: reportData.behavior_reports?.summary || {},
    ai: reportData.ai_reports?.summary || {},
    intervention: reportData.intervention_reports?.summary || {},
  }
  const title = reportTitles[reportCategory] || 'Reports'
  const section = reportSections[reportCategory] || {}
  const metrics = reportMetrics[reportCategory] || []
  const rows = metrics.map(([label, key]) => [label, section[key] ?? 0])
  const hasRecords = {
    student: (section.student_count || 0) > 0 || (section.enrollment_count || 0) > 0,
    academic: (section.total_records || 0) > 0,
    attendance: Object.values(section).some((value) => Number(value) > 0),
    behavior: (section.assessment_count || 0) > 0,
    ai: (section.prediction_count || 0) > 0,
    intervention: (section.total || 0) > 0,
  }[reportCategory] || false
  const filtersApplied = getFilterEntries(filters)

  return (
    <article className="report-print-document">
      <header className="report-print-header">
        <p className="report-print-brand">EDU ASSIST</p>
        <p className="report-print-school">Amigo School of Calinan, Inc.</p>
        <h1 className="report-print-title">{title}</h1>
        <dl className="report-print-meta">
          <div><dt>Report Category</dt><dd>{title}</dd></div>
          <div><dt>Generated Date</dt><dd>{formatPrintDate()}</dd></div>
          <div><dt>Generated Time</dt><dd>{formatPrintTime()}</dd></div>
        </dl>
      </header>
      <section className="report-print-section">
        <h2>Filters</h2>
        {filtersApplied.length ? <dl className="report-print-filters">{filtersApplied.map(({ label, value }) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl> : <p>No filters applied.</p>}
      </section>
      <section className="report-print-section">
        <h2>Report Content</h2>
        {!hasRecords ? <p className="report-print-empty">No records found for the selected criteria.</p> : null}
        <table className="report-print-table">
          <thead><tr><th scope="col">Metric</th><th scope="col">Value</th></tr></thead>
          <tbody>{rows.map(([label, value]) => <tr key={label}><td>{label}</td><td>{value}{label.includes('rate') || label.includes('percentage') ? '%' : ''}</td></tr>)}</tbody>
        </table>
      </section>
      <footer className="report-print-footer">Prepared by: ______________________________</footer>
    </article>
  )
}
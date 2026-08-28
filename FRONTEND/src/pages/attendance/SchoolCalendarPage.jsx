import { useEffect, useMemo, useState } from 'react'
import { ChevronLeftIcon, ChevronRightIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../context/AuthContext'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { PageHeader } from '../../components/common/PageHeader'
import { getAcademicYears, getGradeLevels, getSections, getSubjects } from '../../services/academicsService'
import { getUsers } from '../../services/userService'
import { getApiErrorMessage } from '../../services/api'
import { checkSchoolCalendarConflicts, createSchoolCalendarDay, getSchoolCalendarDays, importPhilippineHolidays, updateSchoolCalendarDay, submitSchoolCalendarDayForApproval, approveSchoolCalendarDay, rejectSchoolCalendarDay, publishSchoolCalendarDay, cancelSchoolCalendarDay, getRecurringSchoolCalendarEvents, createRecurringSchoolCalendarEvent, deactivateRecurringSchoolCalendarEvent } from '../../services/attendanceService'

const DAY_TYPES = [
  { value: 'SCHOOL_DAY', label: 'School Day' },
  { value: 'WEEKEND', label: 'Weekend' },
  { value: 'HOLIDAY', label: 'Holiday' },
  { value: 'SUSPENSION', label: 'Suspension' },
  { value: 'SCHOOL_EVENT', label: 'School event' },
  { value: 'ACTIVITY', label: 'Activity' },
  { value: 'EXAMINATION', label: 'Examination' },
  { value: 'SPECIAL_NON_CLASS_DAY', label: 'Special Non-Class Day' },
  { value: 'ENROLLMENT', label: 'Enrollment' },
  { value: 'ACADEMIC_DEADLINE', label: 'Academic Deadline' },
]

const EVENT_TYPES = {
  ENROLLMENT: [
    ['ENROLLMENT_OPENS', 'Enrollment Opens'], ['ENROLLMENT_PERIOD', 'Enrollment Period'], ['ENROLLMENT_DEADLINE', 'Enrollment Deadline'],
    ['LATE_ENROLLMENT', 'Late Enrollment'], ['ADDING_DROPPING', 'Adding/Dropping Period'], ['SUBJECT_REGISTRATION', 'Subject Registration'],
    ['SCHOLARSHIP_APPLICATION', 'Scholarship Application'], ['CLEARANCE_PERIOD', 'Clearance Period'], ['STUDENT_ORIENTATION', 'Student Orientation'],
    ['OTHER_ENROLLMENT_ACTIVITY', 'Other Enrollment Activity'],
  ],
  ACADEMIC_DEADLINE: [
    ['GRADE_SUBMISSION', 'Grade Submission'], ['FACULTY_EVALUATION', 'Faculty Evaluation'], ['RESEARCH_SUBMISSION', 'Research Submission'],
    ['THESIS_DEFENSE', 'Thesis Defense'], ['CLEARANCE', 'Clearance'], ['LIBRARY_RETURN', 'Library Return'],
    ['SCHOLARSHIP_APPLICATION', 'Scholarship Application'], ['OJT_APPLICATION', 'OJT Application'], ['OJT_REQUIREMENTS', 'OJT Requirements'],
    ['GRADUATION_REQUIREMENTS', 'Graduation Requirements'], ['OTHER_ACADEMIC_DEADLINE', 'Other Academic Deadline'],
  ],
}

const TYPE_LABELS = Object.fromEntries(DAY_TYPES.map((option) => [option.value, option.label]))
const TYPE_CLASS = { SCHOOL_DAY: 'school-day', HOLIDAY: 'holiday', SUSPENSION: 'suspension', SPECIAL_NON_CLASS_DAY: 'non-class', SCHOOL_EVENT: 'event', ACTIVITY: 'event', EXAMINATION: 'examination', ENROLLMENT: 'enrollment', ACADEMIC_DEADLINE: 'deadline', WEEKEND: 'weekend' }
const STATUS_LABELS = { DRAFT: 'Draft', PENDING_APPROVAL: 'Pending Approval', APPROVED: 'Approved', PUBLISHED: 'Published', REJECTED: 'Rejected', CANCELLED: 'Cancelled', ARCHIVED: 'Archived' }

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

function dateKey(date) { return date.toISOString().slice(0, 10) }
function monthLabel(date) { return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) }
function formatCalendarDate(value) { return value ? new Date(`${value}T00:00:00`).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }) : 'No date' }
function displayType(type) { return TYPE_LABELS[type] || type?.replaceAll('_', ' ') || 'Calendar entry' }

export function SchoolCalendarPage() {
  const { user } = useAuth()
  const [calendarEntries, setCalendarEntries] = useState([])
    const [recurringEvents, setRecurringEvents] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [subjects, setSubjects] = useState([])
  const [teachers, setTeachers] = useState([])
  const [selectedAcademicYearId, setSelectedAcademicYearId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [conflictDetails, setConflictDetails] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [selectedEntry, setSelectedEntry] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1))
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [form, setForm] = useState({
    academic_year: '',
    calendar_date: '',
    end_date: '',
    day_type: 'HOLIDAY',
    event_type: '',
    title: '',
    remarks: '',
    attendance_expected: false,
    classes_suspended: false,
    scope_type: 'SCHOOL_WIDE',
    start_time: '',
    end_time: '',
    reason: '',
    suspension_type: 'OTHER',
    affected_department: '',
    announcement: '',
    location: '',
    organizer: '',
    target_participants: '',
    status: 'DRAFT',
    cancellation_reason: '',
    examination_type: '',
    examination_period: '',
    subject: '',
    instructor: '',
    affected_grade_level: '',
    section: '',
    recurrence_enabled: false,
    frequency: 'WEEKLY',
    recurrence_end_date: '',
    recurrence_interval: 1,
    recurrence_weekday: 4,
    recurrence_week: 1,
    recurrence_month: '',
    recurrence_month_day: '',
  })

  useEffect(() => {
    let active = true

    async function loadAcademicYears() {
      try {
        const data = await getAcademicYears()
        const yearItems = normalizeListResponse(data).items
        if (!active) return

        setAcademicYears(yearItems)
        const defaultYear = yearItems.find((year) => year.is_active) || yearItems[0]
        if (defaultYear) {
          const defaultYearId = String(defaultYear.id)
          setSelectedAcademicYearId(defaultYearId)
          setForm((previous) => ({ ...previous, academic_year: defaultYearId }))
        }
      } catch (err) {
        if (active) setError(getApiErrorMessage(err))
      }
    }

    loadAcademicYears()
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!selectedAcademicYearId) {
      return
    }

    let active = true
    async function loadCalendar() {
      setLoading(true)
      setError('')
      try {
        const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
        if (!active) return
        setCalendarEntries(normalizeListResponse(data).items)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadCalendar()
    return () => { active = false }
  }, [selectedAcademicYearId])

  const visibleEntries = useMemo(() => calendarEntries.filter((entry) => {
    const searchMatch = !search || `${entry.title} ${entry.remarks} ${entry.location}`.toLowerCase().includes(search.toLowerCase())
    return searchMatch && (typeFilter === 'ALL' || entry.day_type === typeFilter) && (statusFilter === 'ALL' || entry.status === statusFilter)
  }), [calendarEntries, search, typeFilter, statusFilter])
  const entriesByDate = useMemo(() => visibleEntries.reduce((result, entry) => { (result[entry.calendar_date] ||= []).push(entry); return result }, {}), [visibleEntries])
  const monthDays = useMemo(() => {
    const first = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1)
    const start = new Date(first)
    start.setDate(1 - ((first.getDay() + 6) % 7))
    return Array.from({ length: 42 }, (_, index) => { const date = new Date(start); date.setDate(start.getDate() + index); return date })
  }, [currentMonth])
  const monthEntries = useMemo(() => visibleEntries.filter((entry) => entry.calendar_date?.startsWith(`${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}`)), [visibleEntries, currentMonth])
  const summary = { school: monthEntries.filter((entry) => entry.day_type === 'SCHOOL_DAY').length, holiday: monthEntries.filter((entry) => entry.day_type === 'HOLIDAY').length, suspension: monthEntries.filter((entry) => entry.day_type === 'SUSPENSION').length, nonClass: monthEntries.filter((entry) => ['SPECIAL_NON_CLASS_DAY', 'WEEKEND'].includes(entry.day_type)).length }

  useEffect(() => {
    if (!selectedAcademicYearId) return
    Promise.all([
      getGradeLevels({ is_active: true }),
      getSections({ academic_year: selectedAcademicYearId, is_active: true }),
      getSubjects({ active_only: true }),
      getUsers({ active_only: true, role_name: 'TEACHER' }),
    ]).then(([gradeData, sectionData, subjectData, teacherData]) => {
      setGradeLevels(normalizeListResponse(gradeData).items)
      setSections(normalizeListResponse(sectionData).items)
      setSubjects(normalizeListResponse(subjectData).items)
      setTeachers(normalizeListResponse(teacherData).items)
    }).catch((err) => setError(getApiErrorMessage(err)))
  }, [selectedAcademicYearId])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccessMessage('')
    setConflictDetails([])

    try {
      const payloadAcademicYear = Number(form.academic_year || selectedAcademicYearId)
      const savePayload = {
        ...form,
        academic_year: payloadAcademicYear,
      }
      if (form.recurrence_enabled && !editingId) {
        await createRecurringSchoolCalendarEvent({
          ...savePayload,
          start_date: savePayload.calendar_date,
          recurrence_end_date: savePayload.recurrence_end_date,
        })
      } else {
        delete savePayload.recurrence_enabled
        delete savePayload.frequency
        delete savePayload.recurrence_end_date
        delete savePayload.recurrence_interval
        delete savePayload.recurrence_weekday
        delete savePayload.recurrence_week
        delete savePayload.recurrence_month
        delete savePayload.recurrence_month_day
        if (!editingId) {
          const conflictResult = await checkSchoolCalendarConflicts(savePayload)
          setConflictDetails(conflictResult.conflicts || [])
          if ((conflictResult.conflicts || []).some((conflict) => conflict.severity === 'ERROR')) {
            setError('This event has a definite scheduling conflict and was not saved.')
            return
          }
        }
        if (editingId) await updateSchoolCalendarDay(editingId, savePayload)
        else await createSchoolCalendarDay(savePayload)
      }
      setSuccessMessage(editingId ? 'School calendar entry updated.' : 'School calendar entry saved.')
      const data = await getSchoolCalendarDays({ academic_year: payloadAcademicYear, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
      setForm((previous) => ({
        ...previous,
        academic_year: String(payloadAcademicYear),
        calendar_date: '',
        end_date: '',
        day_type: 'HOLIDAY',
        event_type: '',
        title: '',
        remarks: '',
        attendance_expected: false,
        classes_suspended: false,
        scope_type: 'SCHOOL_WIDE',
        affected_grade_level: '', section: '', examination_type: '', examination_period: '', subject: '', instructor: '',
        start_time: '', end_time: '', reason: '', suspension_type: 'OTHER', affected_department: '', announcement: '', location: '', organizer: '', target_participants: '', status: 'DRAFT', cancellation_reason: '', recurrence_enabled: false, recurrence_end_date: '', recurrence_interval: 1, recurrence_weekday: 4, recurrence_week: 1, recurrence_month: '', recurrence_month_day: '',
      }))
      setEditingId(null)
      setShowForm(false)
      setSelectedAcademicYearId(String(payloadAcademicYear))
      const recurringData = await getRecurringSchoolCalendarEvents({ academic_year: payloadAcademicYear, ordering: 'start_date' })
      setRecurringEvents(normalizeListResponse(recurringData).items)
    } catch (err) {
      setConflictDetails(err.response?.data?.conflicts || [])
      setError(getApiErrorMessage(err))
    }
  }

  function editEntry(entry) {
    setEditingId(entry.id)
    setSelectedEntry(entry)
    setShowForm(true)
    const editableFields = [
      'academic_year', 'calendar_date', 'day_type', 'title', 'remarks', 'attendance_expected',
      'end_date', 'event_type',
      'classes_suspended', 'scope_type', 'affected_grade_level', 'section', 'affected_department',
      'start_time', 'end_time', 'reason', 'suspension_type', 'announcement', 'location',
      'organizer', 'target_participants', 'status', 'cancellation_reason',
      'examination_type', 'examination_period', 'subject', 'instructor',
    ]
    const editableEntry = Object.fromEntries(editableFields.map((field) => [field, entry[field] ?? '']))
    setForm({ ...form, ...editableEntry, academic_year: String(entry.academic_year) })
  }

  async function submitEntryForApproval(entry) {
    try {
      await submitSchoolCalendarDayForApproval(entry.id)
      setSuccessMessage('Calendar entry submitted for approval.')
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function approveEntry(entry) {
    const note = window.prompt('Approval notes (optional)', '') || ''
    try {
      await approveSchoolCalendarDay(entry.id, note.trim())
      setSuccessMessage('Calendar entry approved.')
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function rejectEntry(entry) {
    const reason = window.prompt('Rejection reason is required')
    if (!reason?.trim()) {
      setError('Rejection reason is required.')
      return
    }
    try {
      await rejectSchoolCalendarDay(entry.id, reason.trim())
      setSuccessMessage('Calendar entry rejected.')
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function publishEntry(entry) {
    try {
      await publishSchoolCalendarDay(entry.id)
      setSuccessMessage('Calendar entry published.')
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function cancelEntry(entry) {
    const reason = window.prompt('Cancellation reason')
    if (!reason?.trim()) return
    try {
      await cancelSchoolCalendarDay(entry.id, reason.trim())
      setSuccessMessage('Calendar entry cancelled and preserved in history.')
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function deactivateRecurringEvent(event) {
    try {
      await deactivateRecurringSchoolCalendarEvent(event.id)
      setRecurringEvents((previous) => previous.map((item) => item.id === event.id ? { ...item, active: false } : item))
      setSuccessMessage('Recurring event deactivated. Existing calendar occurrences were preserved.')
    } catch (err) { setError(getApiErrorMessage(err)) }
  }

  async function handleImportPhilippineHolidays() {
    if (!selectedAcademicYearId) {
      setError('Select an academic year before importing holidays.')
      return
    }

    setError('')
    setSuccessMessage('')

    try {
      const result = await importPhilippineHolidays(selectedAcademicYearId)
      const data = await getSchoolCalendarDays({ academic_year: selectedAcademicYearId, ordering: 'calendar_date' })
      setCalendarEntries(normalizeListResponse(data).items)
      setSuccessMessage(result.message || 'Philippine holidays imported successfully.')
    } catch (err) {
      setError(getApiErrorMessage(err))
    }
  }

  return (
    <div className="page-stack attendance-page">
      <PageHeader
        eyebrow="Academic operations"
        title="School Calendar"
        description="Manage holidays, suspensions, and non-class days"
        actions={<button type="button" className="btn btn-primary" onClick={() => { setEditingId(null); setShowForm(true) }}><PlusIcon className="icon" /> Add Event</button>}
      />

      {error ? <ErrorBanner message={error} /> : null}
      {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}
      {conflictDetails.length > 0 ? <div className="status-banner"><strong>Scheduling conflicts</strong>{conflictDetails.map((conflict) => <div key={`${conflict.event_id}-${conflict.recurrence_date || conflict.date}-${conflict.conflict_types.join('-')}`}>{conflict.severity}: {conflict.title} ({conflict.conflict_types.join(', ')}) on {conflict.recurrence_date || conflict.date}{conflict.start_time ? `, ${conflict.start_time}-${conflict.end_time || ''}` : ''}{conflict.location ? `, ${conflict.location}` : ''}</div>)}</div> : null}

      <div className="calendar-filter-bar"><label><span>Search events</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search title or location" /></label><label><span>Event type</span><select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}><option value="ALL">All types</option>{DAY_TYPES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label><label><span>Status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="ALL">All statuses</option>{Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label><span>Academic year</span><select value={selectedAcademicYearId} onChange={(event) => { setSelectedAcademicYearId(event.target.value); setForm((previous) => ({ ...previous, academic_year: event.target.value })) }}>{academicYears.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}</select></label></div>
      <section className="calendar-summary">{[['school', 'School Days', summary.school, 'Attendance expected'], ['holiday', 'Holidays', summary.holiday, 'No attendance'], ['suspension', 'Suspensions', summary.suspension, 'No attendance'], ['non-class', 'Non-Class Days', summary.nonClass, 'No attendance']].map(([key, label, count, note]) => <div className={`calendar-stat calendar-stat--${key}`} key={key}><strong>{count}</strong><span>{label}</span><small>{monthLabel(currentMonth)} · {note}</small></div>)}</section>
      <section className="calendar-layout"><div className="calendar-main panel-card"><div className="calendar-nav"><button type="button" className="icon-button icon-button--light" onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))} aria-label="Previous month"><ChevronLeftIcon className="icon" /></button><div><p className="eyebrow">Monthly view</p><h2>{monthLabel(currentMonth)}</h2></div><button type="button" className="icon-button icon-button--light" onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))} aria-label="Next month"><ChevronRightIcon className="icon" /></button><select aria-label="Calendar view"><option>Month</option></select><button type="button" className="btn btn-outline btn-sm" onClick={() => setCurrentMonth(new Date(new Date().getFullYear(), new Date().getMonth(), 1))}>Today</button></div><div className="calendar-grid" role="grid" aria-label={monthLabel(currentMonth)}><div className="calendar-weekdays">{['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'].map((day) => <span key={day}>{day}</span>)}</div><div className="calendar-days">{monthDays.map((date) => { const key = dateKey(date); const entries = entriesByDate[key] || []; return <button type="button" role="gridcell" className={`calendar-day ${date.getMonth() !== currentMonth.getMonth() ? 'calendar-day--outside' : ''} ${date.getDay() === 0 || date.getDay() === 6 ? 'calendar-day--weekend' : ''} ${key === dateKey(new Date()) ? 'calendar-day--today' : ''} ${selectedEntry?.calendar_date === key ? 'calendar-day--selected' : ''}`} key={key} onClick={() => setSelectedEntry(entries[0] || null)}><span className="calendar-date">{date.getDate()}</span><span className="calendar-markers">{entries.slice(0, 4).map((entry) => <i className={`calendar-marker calendar-marker--${TYPE_CLASS[entry.day_type] || 'event'}`} key={entry.id} title={`${displayType(entry.day_type)}: ${entry.title}`} />)}</span><span className="calendar-cell-titles">{entries.slice(0, 2).map((entry) => <span key={entry.id}>{entry.title}</span>)}</span></button> })}</div></div><div className="calendar-legend"><span><i className="calendar-marker calendar-marker--school-day" /> School Day</span><span><i className="calendar-marker calendar-marker--holiday" /> Holiday</span><span><i className="calendar-marker calendar-marker--suspension" /> Suspension</span><span><i className="calendar-marker calendar-marker--non-class" /> Non-Class Day</span><span><i className="calendar-marker calendar-marker--event" /> Special Event</span></div></div><aside className="calendar-details panel-card">{selectedEntry ? <><div className="details-heading"><div><p className="eyebrow">Selected event</p><h2>{selectedEntry.title || displayType(selectedEntry.day_type)}</h2></div><button type="button" className="icon-button icon-button--light" onClick={() => setSelectedEntry(null)} aria-label="Close event details"><XMarkIcon className="icon" /></button></div>{(entriesByDate[selectedEntry.calendar_date] || []).length > 1 ? <div className="date-event-list"><p className="form-help">Events on this date</p>{entriesByDate[selectedEntry.calendar_date].map((entry) => <button type="button" className={`date-event-option ${entry.id === selectedEntry.id ? 'date-event-option--active' : ''}`} key={entry.id} onClick={() => setSelectedEntry(entry)}><span className={`calendar-marker calendar-marker--${TYPE_CLASS[entry.day_type] || 'event'}`} />{entry.title}</button>)}</div> : null}<div className="event-badge-row"><span className={`event-badge event-badge--${TYPE_CLASS[selectedEntry.day_type] || 'event'}`}>{displayType(selectedEntry.day_type)}</span><span className="badge badge--status">{STATUS_LABELS[selectedEntry.status] || selectedEntry.status}</span></div><dl className="event-facts"><div><dt>Date</dt><dd>{formatCalendarDate(selectedEntry.calendar_date)}{selectedEntry.end_date ? ` to ${formatCalendarDate(selectedEntry.end_date)}` : ''}</dd></div><div><dt>Attendance</dt><dd className={selectedEntry.attendance_expected ? 'attendance-yes' : 'attendance-no'}>{selectedEntry.attendance_expected ? 'Attendance expected' : 'No attendance expected'}</dd></div><div><dt>Time</dt><dd>{selectedEntry.start_time ? `${selectedEntry.start_time} - ${selectedEntry.end_time || 'No end time'}` : 'All day'}</dd></div><div><dt>Location</dt><dd>{selectedEntry.location || 'Not specified'}</dd></div><div><dt>Academic year</dt><dd>{academicYears.find((year) => year.id === selectedEntry.academic_year)?.name || 'Not specified'}</dd></div></dl><p className="event-description">{selectedEntry.remarks || selectedEntry.reason || 'No additional details.'}</p><button type="button" className="btn btn-primary btn-sm" onClick={() => editEntry(selectedEntry)}>Edit event</button></> : <EmptyState title="Select a date" message="Choose a date to inspect its events and workflow status." />}</aside></section>
      <section className={`panel-card record-panel calendar-editor ${showForm ? 'calendar-editor--open' : ''}`}>
        <div className="section-header">
          <div>
            <p className="eyebrow">Academic year context</p>
            <h2>School day classification</h2>
          </div>
          {showForm ? <button type="button" className="icon-button icon-button--light" onClick={() => { setShowForm(false); setEditingId(null) }} aria-label="Close event form"><XMarkIcon className="icon" /></button> : null}
        </div>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            <span>Academic year</span>
            <select value={form.academic_year || selectedAcademicYearId} onChange={(event) => {
              const nextYearId = event.target.value
              setSelectedAcademicYearId(nextYearId)
              setForm((previous) => ({ ...previous, academic_year: nextYearId }))
            }} required>
              <option value="">Select academic year</option>
              {academicYears.map((year) => (
                <option key={year.id} value={String(year.id)}>{year.name}</option>
              ))}
            </select>
          </label>
          {form.scope_type === 'GRADE_LEVEL' ? <label><span>Affected grade level</span><select value={form.affected_grade_level || ''} onChange={(event) => setForm({ ...form, affected_grade_level: event.target.value })} required><option value="">Select grade level</option>{gradeLevels.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}</select></label> : null}
          {form.scope_type === 'SECTION_SPECIFIC' ? <label><span>Affected section</span><select value={form.section || ''} onChange={(event) => setForm({ ...form, section: event.target.value })} required><option value="">Select section</option>{sections.map((section) => <option key={section.id} value={section.id}>{section.name}</option>)}</select></label> : null}
          {form.scope_type === 'DEPARTMENT' ? <label><span>Affected department</span><input value={form.affected_department || ''} onChange={(event) => setForm({ ...form, affected_department: event.target.value })} required /></label> : null}
          {form.day_type === 'EXAMINATION' ? <>
            <label><span>Examination type</span><select value={form.examination_type} onChange={(event) => setForm({ ...form, examination_type: event.target.value })} required><option value="">Select examination type</option><option value="PRELIMINARY">Preliminary Examination</option><option value="MIDTERM">Midterm Examination</option><option value="SEMI_FINAL">Semi-Final Examination</option><option value="FINAL">Final Examination</option><option value="ENTRANCE">Entrance Examination</option><option value="ADMISSION_TEST">Admission Test</option><option value="QUALIFYING">Qualifying Examination</option><option value="OTHER">Other Examination</option></select></label>
            <label><span>Examination period</span><select value={form.examination_period} onChange={(event) => setForm({ ...form, examination_period: event.target.value })}><option value="">Select period</option><option value="PRELIMINARY">Preliminary</option><option value="MIDTERM">Midterm</option><option value="SEMI_FINAL">Semi-Final</option><option value="FINAL">Final</option><option value="OTHER">Other</option></select></label>
            <label><span>Subject</span><select value={form.subject || ''} onChange={(event) => setForm({ ...form, subject: event.target.value })}><option value="">Select subject</option>{subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.code} - {subject.name}</option>)}</select></label>
            <label><span>Instructor</span><select value={form.instructor || ''} onChange={(event) => setForm({ ...form, instructor: event.target.value })}><option value="">Select instructor</option>{teachers.map((teacher) => <option key={teacher.id} value={teacher.id}>{teacher.first_name || teacher.last_name ? `${teacher.first_name || ''} ${teacher.last_name || ''}`.trim() : teacher.username}</option>)}</select></label>
          </> : null}
          {form.day_type === 'SUSPENSION' || form.day_type === 'SCHOOL_EVENT' || form.day_type === 'ACTIVITY' || form.day_type === 'EXAMINATION' || form.day_type === 'ENROLLMENT' || form.day_type === 'ACADEMIC_DEADLINE' ? <>
            <label><span>Start time</span><input type="time" value={form.start_time || ''} onChange={(event) => setForm({ ...form, start_time: event.target.value })} /></label>
            <label><span>End time</span><input type="time" value={form.end_time || ''} onChange={(event) => setForm({ ...form, end_time: event.target.value })} /></label>
            <label><span>Location</span><input value={form.location || ''} onChange={(event) => setForm({ ...form, location: event.target.value })} /></label>
            <label><span>Organizer</span><input value={form.organizer || ''} onChange={(event) => setForm({ ...form, organizer: event.target.value })} /></label>
            <label className="form-grid-full"><span>Target participants</span><input value={form.target_participants || ''} onChange={(event) => setForm({ ...form, target_participants: event.target.value })} /></label>
          </> : null}
          {form.day_type === 'SUSPENSION' ? <>
            <label><span>Suspension type</span><select value={form.suspension_type} onChange={(event) => setForm({ ...form, suspension_type: event.target.value })}><option value="WEATHER_RELATED">Weather-related</option><option value="NATURAL_DISASTER">Natural Disaster</option><option value="LOCAL_GOVERNMENT">Local Government Announcement</option><option value="SCHOOL_ADMINISTRATION">School Administration</option><option value="EMERGENCY">Emergency</option><option value="OTHER">Other</option></select></label>
            <label className="form-grid-full"><span>Announcement</span><textarea value={form.announcement} onChange={(event) => setForm({ ...form, announcement: event.target.value })} rows={2} /></label>
          </> : null}
          <label>
            <span>Date</span>
            <input type="date" value={form.calendar_date} onChange={(event) => setForm({ ...form, calendar_date: event.target.value })} required />
          </label>
          {form.day_type === 'ENROLLMENT' ? <label><span>End date</span><input type="date" value={form.end_date || ''} min={form.calendar_date || undefined} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></label> : null}
          <label className="checkbox-field">
            <input type="checkbox" checked={form.recurrence_enabled} disabled={Boolean(editingId) || form.day_type === 'EXAMINATION'} onChange={(event) => setForm({ ...form, recurrence_enabled: event.target.checked })} />
            <span>Recurring event</span>
          </label>
          {form.recurrence_enabled && !editingId ? <>
            <label><span>Frequency</span><select value={form.frequency} onChange={(event) => setForm({ ...form, frequency: event.target.value })}><option value="DAILY">Daily</option><option value="WEEKLY">Weekly</option><option value="MONTHLY">Monthly</option><option value="YEARLY">Yearly</option><option value="CUSTOM">Custom days</option></select></label>
            <label><span>Recurrence end date</span><input type="date" value={form.recurrence_end_date} onChange={(event) => setForm({ ...form, recurrence_end_date: event.target.value })} required /></label>
            <label><span>Interval</span><input type="number" min="1" value={form.recurrence_interval} onChange={(event) => setForm({ ...form, recurrence_interval: Number(event.target.value) })} required /></label>
            {form.frequency === 'WEEKLY' || form.frequency === 'MONTHLY' ? <label><span>Weekday</span><select value={form.recurrence_weekday} onChange={(event) => setForm({ ...form, recurrence_weekday: Number(event.target.value) })}><option value="0">Monday</option><option value="1">Tuesday</option><option value="2">Wednesday</option><option value="3">Thursday</option><option value="4">Friday</option><option value="5">Saturday</option><option value="6">Sunday</option></select></label> : null}
            {form.frequency === 'MONTHLY' ? <label><span>Week of month</span><select value={form.recurrence_week} onChange={(event) => setForm({ ...form, recurrence_week: Number(event.target.value) })}><option value="1">First</option><option value="2">Second</option><option value="3">Third</option><option value="4">Fourth</option><option value="5">Fifth</option><option value="-1">Last</option></select></label> : null}
            {form.frequency === 'YEARLY' ? <><label><span>Month</span><input type="number" min="1" max="12" value={form.recurrence_month} onChange={(event) => setForm({ ...form, recurrence_month: Number(event.target.value) })} required /></label><label><span>Day of month</span><input type="number" min="1" max="31" value={form.recurrence_month_day} onChange={(event) => setForm({ ...form, recurrence_month_day: Number(event.target.value) })} required /></label></> : null}
          </> : null}
          <label>
            <span>Day type</span>
            <select value={form.day_type} onChange={(event) => setForm({ ...form, day_type: event.target.value, event_type: '', end_date: '', attendance_expected: event.target.value === 'SCHOOL_DAY' || event.target.value === 'EXAMINATION', classes_suspended: event.target.value === 'SUSPENSION', recurrence_enabled: event.target.value === 'EXAMINATION' ? false : form.recurrence_enabled, examination_type: event.target.value === 'EXAMINATION' ? form.examination_type : '', examination_period: event.target.value === 'EXAMINATION' ? form.examination_period : '', subject: event.target.value === 'EXAMINATION' ? form.subject : '', instructor: event.target.value === 'EXAMINATION' ? form.instructor : '' })}>
              {DAY_TYPES.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          {EVENT_TYPES[form.day_type] ? <label><span>{form.day_type === 'ENROLLMENT' ? 'Enrollment activity' : 'Academic deadline'}</span><select value={form.event_type} onChange={(event) => setForm({ ...form, event_type: event.target.value })} required><option value="">Select type</option>{EVENT_TYPES[form.day_type].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label> : null}
          <label>
            <span>Scope</span>
            <select value={form.scope_type} onChange={(event) => setForm({ ...form, scope_type: event.target.value })}>
              <option value="SCHOOL_WIDE">School-wide</option>
              <option value="SECTION_SPECIFIC">Section-specific</option>
            </select>
          </label>
          <label className="form-grid-full">
            <span>Title / reason</span>
            <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
          </label>
          <label className="form-grid-full">
            <span>Remarks</span>
            <textarea value={form.remarks} onChange={(event) => setForm({ ...form, remarks: event.target.value })} rows={3} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.attendance_expected} disabled={form.day_type === 'ENROLLMENT' || form.day_type === 'ACADEMIC_DEADLINE'} onChange={(event) => setForm({ ...form, attendance_expected: event.target.checked })} />
            <span>Attendance expected</span>
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={form.classes_suspended} onChange={(event) => setForm({ ...form, classes_suspended: event.target.checked })} />
            <span>Classes suspended</span>
          </label>

          <div className="section-actions form-grid-full">
            <button type="submit" className="action-button">{editingId ? 'Update calendar entry' : 'Save calendar entry'}</button>
            {editingId ? <button type="button" className="action-button secondary-button" onClick={() => setEditingId(null)}>Cancel edit</button> : null}
            <button type="button" className="action-button secondary-button" onClick={handleImportPhilippineHolidays}>
              Import Philippine Holidays
            </button>
          </div>
        </form>
      </section>

      <section className="panel-card record-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Calendar entries</p>
            <h2>Registered dates</h2>
          </div>
        </div>

        {loading ? <div className="table-skeleton-grid"><div className="students-skeleton-card" /></div> : null}

        {!loading && calendarEntries.length === 0 ? (
          <EmptyState title="No calendar entries" message="No school-day classifications have been recorded yet." />
        ) : null}

        {!loading && visibleEntries.length > 0 ? (
          <div className="table-card">
            <table className="records-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Academic year</th>
                  <th>Type</th>
                  <th>Title</th>
                  <th>Attendance expected</th>
                  <th>Suspended</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleEntries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{entry.end_date ? `${entry.calendar_date} to ${entry.end_date}` : entry.calendar_date || '—'}</td>
                    <td>{academicYears.find((year) => year.id === entry.academic_year)?.name || '—'}</td>
                          <td>{entry.day_type || '—'}</td>
                    <td>{entry.title || '—'}</td>
                    <td>{entry.attendance_expected ? 'Yes' : 'No'}</td>
                    <td>{entry.classes_suspended ? 'Yes' : 'No'}</td>
                    <td>{entry.status || '—'}</td>
                    <td>
                      <button type="button" className="table-action" onClick={() => setSelectedEntry(entry)}>View</button>
                      <button type="button" className="table-action" onClick={() => editEntry(entry)}>Edit</button>
                      {entry.status === 'DRAFT' || entry.status === 'REJECTED' ? (
                        <button type="button" className="table-action" onClick={() => submitEntryForApproval(entry)}>Submit for Approval</button>
                      ) : null}
                      {entry.status === 'PENDING_APPROVAL' && (user?.role_name === 'SCHOOL_ADMIN' || user?.role_name === 'SUPER_ADMIN') ? (
                        <>
                          <button type="button" className="table-action" onClick={() => approveEntry(entry)}>Approve</button>
                          <button type="button" className="table-action" onClick={() => rejectEntry(entry)}>Reject</button>
                        </>
                      ) : null}
                      {entry.status === 'APPROVED' && (user?.role_name === 'SCHOOL_ADMIN' || user?.role_name === 'SUPER_ADMIN') ? (
                        <button type="button" className="table-action" onClick={() => publishEntry(entry)}>Publish</button>
                      ) : null}
                      {entry.status !== 'CANCELLED' ? <button type="button" className="table-action" onClick={() => cancelEntry(entry)}>Cancel</button> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {selectedEntry ? <div className="status-banner"><strong>{selectedEntry.day_type === 'SUSPENSION' ? 'CLASS SUSPENSION' : selectedEntry.day_type === 'EXAMINATION' ? `${selectedEntry.examination_type || 'EXAMINATION'}: ${selectedEntry.title}` : selectedEntry.title}</strong><br />Academic year: {academicYears.find((year) => year.id === selectedEntry.academic_year)?.name || '—'}<br />{selectedEntry.calendar_date}{selectedEntry.end_date ? ` to ${selectedEntry.end_date}` : ''} {selectedEntry.start_time ? `${selectedEntry.start_time} - ${selectedEntry.end_time || ''}` : ''}<br />{selectedEntry.event_type ? `Type: ${selectedEntry.event_type}; ` : ''}{selectedEntry.day_type === 'EXAMINATION' && selectedEntry.examination_period ? `Period: ${selectedEntry.examination_period}; ` : ''}{selectedEntry.reason || selectedEntry.remarks || 'No additional details.'}<br />Status: {selectedEntry.status || '—'}{selectedEntry.rejection_reason ? `; Rejection reason: ${selectedEntry.rejection_reason}` : ''}{selectedEntry.cancellation_reason ? `; Cancellation reason: ${selectedEntry.cancellation_reason}` : ''}</div> : null}
      </section>
      {recurringEvents.length > 0 ? <section className="panel-card record-panel"><div className="section-header"><div><p className="eyebrow">Recurring definitions</p><h2>Active and historical series</h2></div></div><div className="table-card"><table className="records-table"><thead><tr><th>Event</th><th>Rule</th><th>Range</th><th>Occurrences</th><th>Status</th><th>Actions</th></tr></thead><tbody>{recurringEvents.map((event) => <tr key={event.id}><td>{event.title}</td><td>{event.frequency}</td><td>{event.start_date} to {event.recurrence_end_date}</td><td>{event.occurrence_count}</td><td>{event.active ? 'Active' : 'Inactive'}</td><td>{event.active ? <button type="button" className="table-action" onClick={() => deactivateRecurringEvent(event)}>Deactivate</button> : null}</td></tr>)}</tbody></table></div></section> : null}
    </div>
  )
}

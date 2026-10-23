import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { PageHeader } from '../../components/common/PageHeader'
import { getApiErrorMessage } from '../../services/api'
import { getAcademicYears, getGradeLevels, getSections, getStrands } from '../../services/academicsService'
import { createEnrollment, getStudents } from '../../services/studentService'
import apiClient from '../../services/api'

function normalizeListResponse(data) {
  const items = data?.results || data || []
  return { items, count: typeof data?.count === 'number' ? data.count : Array.isArray(items) ? items.length : 0 }
}

const enrollmentSteps = [
  'Enrollment Type & Level',
  'Grade Level',
  'Strand',
  'Section',
  'Student',
  'Review',
]

const enrollmentTypes = [
  'Continuing Student',
  'Transferee',
  'New Student',
  'Returning Student',
]

const educationLevels = [
  { value: 'Elementary', label: 'Elementary' },
  { value: 'Junior High School', label: 'Junior High' },
  { value: 'Senior High School', label: 'Senior High' },
]

export function EnrollmentPage() {
  const [enrollments, setEnrollments] = useState([])
  const [students, setStudents] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [gradeLevels, setGradeLevels] = useState([])
  const [sections, setSections] = useState([])
  const [strands, setStrands] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [wizardError, setWizardError] = useState('')
  const [currentStep, setCurrentStep] = useState(0)
  const [enrollmentType, setEnrollmentType] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('')
  const [selectedGradeId, setSelectedGradeId] = useState('')
  const [selectedStrandId, setSelectedStrandId] = useState('')
  const [studentStrandSelections, setStudentStrandSelections] = useState({})
  const [selectedSectionId, setSelectedSectionId] = useState('')
  const [selectedStudentIds, setSelectedStudentIds] = useState([])
  const [selectionResetNotice, setSelectionResetNotice] = useState('')
  const [completedStudentIds, setCompletedStudentIds] = useState([])
  const [enrollmentResult, setEnrollmentResult] = useState(null)
  const [priorEnrollmentHistory, setPriorEnrollmentHistory] = useState({})
  const [historyLoadErrors, setHistoryLoadErrors] = useState({})
  const [historyLoading, setHistoryLoading] = useState(false)
  const [studentSearch, setStudentSearch] = useState('')
  const [searchedStudentIds, setSearchedStudentIds] = useState([])
  const [searchedStudentQuery, setSearchedStudentQuery] = useState('')
  const [searchedEnrollmentType, setSearchedEnrollmentType] = useState('')
  const [studentSearchLoading, setStudentSearchLoading] = useState(true)
  const [studentSearchError, setStudentSearchError] = useState('')
  const [sectionSearch, setSectionSearch] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [restartConfirmationOpen, setRestartConfirmationOpen] = useState(false)
  const selectAllStudentsRef = useRef(null)

  useEffect(() => {
    let active = true

    async function loadData() {
      setLoading(true)
      setError('')
      try {
        const [enrollmentData, yearData, gradeData, sectionData, strandData] = await Promise.all([
          apiClient.get('/enrollments/?status=all'),
          getAcademicYears(),
          getGradeLevels(),
          getSections(),
          getStrands(),
        ])

        if (!active) return

        const yearList = normalizeListResponse(yearData).items
        const gradeList = normalizeListResponse(gradeData).items
        const sectionList = normalizeListResponse(sectionData).items
        const strandList = normalizeListResponse(strandData).items
        setEnrollments(normalizeListResponse(enrollmentData.data).items)
        setAcademicYears(yearList)
        setGradeLevels(gradeList)
        setSections(sectionList)
        setStrands(strandList)
      } catch (err) {
        if (!active) return
        setError(getApiErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }

    loadData()
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    const query = studentSearch.trim()
    const enrollmentTypeFilter = enrollmentType
      ? enrollmentType.toLowerCase().replace(/\s+/g, '_')
      : ''
    setStudentSearchLoading(true)
    setStudentSearchError('')

    const timer = setTimeout(async () => {
      try {
        const response = await getStudents({
          search: query,
          enrollment_type: enrollmentTypeFilter || undefined,
        })
        if (!active) return
        const results = normalizeListResponse(response).items
        setStudents((current) => {
          const studentsById = new Map(current.map((student) => [String(student.id), student]))
          results.forEach((student) => studentsById.set(String(student.id), student))
          return [...studentsById.values()]
        })
        setSearchedStudentIds(results.map((student) => String(student.id)))
        setSearchedStudentQuery(query)
        setSearchedEnrollmentType(enrollmentTypeFilter)
      } catch (err) {
        if (!active) return
        setSearchedStudentIds([])
        setSearchedStudentQuery(query)
        setSearchedEnrollmentType(enrollmentTypeFilter)
        setStudentSearchError(getApiErrorMessage(err))
      } finally {
        if (active) setStudentSearchLoading(false)
      }
    }, 250)

    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [enrollmentType, studentSearch])

  const activeYears = useMemo(() => academicYears.filter((year) => year.is_active), [academicYears])
  const selectedYear = activeYears.length === 1 ? activeYears[0] : null
  const selectedYearId = selectedYear ? String(selectedYear.id) : ''
  const precedingAcademicYear = useMemo(() => {
    if (!selectedYear?.start_date || !selectedYear?.end_date) return null
    const precedingYears = academicYears
      .filter((year) => year.start_date && year.start_date < selectedYear.start_date)
      .sort((left, right) => String(right.start_date).localeCompare(String(left.start_date)))
    const nearestStartDate = precedingYears[0]?.start_date
    const nearestYears = precedingYears.filter((year) => year.start_date === nearestStartDate)
    if (
      nearestYears.length !== 1 ||
      !nearestYears[0].end_date ||
      nearestYears[0].end_date >= selectedYear.start_date
    ) {
      return null
    }
    return nearestYears[0]
  }, [academicYears, selectedYear])

  const selectedGrade = useMemo(
    () => gradeLevels.find((grade) => String(grade.id) === String(selectedGradeId)) || null,
    [gradeLevels, selectedGradeId],
  )

  const selectedSection = useMemo(
    () => sections.find((section) => String(section.id) === String(selectedSectionId)) || null,
    [sections, selectedSectionId],
  )

  const selectedStudents = useMemo(
    () => students.filter((student) => selectedStudentIds.map(String).includes(String(student.id))),
    [students, selectedStudentIds],
  )

  const selectedStudentIdSet = useMemo(
    () => new Set(selectedStudentIds.map(String)),
    [selectedStudentIds],
  )

  const selectedStrand = useMemo(
    () => strands.find((strand) => String(strand.id) === String(selectedStrandId)) || null,
    [strands, selectedStrandId],
  )

  const filteredLevels = useMemo(
    () => gradeLevels.filter((grade) => grade.is_active !== false && (!selectedLevel || grade.school_level === selectedLevel)),
    [gradeLevels, selectedLevel],
  )

  const requiresStrand = selectedGrade?.school_level === 'Senior High School'

  const sectionOptions = useMemo(() => {
    const query = sectionSearch.trim().toLowerCase()
    return sections.filter((section) => {
      const matchesYear = section.is_active !== false && String(section.academic_year) === String(selectedYearId)
      const matchesGrade = String(section.grade_level) === String(selectedGradeId)
      const matchesStrand = !requiresStrand || !section.strand || String(section.strand) === String(selectedStrandId)
      const matchesQuery = !query || `${section.name || ''} ${section.adviser_name || ''} ${section.description || ''}`.toLowerCase().includes(query)
      return matchesYear && matchesGrade && matchesStrand && matchesQuery
    })
  }, [sections, selectedYearId, selectedGradeId, selectedStrandId, sectionSearch, requiresStrand, enrollments])

  const availableStudents = useMemo(() => {
    const query = studentSearch.trim().toLowerCase()
    const enrollmentTypeFilter = enrollmentType.toLowerCase().replace(/\s+/g, '_')
    if (
      searchedStudentQuery !== studentSearch.trim() ||
      searchedEnrollmentType !== enrollmentTypeFilter
    ) {
      return []
    }

    return students.filter((student) => {
      if (!searchedStudentIds.includes(String(student.id))) {
        return false
      }

      if (!query) {
        return true
      }

      const lrn = String(student.lrn || '').toLowerCase()
      const firstName = String(student.first_name || '').toLowerCase()
      const lastName = String(student.last_name || '').toLowerCase()
      const fullName = `${student.first_name || ''} ${student.last_name || ''}`.trim().toLowerCase()
      return lrn.includes(query) || firstName.includes(query) || lastName.includes(query) || fullName.includes(query)
    })
  }, [enrollmentType, searchedEnrollmentType, searchedStudentIds, searchedStudentQuery, studentSearch, students])

  const visibleStudentIds = useMemo(
    () => availableStudents.map((student) => String(student.id)),
    [availableStudents],
  )
  const visibleSelectedCount = visibleStudentIds.filter((id) => selectedStudentIdSet.has(id)).length
  const allVisibleStudentsSelected = visibleStudentIds.length > 0 && visibleSelectedCount === visibleStudentIds.length
  const hiddenSelectedCount = selectedStudentIds.length - visibleSelectedCount
  const searchResultsCurrent = searchedStudentQuery === studentSearch.trim() &&
    searchedEnrollmentType === enrollmentType.toLowerCase().replace(/\s+/g, '_')

  useEffect(() => {
    if (selectAllStudentsRef.current) {
      selectAllStudentsRef.current.indeterminate =
        enrollmentType !== 'Transferee' && visibleSelectedCount > 0 && !allVisibleStudentsSelected
    }
  }, [allVisibleStudentsSelected, enrollmentType, visibleSelectedCount])

  function resetWizard() {
    setRestartConfirmationOpen(false)
    setCurrentStep(0)
    setEnrollmentType('')
    setSelectedLevel('')
    setSelectedGradeId('')
    setSelectedStrandId('')
    setStudentStrandSelections({})
    setSelectedSectionId('')
    setSelectedStudentIds([])
    setSelectionResetNotice('')
    setCompletedStudentIds([])
    setEnrollmentResult(null)
    setStudentSearch('')
    setSectionSearch('')
    setWizardError('')
    setSuccessMessage('')
  }

  const hasWizardProgress = Boolean(
    currentStep > 0 ||
    enrollmentType ||
    selectedLevel ||
    selectedGradeId ||
    selectedStrandId ||
    selectedSectionId ||
    selectedStudentIds.length,
  )

  function requestWizardRestart() {
    if (hasWizardProgress) {
      setRestartConfirmationOpen(true)
      return
    }
    resetWizard()
  }

  function handleEnrollmentTypeChange(type) {
    if (type === enrollmentType) return
    if (selectedStudentIds.length > 0) {
      setSelectionResetNotice(
        `Your ${selectedStudentIds.length} selected student${selectedStudentIds.length === 1 ? ' was' : 's were'} cleared because the eligible student list changed with the enrollment type.`,
      )
    } else {
      setSelectionResetNotice('')
    }
    setEnrollmentType(type)
    setSelectedStudentIds([])
    setStudentStrandSelections({})
    setCompletedStudentIds([])
    setEnrollmentResult(null)
    setSuccessMessage('')
    setWizardError('')
  }

  function validateCurrentStep() {
    if (!selectedYear) {
      setWizardError('A single active academic year is required. Ask an administrator to configure Academic Year Management.')
      return false
    }

    if (currentStep === 0) {
      if (!enrollmentType) {
        setWizardError('Choose an enrollment type before continuing.')
        return false
      }
      if (!selectedLevel) {
        setWizardError('Choose an educational level before continuing.')
        return false
      }
      return true
    }

    if (currentStep === 1) {
      if (!selectedGradeId) {
        setWizardError('Choose a grade level before continuing.')
        return false
      }
      return true
    }

    if (currentStep === 2) {
      if (!requiresStrand) {
        return true
      }
      if (!selectedStrandId) {
        setWizardError('Select a strand for Grade 11 or Grade 12.')
        return false
      }
      return true
    }

    if (currentStep === 3) {
      if (!selectedSectionId) {
        setWizardError('Select a section to continue.')
        return false
      }
      return true
    }

    if (currentStep === 4) {
      if (selectedStudentIds.length === 0) {
        setWizardError('Choose a student before continuing.')
        return false
      }
      return true
    }

    return true
  }

  function handlePrevious() {
    setWizardError('')
    setCurrentStep((step) => Math.max(step - 1, 0))
  }

  function handleNext() {
    if (!validateCurrentStep()) {
      return
    }

    let nextStep = currentStep + 1
    if (currentStep === 1 && !requiresStrand) {
      nextStep += 1
    }

    setWizardError('')
    setCurrentStep(Math.min(nextStep, enrollmentSteps.length - 1))
  }

  async function handleEnroll() {
    if (!selectedYear || !selectedGradeId || !selectedSectionId || selectedStudentIds.length === 0) {
      setWizardError('Complete the enrollment wizard before submitting.')
      return
    }

    if (
      !selectedGrade ||
      selectedGrade.is_active === false ||
      selectedGrade.school_level !== selectedLevel ||
      !selectedSection ||
      selectedSection.is_active === false ||
      String(selectedSection.academic_year) !== String(selectedYearId) ||
      String(selectedSection.grade_level) !== String(selectedGradeId) ||
      (requiresStrand && !selectedStrandId) ||
      (!requiresStrand && selectedStrandId) ||
      (selectedSection.strand && String(selectedSection.strand) !== String(selectedStrandId))
    ) {
      setWizardError('Review the academic year, grade level, strand, and section selections before enrolling.')
      return
    }

    const studentsToEnroll = selectedStudentIds.filter(
      (id) => !completedStudentIds.map(String).includes(String(id)),
    )
    if (studentsToEnroll.length === 0) {
      setWizardError('All selected students have already been processed in this enrollment session.')
      return
    }

    const successfulStudents = []
    const rejectedStudents = []
    const createdEnrollments = []
    const enrollmentTypeFilter = enrollmentType.toLowerCase().replace(/\s+/g, '_')

    try {
      setSubmitting(true)
      setWizardError('')
      setEnrollmentResult(null)

      for (const studentId of studentsToEnroll) {
        const student = students.find((item) => String(item.id) === String(studentId))
        if (!student) {
          rejectedStudents.push({
            id: String(studentId),
            name: `Student ${studentId}`,
            reason: 'This student record is no longer available. Search again and select a current record.',
          })
          continue
        }

        const assignedStrandId = requiresStrand
          ? studentStrandSelections[String(studentId)] ?? selectedStrandId
          : ''
        const assignedStrand = strands.find(
          (strand) => String(strand.id) === String(assignedStrandId) && strand.is_active !== false,
        )
        if (requiresStrand && (
          !assignedStrand ||
          (selectedSection.strand && String(selectedSection.strand) !== String(assignedStrand.id))
        )) {
          rejectedStudents.push({
            id: String(studentId),
            name: `${student.first_name || ''} ${student.last_name || ''}`.trim(),
            reason: 'Choose an active strand for this student that is compatible with the selected section.',
          })
          continue
        }

        try {
          const eligibilityResponse = await getStudents({
            enrollment_type: enrollmentTypeFilter,
            student_ids: String(studentId),
          })
          const eligibleStudents = normalizeListResponse(eligibilityResponse).items
          if (!eligibleStudents.some((candidate) => String(candidate.id) === String(studentId))) {
            rejectedStudents.push({
              id: String(studentId),
              name: `${student.first_name || ''} ${student.last_name || ''}`.trim(),
              reason: 'This student no longer matches the selected enrollment type or already has an enrollment for the active academic year.',
            })
            continue
          }

          const createdEnrollment = await createEnrollment({
            student: Number(studentId),
            academic_year: Number(selectedYearId),
            grade_level: Number(selectedGradeId),
            section: Number(selectedSectionId),
            strand: assignedStrandId ? Number(assignedStrandId) : null,
            enrollment_status: 'active',
            enrollment_date: new Date().toISOString().slice(0, 10),
          })
          successfulStudents.push(student)
          createdEnrollments.push(createdEnrollment)
        } catch (err) {
          rejectedStudents.push({
            id: String(studentId),
            name: `${student.first_name || ''} ${student.last_name || ''}`.trim(),
            reason: getApiErrorMessage(err),
          })
        }
      }

      if (successfulStudents.length) {
        setCompletedStudentIds((current) => [
          ...new Set([...current, ...successfulStudents.map((student) => String(student.id))]),
        ])
      }
      const completedIds = new Set([
        ...completedStudentIds.map(String),
        ...successfulStudents.map((student) => String(student.id)),
      ])
      const completedStudents = students.filter((student) => completedIds.has(String(student.id)))
      setSuccessMessage(completedStudents.length
        ? `${completedStudents.length} student${completedStudents.length === 1 ? '' : 's'} enrolled: ${completedStudents.map((student) => `${student.first_name || ''} ${student.last_name || ''}`.trim()).join(', ')}.`
        : '')
      setEnrollmentResult({ failures: rejectedStudents })
      if (createdEnrollments.length) {
        const createdIds = new Set(createdEnrollments.map((enrollment) => String(enrollment.id)))
        setEnrollments((current) => [
          ...createdEnrollments,
          ...current.filter((enrollment) => !createdIds.has(String(enrollment.id))),
        ])
      }

      try {
        const refreshed = await apiClient.get('/enrollments/?status=all')
        const refreshedEnrollments = normalizeListResponse(refreshed.data).items
        setEnrollments((current) => {
          const enrollmentById = new Map(current.map((enrollment) => [String(enrollment.id), enrollment]))
          refreshedEnrollments.forEach((enrollment) => enrollmentById.set(String(enrollment.id), enrollment))
          return [...enrollmentById.values()]
        })
      } catch (err) {
        setWizardError(`Enrollment submission finished, but the enrollment history could not refresh. ${getApiErrorMessage(err)}`)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const reviewSummary = useMemo(() => ({
    students: selectedStudents,
    schoolYear: selectedYear?.name || 'Not configured',
    grade: selectedGrade?.name || 'Not selected',
    strand: selectedStrand?.name || 'Not applicable',
    section: selectedSection ? `${selectedSection.name}` : 'Not selected',
    adviser: selectedSection?.adviser_name || selectedSection?.adviser || 'Not assigned',
  }), [selectedSection, selectedStrand, selectedStudents, selectedYear, selectedGrade])

  const studentEnrollmentHistory = useMemo(() => {
    const history = new Map()
    for (const student of selectedStudents) {
      history.set(
        String(student.id),
        enrollments.filter((entry) => String(entry.student) === String(student.id)),
      )
    }
    return history
  }, [enrollments, selectedStudents])

  useEffect(() => {
    if (currentStep !== 5 || enrollmentType !== 'Returning Student' || selectedStudents.length === 0) {
      setHistoryLoading(false)
      return undefined
    }

    let active = true
    setHistoryLoading(true)
    setPriorEnrollmentHistory({})
    setHistoryLoadErrors({})

    async function loadPriorEnrollmentHistory() {
      const entries = await Promise.all(selectedStudents.map(async (student) => {
        try {
          const response = await apiClient.get('/enrollments/', {
            params: { status: 'all', student: student.id },
          })
          return [String(student.id), normalizeListResponse(response.data).items, '']
        } catch (err) {
          return [String(student.id), [], getApiErrorMessage(err)]
        }
      }))

      if (!active) return
      setPriorEnrollmentHistory(Object.fromEntries(entries.map(([id, records]) => [id, records])))
      setHistoryLoadErrors(Object.fromEntries(entries.filter(([, , message]) => message).map(([id, , message]) => [id, message])))
      setHistoryLoading(false)
    }

    loadPriorEnrollmentHistory()
    return () => { active = false }
  }, [currentStep, enrollmentType, selectedStudents])

  if (loading) {
    return (
      <div className="page-stack">
        <PageHeader eyebrow="Enrollment management" title="Enrollment wizard" description="Loading school-year and student data..." />
        <div className="panel-card record-panel">
          <p>Loading enrollment data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Enrollment management"
        title="Enrollment wizard"
        description="Register a student into a class section. This workflow is separate from Student Registration."
      />

      {error ? <ErrorBanner message={error} /> : null}
      {selectedYear ? (
        <div className="status-banner status-banner--info">New enrollments will use the active academic year: {selectedYear.name}.</div>
      ) : (
        <div className="status-banner status-banner--warning">
          {activeYears.length === 0 ? 'No active academic year is configured. ' : 'More than one active academic year is configured. '}
          Ask an administrator to configure <Link to="/academic-years">Academic Year Management</Link> before enrolling students.
        </div>
      )}

      <div className="panel-card record-panel enrollment-wizard-panel">
        <div className="section-header" style={{ marginBottom: '1.25rem' }}>
          <div>
            <p className="eyebrow">Enrollment process</p>
            <h2>Complete the enrollment steps</h2>
          </div>
        </div>

        <div className="enrollment-steps">
          {enrollmentSteps.map((step, index) => {
            const isActive = index === currentStep
            const isComplete = index < currentStep
            return (
              <div
                key={step}
                className={`enrollment-step${isActive ? ' enrollment-step--active' : ''}${isComplete ? ' enrollment-step--complete' : ''}`}
              >
                {index + 1}. {step}
              </div>
            )
          })}
        </div>

        {wizardError ? <ErrorBanner message={wizardError} /> : null}
        {successMessage ? <div className="status-banner status-banner--success">{successMessage}</div> : null}

        {currentStep === 0 && (
          <div>
            <p className="eyebrow">Step 1 of 6</p>
            <h3>Choose enrollment type and educational level</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {enrollmentTypes.map((type) => {
                const selected = enrollmentType === type
                return (
                  <button
                    key={type}
                    type="button"
                    className={`enrollment-option${selected ? ' enrollment-option--selected' : ''}`}
                    aria-pressed={selected}
                    onClick={() => handleEnrollmentTypeChange(type)}
                  >
                    <div style={{ fontWeight: 700 }}>{type}</div>
                  </button>
                )
              })}
            </div>
            {enrollmentType === 'Transferee' ? (
              <div className="status-banner status-banner--info" style={{ marginTop: '1rem' }}>
                Transfer status and previous-school details are not stored in EDU ASSIST. Existing records cannot be reliably classified as transferees, so verify the student's transfer status manually before enrollment.
              </div>
            ) : null}
            {enrollmentType === 'New Student' ? (
              <div className="status-banner status-banner--info" style={{ marginTop: '1rem' }}>
                Search for an existing profile first. If no match is found, register the student and then return here to select that profile.
              </div>
            ) : null}
            {enrollmentType === 'Returning Student' ? (
              <div className="status-banner status-banner--info" style={{ marginTop: '1rem' }}>
                Select the existing student and review their recorded enrollment history before confirming grade placement.
              </div>
            ) : null}
            <h3 style={{ marginTop: '1.25rem' }}>Choose educational level</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {educationLevels.map((level) => {
                const selected = selectedLevel === level.value
                return (
                  <button
                    key={level.value}
                    type="button"
                    className={`enrollment-option${selected ? ' enrollment-option--selected' : ''}`}
                    onClick={() => {
                      setSelectedLevel(level.value)
                      setSelectedGradeId('')
                      setSelectedStrandId('')
                      setStudentStrandSelections({})
                      setSelectedSectionId('')
                      setSelectedStudentIds([])
                      setCompletedStudentIds([])
                      setEnrollmentResult(null)
                      setSectionSearch('')
                      setStudentSearch('')
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{level.label}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{level.value}</div>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <p className="eyebrow">Step 2 of 6</p>
            <h3>Choose grade level</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {filteredLevels.length === 0 ? (
                <div className="status-banner status-banner--warning">No grade levels are available for the selected educational level.</div>
              ) : (
                filteredLevels.map((grade) => (
                  <button
                    key={grade.id}
                    type="button"
                    className={`enrollment-option${String(grade.id) === String(selectedGradeId) ? ' enrollment-option--selected' : ''}`}
                    onClick={() => {
                      setSelectedGradeId(String(grade.id))
                      setSelectedStrandId('')
                      setStudentStrandSelections({})
                      setSelectedSectionId('')
                      setSelectedStudentIds([])
                      setCompletedStudentIds([])
                      setEnrollmentResult(null)
                      setSectionSearch('')
                      setStudentSearch('')
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{grade.name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{grade.school_level}</div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div>
            <p className="eyebrow">Step 3 of 6</p>
            <h3>Select strand</h3>
            {selectedGrade && requiresStrand ? (
              <>
                <p className="small-muted">Choose a default strand. On Review, you can assign different strands to individual students when using a shared section.</p>
                <div className="form-grid" style={{ marginTop: '1rem' }}>
                  {strands.filter((strand) => strand.is_active !== false).map((strand) => {
                    const strandValue = String(strand.id)
                    const selected = String(selectedStrandId) === strandValue
                    return (
                      <button
                        key={strand.id}
                        type="button"
                        className={`enrollment-option${selected ? ' enrollment-option--selected' : ''}`}
                        onClick={() => {
                          setSelectedStrandId(strandValue)
                          if (selectedSection?.strand && String(selectedSection.strand) !== strandValue) {
                            setSelectedSectionId('')
                            setStudentStrandSelections({})
                          }
                        }}
                      >
                        <div style={{ fontWeight: 700 }}>{strand.name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>Active strand</div>
                      </button>
                    )
                  })}
                </div>
              </>
            ) : (
              <div className="status-banner status-banner--info" style={{ marginTop: '1rem' }}>
                A strand is required for Senior High School enrollments. This selection is skipped automatically for lower school levels.
              </div>
            )}
          </div>
        )}

        {currentStep === 3 && (
          <div>
            <p className="eyebrow">Step 4 of 6</p>
            <h3>Choose a section</h3>
            <label style={{ display: 'block', marginBottom: '1rem' }}>
              <span>Search sections</span>
              <input
                value={sectionSearch}
                onChange={(event) => setSectionSearch(event.target.value)}
                placeholder="Search by section, adviser, or description"
                style={{ width: '100%', marginTop: '0.35rem' }}
              />
            </label>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {sectionOptions.length === 0 ? (
                <div className="status-banner status-banner--warning">
                  No sections are available for the active academic year and grade. Choose another grade.
                </div>
              ) : (
                sectionOptions.map((section) => {
                  const currentCount = enrollments.filter(
                    (entry) => String(entry.section) === String(section.id) && String(entry.enrollment_status || 'active') === 'active',
                  ).length
                  const capacityGuideline = Number(section.capacity) || 0
                  const spacesBelowGuideline = capacityGuideline - currentCount
                  const selected = String(section.id) === String(selectedSectionId)
                  return (
                    <button
                      key={section.id}
                      type="button"
                      className={`enrollment-option${selected ? ' enrollment-option--selected' : ''}`}
                      onClick={() => {
                        setSelectedSectionId(String(section.id))
                        setStudentStrandSelections({})
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong style={{ fontSize: '1rem' }}>{section.name}</strong>
                        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-primary)', background: 'var(--color-surface-muted)', padding: '0.25rem 0.5rem', borderRadius: '999px' }}>
                          {capacityGuideline <= 0
                            ? 'No capacity guideline set'
                            : spacesBelowGuideline > 0
                              ? `Planning reference: ${spacesBelowGuideline} ${spacesBelowGuideline === 1 ? 'space' : 'spaces'} below guideline`
                              : spacesBelowGuideline === 0
                                ? 'Guideline reached'
                                : 'Guideline exceeded'}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '0.25rem' }}>
                        Adviser: {section.adviser_name || 'Not assigned'}
                      </div>
                      {requiresStrand ? (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginBottom: '0.25rem' }}>
                          Section strand: {section.strand_name || 'Shared across strands'}
                        </div>
                      ) : null}
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span>Capacity guideline: {capacityGuideline} students</span>
                        <span>Current enrollment: {currentCount} students</span>
                      </div>
                      {capacityGuideline > 0 && spacesBelowGuideline === 0 ? (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '0.35rem' }}>
                          Current enrollment has reached the suggested capacity. Enrollment may continue according to school policy.
                        </div>
                      ) : null}
                      {capacityGuideline > 0 && spacesBelowGuideline < 0 ? (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: '0.35rem' }}>
                          Current enrollment is above the suggested capacity. Review staffing and classroom arrangements as needed.
                        </div>
                      ) : null}
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="enrollment-student-step">
            <p className="eyebrow">Step 5 of 6</p>
            <h3>Choose a student</h3>
            <label className="enrollment-student-search">
              <span>Search by LRN or name</span>
              <span className="enrollment-student-search__field">
                <MagnifyingGlassIcon aria-hidden="true" />
                <input
                  value={studentSearch}
                  onChange={(event) => setStudentSearch(event.target.value)}
                  placeholder="Search by student name or LRN"
                  aria-label="Search by student name or LRN"
                />
              </span>
            </label>

            <div className="enrollment-selection-toolbar" aria-label="Student selection controls">
              <div className="enrollment-selection-toolbar__summary" aria-live="polite">
                <strong>
                  {selectedStudentIds.length} student{selectedStudentIds.length === 1 ? '' : 's'} selected
                </strong>
                <span>
                  {visibleStudentIds.length} displayed · {allVisibleStudentsSelected
                    ? 'all displayed students selected'
                    : `${visibleSelectedCount} of ${visibleStudentIds.length} displayed students selected`}
                </span>
              </div>
              <div className="enrollment-selection-toolbar__actions">
                <label className="enrollment-select-all">
                  <input
                    ref={selectAllStudentsRef}
                    type="checkbox"
                    checked={allVisibleStudentsSelected}
                    disabled={studentSearchLoading ||
                      Boolean(studentSearchError) ||
                      visibleStudentIds.length === 0 ||
                      enrollmentType === 'Transferee'}
                    onChange={() => {
                      setSelectedStudentIds((current) => {
                        const currentIds = new Set(current.map(String))
                        if (allVisibleStudentsSelected) {
                          return current.filter((id) => !visibleStudentIds.includes(String(id)))
                        }
                        visibleStudentIds.forEach((id) => currentIds.add(id))
                        return [...currentIds]
                      })
                      setEnrollmentResult(null)
                      setWizardError('')
                    }}
                  />
                  <span>{enrollmentType === 'Transferee' ? 'Select all unavailable' : 'Select all displayed students'}</span>
                </label>
                <button
                  type="button"
                  className="action-button action-button--neutral"
                  onClick={() => {
                    setSelectedStudentIds([])
                    setCompletedStudentIds([])
                    setEnrollmentResult(null)
                    setSuccessMessage('')
                    setWizardError('')
                  }}
                  disabled={selectedStudentIds.length === 0}
                >
                  Clear selection
                </button>
              </div>
            </div>
            {selectionResetNotice ? (
              <div className="enrollment-hidden-selection" role="status">
                {selectionResetNotice}
              </div>
            ) : null}
            {enrollmentType === 'Transferee' ? (
              <div className="enrollment-hidden-selection" role="note">
                EDU ASSIST has no stored transferee classification. Search existing profiles and manually verify transfer status; select students individually. Do not use Select All for unverified candidates.
              </div>
            ) : null}
            {['Continuing Student', 'Returning Student'].includes(enrollmentType) ? (
              <div className="enrollment-history-guidance" role="note">
                {enrollmentType === 'Continuing Student' ? (
                  precedingAcademicYear ? (
                    <>Candidates have an enrollment in the immediately preceding configured academic year ({precedingAcademicYear.name}). Review the previous grade shown on each card and confirm placement; the system does not automatically promote students.</>
                  ) : (
                    <>The immediately preceding academic year cannot be identified reliably from the configured dates. Ask an administrator to review Academic Year Management; continuing-student eligibility is unavailable until the year sequence is clear.</>
                  )
                ) : (
                  <>Candidates have an enrollment before the immediately preceding configured academic year and none in that year. This is a recorded enrollment gap only; the reason is unknown. Review the history and confirm classification and placement. The system does not automatically promote students.</>
                )}
              </div>
            ) : null}
            {enrollmentType === 'New Student' ? (
              <div className="enrollment-history-guidance" role="note">
                These are active profiles with no enrollment history recorded in EDU ASSIST. This does not establish that a student is new to the school; confirm the classification before enrollment.
              </div>
            ) : null}
            {hiddenSelectedCount > 0 ? (
              <div className="enrollment-hidden-selection" role="status">
                {hiddenSelectedCount} selected student{hiddenSelectedCount === 1 ? ' is' : 's are'} hidden by your search or current filters. Selection is retained and will be listed on Review.
              </div>
            ) : null}

            <div className="enrollment-student-grid">
              {studentSearchLoading || !searchResultsCurrent ? (
                <div className="enrollment-student-grid__message">Searching student records...</div>
              ) : studentSearchError ? (
                <div className="enrollment-student-grid__message">
                  <ErrorBanner message={`Unable to search student records: ${studentSearchError}`} />
                </div>
              ) : availableStudents.length === 0 ? (
                <div className="enrollment-student-grid__message enrollment-student-grid__message--empty">
                  No eligible students match this search. Students already enrolled in the active school year are hidden.
                </div>
              ) : (
                availableStudents.map((student) => {
                  const selected = selectedStudentIdSet.has(String(student.id))
                  return (
                    <label
                      key={student.id}
                      className={`enrollment-student-card${selected ? ' enrollment-student-card--selected' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => {
                          setSelectedStudentIds((current) => selected
                            ? current.filter((id) => String(id) !== String(student.id))
                            : [...current, String(student.id)])
                          setEnrollmentResult(null)
                          setWizardError('')
                        }}
                      />
                      <span className="enrollment-student-card__details">
                        <span className="enrollment-student-card__name">{student.first_name || ''} {student.last_name || ''}</span>
                        <span className="enrollment-student-card__lrn">LRN: {student.lrn || '—'}</span>
                        {student.current_enrollment?.grade_level ? (
                          <span className="enrollment-student-card__history">
                            Previous: {student.current_enrollment.grade_level}
                            {student.current_enrollment.academic_year ? ` · ${student.current_enrollment.academic_year}` : ''}
                          </span>
                        ) : null}
                      </span>
                    </label>
                  )
                })
              )}
            </div>
            {!studentSearchLoading &&
            searchResultsCurrent &&
            !studentSearchError &&
            searchedStudentIds.length === 0 &&
            ['Transferee', 'New Student'].includes(enrollmentType) ? (
              <div style={{ marginTop: '1rem' }}>
                <Link
                  className="action-button action-button--primary"
                  to="/students"
                  state={{ openRegisterModal: true }}
                >
                  Go to Student Registration
                </Link>
              </div>
            ) : null}
          </div>
        )}

        {currentStep === 5 && (
          <div>
            <p className="eyebrow">Step 6 of 6</p>
            <h3>Review summary</h3>
            <div className="detail-card" style={{ marginTop: '1rem', padding: '1.25rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div>
                  <strong>Student{reviewSummary.students.length === 1 ? '' : 's'}</strong>
                  {reviewSummary.students.length ? (
                    <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.25rem' }}>
                      {reviewSummary.students.map((student) => (
                        <li key={student.id}>{student.first_name || ''} {student.last_name || ''}</li>
                      ))}
                    </ul>
                  ) : <div>Not selected</div>}
                </div>
                <div><strong>Enrollment Type</strong><div>{enrollmentType || 'Not selected'}</div></div>
                <div><strong>School Year</strong><div>{reviewSummary.schoolYear}</div></div>
                <div><strong>Grade</strong><div>{reviewSummary.grade}</div></div>
                <div><strong>Enrollment Destination</strong><div>{reviewSummary.grade} · {reviewSummary.section}</div></div>
                <div><strong>Section</strong><div>{reviewSummary.section}</div></div>
                <div><strong>Default strand</strong><div>{reviewSummary.strand}</div></div>
                <div><strong>Adviser</strong><div>{reviewSummary.adviser}</div></div>
              </div>
            </div>
            {requiresStrand && reviewSummary.students.length > 0 ? (
              <div className="detail-card" style={{ marginTop: '0.75rem', padding: '1.25rem' }}>
                <strong>Student strand assignments</strong>
                <p className="small-muted">Each student’s strand is saved on their enrollment. Shared sections can include students from different strands.</p>
                <div className="form-grid">
                  {reviewSummary.students.map((student) => {
                    const studentId = String(student.id)
                    const strandOptions = strands.filter((strand) =>
                      strand.is_active !== false &&
                      (!selectedSection?.strand || String(strand.id) === String(selectedSection.strand)),
                    )
                    return (
                      <label key={student.id}>
                        <span>{student.first_name || ''} {student.last_name || ''}</span>
                        <select
                          value={studentStrandSelections[studentId] ?? selectedStrandId}
                          onChange={(event) => setStudentStrandSelections((current) => ({
                            ...current,
                            [studentId]: event.target.value,
                          }))}
                        >
                          <option value="">Select strand</option>
                          {strandOptions.map((strand) => (
                            <option key={strand.id} value={String(strand.id)}>{strand.name}</option>
                          ))}
                        </select>
                      </label>
                    )
                  })}
                </div>
              </div>
            ) : null}
            <div className="status-banner status-banner--info" style={{ marginTop: '0.75rem' }}>
              Enrollment type guides this workflow but is not saved on enrollment records because the current data model has no enrollment-type field.
            </div>
            {enrollmentType === 'Returning Student' ? (
              <div className="detail-card" style={{ marginTop: '1rem', padding: '1.25rem' }}>
                <strong>Prior enrollment history</strong>
                {historyLoading ? <div style={{ marginTop: '0.5rem' }}>Loading recorded enrollment history...</div> : null}
                {reviewSummary.students.length ? reviewSummary.students.map((student) => {
                  const history = priorEnrollmentHistory[String(student.id)]
                    ?? studentEnrollmentHistory.get(String(student.id))
                    ?? []
                  const latestEnrollment = student.current_enrollment
                  const displayedHistory = latestEnrollment && !history.some((entry) => String(entry.id) === String(latestEnrollment.id))
                    ? [...history, {
                      ...latestEnrollment,
                      academic_year_name: latestEnrollment.academic_year,
                      grade_level_name: latestEnrollment.grade_level,
                      section_name: latestEnrollment.section,
                    }]
                    : history
                  return (
                    <div key={student.id} style={{ marginTop: '0.75rem' }}>
                      <strong>{student.first_name || ''} {student.last_name || ''}</strong>
                      {historyLoadErrors[String(student.id)] ? (
                        <div className="status-banner status-banner--warning" role="alert" style={{ marginTop: '0.35rem' }}>
                          Enrollment history could not be loaded: {historyLoadErrors[String(student.id)]}
                        </div>
                      ) : null}
                      {displayedHistory.length ? (
                        <ul style={{ margin: '0.25rem 0 0', paddingLeft: '1.25rem' }}>
                          {displayedHistory.map((entry, index) => (
                            <li key={entry.id || `${entry.academic_year_name}-${index}`}>
                              {entry.academic_year_name || 'Academic year not recorded'} · {entry.grade_level_name || 'Grade not recorded'} · {entry.section_name || 'Section not recorded'}{entry.strand_name ? ` · ${entry.strand_name}` : ''}
                            </li>
                          ))}
                        </ul>
                      ) : <div>No prior enrollment history is available.</div>}
                    </div>
                  )
                }) : <div style={{ marginTop: '0.5rem' }}>Select a student to review recorded enrollment history.</div>}
              </div>
            ) : null}
            {enrollmentResult?.failures.length ? (
              <div className="status-banner status-banner--warning" role="alert" style={{ marginTop: '1rem' }}>
                <strong>Some students were not enrolled. Review each item and correct it before retrying:</strong>
                <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem' }}>
                  {enrollmentResult.failures.map((failure) => (
                    <li key={failure.id}>{failure.name}: {failure.reason}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div style={{ marginTop: '1.5rem' }}>
              <button
                type="button"
                className="action-button action-button--primary"
                onClick={handleEnroll}
                disabled={submitting || !selectedYear || selectedStudentIds.every((id) => completedStudentIds.map(String).includes(String(id)))}
                style={{ width: '100%', fontSize: '1.1rem', padding: '1rem 1.25rem' }}
              >
                {submitting ? 'Completing Enrollment...' : 'Complete Enrollment'}
              </button>
              {successMessage && !enrollmentResult?.failures.length ? <button type="button" className="action-button action-button--neutral" onClick={resetWizard} style={{ width: '100%', marginTop: '0.75rem' }}>Start New Enrollment</button> : null}
            </div>
          </div>
        )}

        {currentStep < enrollmentSteps.length - 1 && (
          <div className="enrollment-wizard-navigation">
            <button
              type="button"
              className="action-button action-button--neutral"
              onClick={requestWizardRestart}
              disabled={!hasWizardProgress}
            >
              Restart
            </button>

            <div className="enrollment-wizard-navigation__actions">
              <button
                type="button"
                className="action-button action-button--neutral"
                onClick={handlePrevious}
                disabled={currentStep === 0}
              >
                Back
              </button>

              <button
                type="button"
                className="action-button action-button--primary"
                onClick={handleNext}
                disabled={!selectedYear || (currentStep === 4 && selectedStudentIds.length === 0)}
              >
                {currentStep === 4 ? 'Next: Review' : 'Next'}
              </button>
            </div>
          </div>
        )}
      </div>
      <ConfirmDialog
        open={restartConfirmationOpen}
        title="Restart enrollment wizard?"
        message="Restarting will discard your current enrollment selections and wizard progress."
        confirmLabel="Restart wizard"
        cancelLabel="Continue enrollment"
        onConfirm={resetWizard}
        onCancel={() => setRestartConfirmationOpen(false)}
      />
    </div>
  )
}

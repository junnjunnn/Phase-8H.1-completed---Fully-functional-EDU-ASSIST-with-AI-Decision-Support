import { useEffect, useMemo, useState } from 'react'
import { ErrorBanner } from '../../components/feedback/ErrorBanner'
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
  'School Year',
  'Educational Level',
  'Grade Level',
  'Strand',
  'Section',
  'Student',
  'Review',
]

const educationLevels = [
  { value: 'Elementary', label: 'Elementary' },
  { value: 'Junior High School', label: 'Junior High' },
  { value: 'Senior High School', label: 'Senior High' },
]

const supportedStrands = ['STEM', 'ABM', 'HUMSS', 'GAS', 'TVL ICT', 'TVL HE']

function gradeRequiresStrand(gradeName = '') {
  return /Grade\s*(11|12)/i.test(String(gradeName))
}

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
  const [selectedYearId, setSelectedYearId] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('')
  const [selectedGradeId, setSelectedGradeId] = useState('')
  const [selectedStrandId, setSelectedStrandId] = useState('')
  const [selectedSectionId, setSelectedSectionId] = useState('')
  const [selectedStudentId, setSelectedStudentId] = useState('')
  const [studentSearch, setStudentSearch] = useState('')
  const [sectionSearch, setSectionSearch] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    let active = true

    async function loadData() {
      setLoading(true)
      setError('')
      try {
        const [enrollmentData, studentData, yearData, gradeData, sectionData, strandData] = await Promise.all([
          apiClient.get('/enrollments/'),
          getStudents(),
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
        setStudents(normalizeListResponse(studentData).items || [])
        setAcademicYears(yearList)
        setGradeLevels(gradeList)
        setSections(sectionList)
        setStrands(strandList)

        const activeYear = yearList.find((year) => year.is_active) || yearList[0]
        if (activeYear) {
          setSelectedYearId(String(activeYear.id))
        }
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

  const activeYears = useMemo(() => academicYears.filter((year) => year.is_active), [academicYears])

  const selectedYear = useMemo(
    () => academicYears.find((year) => String(year.id) === String(selectedYearId)) || null,
    [academicYears, selectedYearId],
  )

  const selectedGrade = useMemo(
    () => gradeLevels.find((grade) => String(grade.id) === String(selectedGradeId)) || null,
    [gradeLevels, selectedGradeId],
  )

  const selectedSection = useMemo(
    () => sections.find((section) => String(section.id) === String(selectedSectionId)) || null,
    [sections, selectedSectionId],
  )

  const selectedStudent = useMemo(
    () => students.find((student) => String(student.id) === String(selectedStudentId)) || null,
    [students, selectedStudentId],
  )

  const selectedStrand = useMemo(
    () => strands.find((strand) => String(strand.id) === String(selectedStrandId)) || null,
    [strands, selectedStrandId],
  )

  const filteredLevels = useMemo(
    () => gradeLevels.filter((grade) => !selectedLevel || grade.school_level === selectedLevel),
    [gradeLevels, selectedLevel],
  )

  const requiresStrand = Boolean(selectedGrade && gradeRequiresStrand(selectedGrade.name))

  const sectionOptions = useMemo(() => {
    const query = sectionSearch.trim().toLowerCase()
    return sections.filter((section) => {
      const matchesYear = String(section.academic_year) === String(selectedYearId)
      const matchesGrade = String(section.grade_level) === String(selectedGradeId)
      const matchesStrand = !requiresStrand || String(section.strand) === String(selectedStrandId)
      const matchesQuery = !query || `${section.name || ''} ${section.adviser_name || ''} ${section.description || ''}`.toLowerCase().includes(query)
      return matchesYear && matchesGrade && matchesStrand && matchesQuery
    })
  }, [sections, selectedYearId, selectedGradeId, selectedStrandId, sectionSearch, requiresStrand, enrollments])

  const availableStudents = useMemo(() => {
    const query = studentSearch.trim().toLowerCase()
    const blockedStudentIds = new Set(
      enrollments
        .filter((entry) => {
          const sameYear = String(entry.academic_year) === String(selectedYearId)
          const isActive = String(entry.enrollment_status || 'active') === 'active'
          return sameYear && isActive
        })
        .map((entry) => Number(entry.student)),
    )

    return students.filter((student) => {
      if (blockedStudentIds.has(Number(student.id))) {
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
  }, [enrollments, selectedYearId, studentSearch, students])

  function resetWizard() {
    const activeYear = activeYears[0]
    setCurrentStep(0)
    setSelectedYearId(activeYear ? String(activeYear.id) : '')
    setSelectedLevel('')
    setSelectedGradeId('')
    setSelectedStrandId('')
    setSelectedSectionId('')
    setSelectedStudentId('')
    setStudentSearch('')
    setSectionSearch('')
    setWizardError('')
    setSuccessMessage('')
  }

  function validateCurrentStep() {
    if (currentStep === 0) {
      if (!selectedYearId) {
        setWizardError('Select the current school year to continue.')
        return false
      }
      if (selectedYear && !selectedYear.is_active) {
        setWizardError('Only the active school year can be used for new enrollment.')
        return false
      }
      return true
    }

    if (currentStep === 1) {
      if (!selectedLevel) {
        setWizardError('Choose an educational level before continuing.')
        return false
      }
      return true
    }

    if (currentStep === 2) {
      if (!selectedGradeId) {
        setWizardError('Choose a grade level before continuing.')
        return false
      }
      return true
    }

    if (currentStep === 3) {
      if (!requiresStrand) {
        return true
      }
      if (!selectedStrandId) {
        setWizardError('Select a strand for Grade 11 or Grade 12.')
        return false
      }
      return true
    }

    if (currentStep === 4) {
      if (!selectedSectionId) {
        setWizardError('Select a section to continue.')
        return false
      }
      return true
    }

    if (currentStep === 5) {
      if (!selectedStudentId) {
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

  async function handleNext() {
    if (!validateCurrentStep()) {
      return
    }

    let nextStep = currentStep + 1
    if (currentStep === 2 && !requiresStrand) {
      nextStep += 1
    }

    setWizardError('')
    setCurrentStep(Math.min(nextStep, enrollmentSteps.length - 1))
  }

  async function handleEnroll() {
    if (!selectedYearId || !selectedGradeId || !selectedSectionId || !selectedStudentId) {
      setWizardError('Complete the enrollment wizard before submitting.')
      return
    }

    if (selectedYear && !selectedYear.is_active) {
      setWizardError('Archived school years cannot be used for a new enrollment.')
      return
    }

    const alreadyEnrolled = enrollments.some((entry) => {
      const sameStudent = String(entry.student) === String(selectedStudentId)
      const sameYear = String(entry.academic_year) === String(selectedYearId)
      const isActive = String(entry.enrollment_status || 'active') === 'active'
      return sameStudent && sameYear && isActive
    })

    if (alreadyEnrolled) {
      setWizardError('This student is already enrolled in the selected school year.')
      return
    }

    try {
      setSubmitting(true)
      setWizardError('')
      await createEnrollment({
        student: Number(selectedStudentId),
        academic_year: Number(selectedYearId),
        grade_level: Number(selectedGradeId),
        section: Number(selectedSectionId),
        strand: selectedStrandId ? Number(selectedStrandId) : null,
        enrollment_status: 'active',
        enrollment_date: new Date().toISOString().slice(0, 10),
      })

      const refreshed = await apiClient.get('/enrollments/')
      setEnrollments(normalizeListResponse(refreshed.data).items)
      setSuccessMessage('Student enrolled successfully. The enrollment has been added to the selected section.')
      setCurrentStep(enrollmentSteps.length - 1)
    } catch (err) {
      setWizardError(getApiErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  const reviewSummary = useMemo(() => ({
    student: selectedStudent ? `${selectedStudent.first_name || ''} ${selectedStudent.last_name || ''}`.trim() : 'Not selected',
    schoolYear: selectedYear?.name || 'Not selected',
    grade: selectedGrade?.name || 'Not selected',
    strand: selectedStrand?.name || 'Not applicable',
    section: selectedSection ? `${selectedSection.name}` : 'Not selected',
    adviser: selectedSection?.adviser_name || selectedSection?.adviser || 'Not assigned',
  }), [selectedSection, selectedStrand, selectedStudent, selectedYear, selectedGrade])

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

      <div className="panel-card record-panel">
        <div className="section-header" style={{ marginBottom: '1.25rem' }}>
          <div>
            <p className="eyebrow">Enrollment process</p>
            <h2>Complete the enrollment steps</h2>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          {enrollmentSteps.map((step, index) => {
            const isActive = index === currentStep
            const isComplete = index < currentStep
            return (
              <div
                key={step}
                style={{
                  flex: '1 1 120px',
                  minWidth: '120px',
                  padding: '0.7rem 0.9rem',
                  borderRadius: '12px',
                  border: `1px solid ${isActive ? '#1d4ed8' : isComplete ? '#16a34a' : '#dfe3ee'}`,
                  background: isActive ? '#eff6ff' : isComplete ? '#f0fdf4' : '#ffffff',
                  color: isActive ? '#1d4ed8' : '#374151',
                  fontWeight: isActive ? 700 : 500,
                  textAlign: 'center',
                  fontSize: '0.86rem',
                }}
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
            <p className="eyebrow">Step 1 of 7</p>
            <h3>Choose the current school year</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {activeYears.length === 0 ? (
                <div className="status-banner status-banner--warning">No active school year is available for enrollment.</div>
              ) : (
                activeYears.map((year) => {
                  const isSelected = String(year.id) === String(selectedYearId)
                  return (
                    <button
                      key={year.id}
                      type="button"
                      onClick={() => {
                        setSelectedYearId(String(year.id))
                        setSelectedGradeId('')
                        setSelectedLevel('')
                        setSelectedStrandId('')
                        setSelectedSectionId('')
                        setSelectedStudentId('')
                        setSectionSearch('')
                        setStudentSearch('')
                      }}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        border: isSelected ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                        background: isSelected ? '#eff6ff' : '#fff',
                        textAlign: 'left',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>{year.name}</div>
                      <div style={{ fontSize: '0.8rem', color: '#374151' }}>Current school year</div>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div>
            <p className="eyebrow">Step 2 of 7</p>
            <h3>Choose educational level</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {educationLevels.map((level) => {
                const selected = selectedLevel === level.value
                return (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => {
                      setSelectedLevel(level.value)
                      setSelectedGradeId('')
                      setSelectedStrandId('')
                      setSelectedSectionId('')
                      setSelectedStudentId('')
                      setSectionSearch('')
                      setStudentSearch('')
                    }}
                    style={{
                      padding: '1rem',
                      borderRadius: '12px',
                      border: selected ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                      background: selected ? '#eff6ff' : '#fff',
                      textAlign: 'left',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{level.label}</div>
                    <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{level.value}</div>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div>
            <p className="eyebrow">Step 3 of 7</p>
            <h3>Choose grade level</h3>
            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {filteredLevels.length === 0 ? (
                <div className="status-banner status-banner--warning">No grade levels are available for the selected educational level.</div>
              ) : (
                filteredLevels.map((grade) => (
                  <button
                    key={grade.id}
                    type="button"
                    onClick={() => {
                      setSelectedGradeId(String(grade.id))
                      setSelectedStrandId('')
                      setSelectedSectionId('')
                      setSelectedStudentId('')
                      setSectionSearch('')
                      setStudentSearch('')
                    }}
                    style={{
                      padding: '1rem',
                      borderRadius: '12px',
                      border: String(grade.id) === String(selectedGradeId) ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                      background: String(grade.id) === String(selectedGradeId) ? '#eff6ff' : '#fff',
                      textAlign: 'left',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{grade.name}</div>
                    <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{grade.school_level}</div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div>
            <p className="eyebrow">Step 4 of 7</p>
            <h3>Select strand</h3>
            {selectedGrade && requiresStrand ? (
              <div className="form-grid" style={{ marginTop: '1rem' }}>
                {supportedStrands.map((name) => {
                  const match = strands.find((strand) => strand.name === name)
                  const strandValue = match ? String(match.id) : ''
                  const selected = String(selectedStrandId) === strandValue
                  return (
                    <button
                      key={name}
                      type="button"
                      onClick={() => setSelectedStrandId(strandValue)}
                      disabled={!match}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        border: selected ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                        background: selected ? '#eff6ff' : '#fff',
                        textAlign: 'left',
                        cursor: match ? 'pointer' : 'not-allowed',
                        opacity: match ? 1 : 0.6,
                      }}
                    >
                      <div style={{ fontWeight: 700 }}>{name}</div>
                      <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{match ? 'Available strand' : 'Not configured'}</div>
                    </button>
                  )
                })}
              </div>
            ) : (
              <div className="status-banner status-banner--info" style={{ marginTop: '1rem' }}>
                Strand is required only for Grade 11 and Grade 12 students. This selection is skipped automatically for lower grades.
              </div>
            )}
          </div>
        )}

        {currentStep === 4 && (
          <div>
            <p className="eyebrow">Step 5 of 7</p>
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
                  No sections are available for the selected year and grade. Adjust the filters or choose another grade.
                </div>
              ) : (
                sectionOptions.map((section) => {
                  const currentCount = enrollments.filter(
                    (entry) => String(entry.section) === String(section.id) && String(entry.enrollment_status || 'active') === 'active',
                  ).length
                  const availableSlots = Math.max((Number(section.capacity) || 0) - currentCount, 0)
                  const selected = String(section.id) === String(selectedSectionId)
                  return (
                    <button
                      key={section.id}
                      type="button"
                      onClick={() => setSelectedSectionId(String(section.id))}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        border: selected ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                        background: selected ? '#eff6ff' : '#fff',
                        textAlign: 'left',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong style={{ fontSize: '1rem' }}>{section.name}</strong>
                        <span style={{ fontSize: '0.8rem', color: '#1f2937', background: '#f3f4f6', padding: '0.25rem 0.5rem', borderRadius: '999px' }}>
                          {availableSlots} slots left
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#374151', marginBottom: '0.25rem' }}>
                        Adviser: {section.adviser_name || 'Not assigned'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#374151', display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span>Capacity: {section.capacity || 0}</span>
                        <span>Current enrollees: {currentCount}</span>
                      </div>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}

        {currentStep === 5 && (
          <div>
            <p className="eyebrow">Step 6 of 7</p>
            <h3>Choose a student</h3>
            <label style={{ display: 'block', marginBottom: '1rem' }}>
              <span>Search by LRN or name</span>
              <input
                value={studentSearch}
                onChange={(event) => setStudentSearch(event.target.value)}
                placeholder="Search by LRN, first name, or last name"
                style={{ width: '100%', marginTop: '0.35rem' }}
              />
            </label>

            <div className="form-grid" style={{ marginTop: '1rem' }}>
              {availableStudents.length === 0 ? (
                <div className="status-banner status-banner--warning">
                  No eligible students match this search. Students already enrolled in the selected school year are hidden.
                </div>
              ) : (
                availableStudents.map((student) => {
                  const selected = String(student.id) === String(selectedStudentId)
                  return (
                    <button
                      key={student.id}
                      type="button"
                      onClick={() => setSelectedStudentId(String(student.id))}
                      style={{
                        padding: '1rem',
                        borderRadius: '12px',
                        border: selected ? '2px solid #1d4ed8' : '1px solid #dfe3ee',
                        background: selected ? '#eff6ff' : '#fff',
                        textAlign: 'left',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontWeight: 700 }}>{student.first_name || ''} {student.last_name || ''}</div>
                      <div style={{ fontSize: '0.8rem', color: '#374151' }}>LRN: {student.lrn || '—'}</div>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}

        {currentStep === 6 && (
          <div>
            <p className="eyebrow">Step 7 of 7</p>
            <h3>Review summary</h3>
            <div className="detail-card" style={{ marginTop: '1rem', padding: '1.25rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                <div><strong>Student</strong><div>{reviewSummary.student}</div></div>
                <div><strong>School Year</strong><div>{reviewSummary.schoolYear}</div></div>
                <div><strong>Grade</strong><div>{reviewSummary.grade}</div></div>
                <div><strong>Section</strong><div>{reviewSummary.section}</div></div>
                <div><strong>Strand</strong><div>{reviewSummary.strand}</div></div>
                <div><strong>Adviser</strong><div>{reviewSummary.adviser}</div></div>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <button
                type="button"
                className="action-button action-button--primary"
                onClick={handleEnroll}
                disabled={submitting}
                style={{ width: '100%', fontSize: '1.1rem', padding: '1rem 1.25rem' }}
              >
                {submitting ? 'Completing Enrollment...' : 'Complete Enrollment'}
              </button>
            </div>
          </div>
        )}

        {currentStep < enrollmentSteps.length - 1 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginTop: '1.75rem' }}>
            <button
              type="button"
              className="action-button action-button--neutral"
              onClick={resetWizard}
              disabled={currentStep === 0 && !selectedYearId && !selectedGradeId && !selectedSectionId && !selectedStudentId}
            >
              Restart
            </button>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                type="button"
                className="action-button action-button--neutral"
                onClick={handlePrevious}
                disabled={currentStep === 0}
              >
                Back
              </button>

              <button type="button" className="action-button action-button--primary" onClick={handleNext}>
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


const SUBJECT_DIVISIONS = new Set(['ELEMENTARY', 'JUNIOR_HIGH_SCHOOL', 'SENIOR_HIGH_SCHOOL'])
const SUBJECT_FIELDS = new Set(['name', 'official_subject_code', 'subject_type', 'academic_division', 'grade_level', 'grade_levels', 'category', 'strand', 'is_active'])

export function createEmptySubjectForm(academicDivision = '') {
  return {
    id: '',
    code: '',
    official_subject_code: '',
    name: '',
    subject_type: 'STANDARD',
    category: academicDivision === 'SENIOR_HIGH_SCHOOL' ? 'Core' : 'Learning Area',
    academic_division: academicDivision,
    grade_level: '',
    grade_levels: [],
    strand: '',
    is_active: true,
    initial_academic_division: '',
    initial_grade_levels: [],
    initial_strand: '',
  }
}

export function validateSubjectForm(form, academicDivisions) {
  const errors = {}
  const division = academicDivisions.find((item) => item.value === form.academic_division)
  const gradeSelectionChanged = form.id && (
    form.academic_division !== form.initial_academic_division
    || form.grade_levels.length !== form.initial_grade_levels.length
    || form.grade_levels.some((id) => !form.initial_grade_levels.map(String).includes(String(id)))
  )

  if (!form.name.trim()) errors.name = 'Enter a subject name.'
  if (!form.id || gradeSelectionChanged) {
    if (!form.academic_division || !SUBJECT_DIVISIONS.has(form.academic_division)) {
      errors.academic_division = 'Select Elementary, Junior High School, or Senior High School.'
    } else if (!division?.grade_levels?.length) {
      errors.grade_levels = 'There are no active grade levels for this school category.'
    } else if (!form.grade_levels.length) {
      errors.grade_levels = 'Select at least one applicable grade level.'
    }
  }
  if (!form.category) errors.category = 'Select a subject classification.'

  return errors
}

export function buildSubjectPayload(form) {
  const payload = {
    name: form.name.trim(),
    subject_type: form.subject_type || 'STANDARD',
    category: form.category,
    is_active: form.is_active,
  }
  const gradeSelectionChanged = !form.id || (
    form.academic_division !== form.initial_academic_division
    || form.grade_levels.length !== form.initial_grade_levels.length
    || form.grade_levels.some((id) => !form.initial_grade_levels.map(String).includes(String(id)))
  )

  if (gradeSelectionChanged) {
    payload.academic_division = form.academic_division
    payload.grade_levels = form.grade_levels
    payload.grade_level = form.grade_levels[0] || null
  }
  if (!form.id || form.strand !== form.initial_strand || form.academic_division !== form.initial_academic_division) {
    payload.strand = form.strand || null
  }
  if (
    form.academic_division === 'SENIOR_HIGH_SCHOOL'
    || (form.initial_academic_division === 'SENIOR_HIGH_SCHOOL' && form.academic_division !== form.initial_academic_division)
  ) {
    payload.official_subject_code = form.official_subject_code
  }

  return payload
}

export function getSubjectFieldErrors(error) {
  const data = error?.response?.data
  const fieldErrors = {}
  let hasUnexpectedError = false

  if (data && typeof data === 'object' && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      const message = (Array.isArray(value) ? value : [value])
        .filter((item) => typeof item === 'string')
        .join(' ')
      if (!message) continue
      if (SUBJECT_FIELDS.has(key)) {
        fieldErrors[key === 'grade_level' ? 'grade_levels' : key] = message
      } else {
        hasUnexpectedError = true
      }
    }
  } else if (data) {
    hasUnexpectedError = true
  }

  const formError = hasUnexpectedError || !Object.keys(fieldErrors).length
    ? 'Could not save the subject. Review the fields and try again.'
    : ''

  return { fieldErrors, formError }
}

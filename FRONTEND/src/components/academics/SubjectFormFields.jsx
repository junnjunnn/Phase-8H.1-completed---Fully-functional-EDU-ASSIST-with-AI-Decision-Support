const SUBJECT_TYPE_OPTIONS = [
  { value: 'STANDARD', label: 'Standard curriculum' },
  { value: 'SCHOOL_SPECIFIC', label: 'School-specific' },
]

const SUBJECT_CATEGORIES = {
  'Senior High School': [
    { value: 'Core', label: 'Core' },
    { value: 'Applied', label: 'Applied' },
    { value: 'Specialized', label: 'Specialized' },
    { value: 'Learning Area', label: 'Learning Area' },
  ],
  default: [{ value: 'Learning Area', label: 'Learning Area' }],
}

function FieldError({ id, message }) {
  return message ? <small className="field-error" id={id}>{message}</small> : null
}

export function SubjectFormFields({
  form,
  setForm,
  academicDivisions,
  strands,
  strandLoadStatus = 'loaded',
  errors = {},
  clearErrors = () => {},
}) {
  const selectedDivision = academicDivisions.find((division) => division.value === form.academic_division)
  const availableGrades = selectedDivision?.grade_levels || []
  const availableStrands = strands.filter((strand) => strand.is_active !== false)
  const configuredCategories = SUBJECT_CATEGORIES[selectedDivision?.label] || SUBJECT_CATEGORIES.default
  const categoryOptions = configuredCategories.some((option) => option.value === form.category)
    ? configuredCategories
    : [...configuredCategories, { value: form.category, label: form.category }]

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    clearErrors([field])
  }

  function selectDivision(value) {
    const division = academicDivisions.find((item) => item.value === value)
    setForm((current) => ({
      ...current,
      academic_division: value,
      grade_level: '',
      grade_levels: [],
      category: division?.label === 'Senior High School' ? 'Core' : 'Learning Area',
      strand: '',
      official_subject_code: division?.label === 'Senior High School'
        ? current.official_subject_code
        : '',
    }))
    clearErrors(['academic_division', 'grade_levels', 'category', 'strand', 'official_subject_code'])
  }

  function toggleGrade(grade, checked) {
    setForm((current) => {
      const gradeLevels = checked
        ? [...new Set([...current.grade_levels, grade.id])]
        : current.grade_levels.filter((id) => String(id) !== String(grade.id))
      return {
        ...current,
        grade_level: gradeLevels[0] || '',
        grade_levels: gradeLevels,
      }
    })
    clearErrors(['grade_levels'])
  }

  return (
    <>
      <section className="subject-form-section" aria-labelledby="subject-details-heading">
        <div className="subject-form-section__heading">
          <p className="eyebrow">Subject details</p>
          <h3 id="subject-details-heading">Identity and status</h3>
        </div>
        <div className="subject-form-section__fields">
          <label className="subject-form-field--wide">
            <span>Subject name</span>
            <input
              value={form.name}
              onChange={(event) => updateField('name', event.target.value)}
              required
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? 'subject-name-error' : undefined}
            />
            <FieldError id="subject-name-error" message={errors.name} />
          </label>
          <label>
            <span>Subject type</span>
            <select
              value={form.subject_type || 'STANDARD'}
              onChange={(event) => updateField('subject_type', event.target.value)}
              aria-invalid={Boolean(errors.subject_type)}
              aria-describedby={errors.subject_type ? 'subject-type-error' : undefined}
            >
              {SUBJECT_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <FieldError id="subject-type-error" message={errors.subject_type} />
          </label>
          <label>
            <span>Status</span>
            <select
              value={form.is_active ? 'true' : 'false'}
              onChange={(event) => updateField('is_active', event.target.value === 'true')}
              aria-invalid={Boolean(errors.is_active)}
              aria-describedby={errors.is_active ? 'subject-status-error' : undefined}
            >
              <option value="true">Active</option>
              <option value="false">Archived</option>
            </select>
            <FieldError id="subject-status-error" message={errors.is_active} />
          </label>
          <div className="form-field subject-identifier-field subject-form-field--wide">
            <span className="form-field__label">System-generated subject ID</span>
            <strong>{form.id ? form.code : 'Automatically generated after saving'}</strong>
            <small>EDU ASSIST generates this internal ID. It cannot be edited and remains the subject reference used by assignments.</small>
          </div>
        </div>
      </section>

      <section className="subject-form-section" aria-labelledby="subject-curriculum-heading">
        <div className="subject-form-section__heading">
          <p className="eyebrow">Curriculum placement</p>
          <h3 id="subject-curriculum-heading">School category and classification</h3>
        </div>
        <div className="subject-form-section__fields">
          <label>
            <span>School category</span>
            <select
              className="subject-division-select"
              value={form.academic_division}
              onChange={(event) => selectDivision(event.target.value)}
              required={!form.id}
              aria-invalid={Boolean(errors.academic_division)}
              aria-describedby={errors.academic_division ? 'subject-division-error' : undefined}
            >
              <option value="">Select a school category</option>
              {academicDivisions.map((division) => (
                <option key={division.value} value={division.value}>{division.label}</option>
              ))}
            </select>
            <FieldError id="subject-division-error" message={errors.academic_division} />
          </label>
          <label>
            <span>Subject classification</span>
            <select
              value={form.category}
              onChange={(event) => updateField('category', event.target.value)}
              required
              aria-invalid={Boolean(errors.category)}
              aria-describedby={errors.category ? 'subject-classification-error' : undefined}
            >
              {categoryOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <FieldError id="subject-classification-error" message={errors.category} />
          </label>
          <div className="form-field subject-grade-level-field subject-form-field--wide">
            <span className="form-field__label">Applicable grade levels</span>
            {!form.academic_division ? (
              <p className="subject-field-hint">Select a school category to display its active grade levels.</p>
            ) : availableGrades.length ? (
              <>
                <div className="subject-grade-level-actions">
                  <button
                    type="button"
                    className="action-button action-button--neutral"
                    onClick={() => {
                      setForm((current) => ({
                        ...current,
                        grade_level: availableGrades[0].id,
                        grade_levels: availableGrades.map((grade) => grade.id),
                      }))
                      clearErrors(['grade_levels'])
                    }}
                  >
                    Select all
                  </button>
                  <button
                    type="button"
                    className="action-button action-button--neutral"
                    onClick={() => {
                      setForm((current) => ({ ...current, grade_level: '', grade_levels: [] }))
                      clearErrors(['grade_levels'])
                    }}
                  >
                    Clear
                  </button>
                  <span>{form.grade_levels.length} selected</span>
                </div>
                <div className="selection-summary">
                  {availableGrades.map((grade) => (
                    <label key={grade.id}>
                      <input
                        type="checkbox"
                        checked={form.grade_levels.map(String).includes(String(grade.id))}
                        onChange={(event) => toggleGrade(grade, event.target.checked)}
                        aria-invalid={Boolean(errors.grade_levels)}
                        aria-describedby={errors.grade_levels ? 'subject-grades-error' : undefined}
                      />
                      {grade.name}
                    </label>
                  ))}
                </div>
              </>
            ) : (
              <p className="subject-field-hint">No active grade levels are configured for this school category.</p>
            )}
            <FieldError id="subject-grades-error" message={errors.grade_levels} />
          </div>
          {selectedDivision?.label === 'Senior High School' ? (
            <>
              <label>
                <span>Strand <small>(optional)</small></span>
                <select
                  value={form.strand}
                  onChange={(event) => updateField('strand', event.target.value)}
                  disabled={strandLoadStatus !== 'loaded' || !availableStrands.length}
                  aria-invalid={Boolean(errors.strand)}
                  aria-describedby={errors.strand ? 'subject-strand-error' : undefined}
                >
                  <option value="">
                    {strandLoadStatus === 'loading'
                      ? 'Loading active strands...'
                      : strandLoadStatus === 'error'
                        ? 'Could not load strands'
                        : availableStrands.length
                          ? 'No strand (optional)'
                          : 'No active strands configured'}
                  </option>
                  {availableStrands.map((strand) => (
                    <option key={strand.id} value={strand.id}>
                      {strand.name}{strand.description ? ` - ${strand.description}` : ''}
                    </option>
                  ))}
                </select>
                {strandLoadStatus === 'loading' ? (
                  <small>Loading active strands...</small>
                ) : strandLoadStatus === 'error' ? (
                  <small>Strands could not be loaded. See the page error message and retry.</small>
                ) : availableStrands.length ? (
                  <small>Core and Applied subjects may be left without a strand.</small>
                ) : (
                  <small>No active strands are configured. Ask an administrator to add or activate a strand under Academics &gt; Strands.</small>
                )}
                <FieldError id="subject-strand-error" message={errors.strand} />
              </label>
              <label>
                <span>Official Subject Code <small>(optional; school-provided)</small></span>
                <input
                  value={form.official_subject_code || ''}
                  maxLength={50}
                  onChange={(event) => updateField('official_subject_code', event.target.value)}
                  aria-invalid={Boolean(errors.official_subject_code)}
                  aria-describedby={errors.official_subject_code ? 'official-subject-code-error' : undefined}
                />
                <small>Enter the official curriculum code exactly as supplied by the school administrator.</small>
                <FieldError id="official-subject-code-error" message={errors.official_subject_code} />
              </label>
            </>
          ) : (
            <p className="subject-field-hint subject-form-field--wide">Strand selection is available for Senior High School subjects only.</p>
          )}
        </div>
      </section>
    </>
  )
}

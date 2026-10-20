# Issue 6 Academic Calculation Policy

## 1. Current authoritative data structure

### VERIFIED IMPLEMENTATION

`AcademicRecord` is period-based and identified by:
- enrollment
- subject
- academic_year
- grading_period_type
- quarter
- semester

The model enforces this uniqueness in `BACKEND/academics/models.py` via `unique_together = ('enrollment', 'subject', 'academic_year', 'grading_period_type', 'quarter', 'semester')`.

The system supports:
- Quarter 1 through Quarter 4
- Semester 1 through Semester 2

`AcademicRecord.clean()` also enforces that:
- quarter is required for `grading_period_type == 'Quarter'`
- semester is required for `grading_period_type == 'Semester'`
- quarter and semester are mutually exclusive

This indicates the current model treats quarter/semester records as distinct grading periods, not as replacing each other.

## 2. Current general-average implementation

### VERIFIED IMPLEMENTATION

The frontend currently calculates the displayed general average in `FRONTEND/src/pages/students/StudentDetailPage.jsx`:

- `academicRecords.map((record) => Number(record.final_grade))`
- filter out `NaN` values
- derive `generalAverage` as `sum(grades) / grades.length`, then `toFixed(2)`
- `final_grade` values are the only values used in the displayed general-average calculation
- null / missing `final_grade` values are excluded because `Number(null)` becomes `0`, but the filter keeps only valid numeric values, and the actual code checks `record.final_grade != null` before counting a failed subject

The effective rule is:
- general average = arithmetic mean of valid `final_grade` values from the currently loaded academic-record set
- missing/null `final_grade` values are not counted in the denominator
- the current record set is whatever the UI loaded for the student, not a canonical backend summary

### POTENTIAL GAP

There is no backend canonical academic-summary endpoint; all summary logic observed in the UI is client-computed.

### UNRESOLVED POLICY DECISION

No repository-authored canonical annual/general-average policy exists in the codebase.

## 3. Current failed-subject implementation

### VERIFIED IMPLEMENTATION

In the same frontend summary code:
- failing threshold = `record.final_grade < 75`
- pass threshold = `record.final_grade >= 75`
- failed-subject count is a `Set` of subject names for records where `final_grade != null && Number(record.final_grade) < 75`
- repeated records for the same subject are counted once because the code uses a distinct subject-name set

This means the current implementation counts distinct subject names, not individual period rows.

### VERIFIED IMPLEMENTATION

Missing `final_grade` is not treated as failing in the current frontend logic because the failing check explicitly requires `record.final_grade != null` before comparing to `75`.

### UNRESOLVED POLICY DECISION

The repository does not define whether a canonical subject summary should be aggregated across quarter/semester rows or whether a backend endpoint should become authoritative.

## 4. Academic-year behavior

### VERIFIED IMPLEMENTATION

`AcademicRecord` is linked to `academic_year` and the API exposes filtering by `academic_year` through `AcademicRecordViewSet.filterset_fields` in `BACKEND/academics/api.py`.

The current API behavior is:
- if `academic_year` is supplied, the queryset can be narrowed by that year
- if it is omitted, the caller is responsible for choosing the relevant year set before computing summary statistics

The model itself does not enforce a summary-wide year filter; it only preserves the owning academic year on each record.

### POTENTIAL GAP

A student can have multiple academic-year enrollments, and the frontend summary can potentially include records from more than one academic year if the caller loads a broad record set without explicit year filtering.

### UNRESOLVED POLICY DECISION

Whether the application should always isolate summary calculations to one year is not defined as a canonical rule.

## 5. Grading-period behavior

### VERIFIED IMPLEMENTATION

`AcademicRecord` distinguishes quarter and semester records by:
- `grading_period_type`
- `quarter` for quarter records
- `semester` for semester records

The model validation forbids quarter and semester from both being populated for the same record.

The API and UI also demonstrate period filters by `grading_period_type`, `quarter`, and `semester`.

The Grade Encoding page sends quarter/semester values conditionally:
- quarter records send `quarter: Number(filters.quarter)` and `semester: null`
- semester records send `semester: Number(filters.quarter)` and `quarter: null`

## 6. Prediction-service behavior

### VERIFIED IMPLEMENTATION

`BACKEND/predictions/services/prediction_service.py` selects the latest enrollment for a student with:
- `Enrollment.objects.filter(student=student).order_by('-academic_year__start_date').first()`

It then computes academic features from the raw records attached to that latest enrollment:
- `AcademicRecord.objects.filter(enrollment=enrollment).select_related('subject')`
- raw values are read from `record.final_grade or record.grade or 0`
- general average is computed as the mean of all available grade values on that enrollment
- failed-subject count is computed as the count of rows below 75, not a distinct-subject set

The model contract remains binary:
- `1 = At Risk`
- `0 = Not At Risk`

Application mapping remains:
- `At Risk -> High`
- `Not At Risk -> Low`

Moderate is not introduced in the ML path.

## 7. Frontend/backend responsibility

### VERIFIED IMPLEMENTATION

The backend currently returns raw academic records, not a canonical academic summary object.

The frontend is responsible for the currently displayed summary in `FRONTEND/src/pages/students/StudentDetailPage.jsx`:
- general average
- failed-subject count
- low grade interpretation

The prediction service is a separate pipeline that builds features from the latest enrollment and raw academic records, using different selection semantics than the UI summary.

## 8. Known gaps

### POTENTIAL GAP

- No canonical backend summary exists.
- Student summary behavior can mix records across multiple academic years when the caller omits the year filter.
- There is no authoritative repository document for the annual or semester grading policy.
- Prediction feature construction and UI summary calculation use different record-selection semantics.

### UNRESOLVED POLICY DECISION

- canonical annual/general-average policy
- canonical subject grade across multiple periods
- semester/annual aggregation rules
- whether a backend summary should become canonical

## 9. Current System-Implemented Academic Calculation Policy

### VERIFIED IMPLEMENTATION

Current system behavior is:
1. `AcademicRecord` is a period-based grade row keyed by enrollment, subject, year, period type, quarter, and semester.
2. quarter and semester are mutually exclusive and stored separately.
3. the UI computes the displayed general average as the mean of valid `final_grade` values from the currently loaded record set.
4. missing/null `final_grade` values are excluded from the average denominator.
5. failure threshold is `final_grade < 75`.
6. failed-subject count is a distinct-subject count, not a count of period rows.
7. multiple records for the same subject across different periods are allowed with the existing unique constraints.
8. the backend does not provide a canonical academic summary endpoint.
9. prediction service uses the latest enrollment and raw records attached to it, which is a different selection path from the UI summary.

### POTENTIAL GAP

The repository does not define a single authoritative academic policy beyond the current data model and UI implementation.

### UNRESOLVED POLICY DECISION

Any annual, semester, or final-grade aggregation rule is not currently defined as a canonical project policy.

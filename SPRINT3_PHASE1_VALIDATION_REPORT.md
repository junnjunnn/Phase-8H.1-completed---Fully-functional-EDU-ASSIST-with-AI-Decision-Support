# Sprint 3 Phase 1 Validation Report

## Scope

Implemented academic-year date validation, archived reference protection, and historical-data preservation for academic years, grade levels, sections, strands, enrollments, subjects, and academic records.

## Changes

- Added model and serializer validation for invalid academic-year date ranges.
- Blocked new operations against archived academic years, grade levels, sections, and strands.
- Preserved read access to existing historical enrollments and academic records.
- Filtered archived references from enrollment and section creation controls.
- Filtered archived grade levels from new subject creation while preserving them during historical subject editing.
- Fixed `Enrollment.enrollment_date` to use a date-valued default and added its migration.

## Validation Results

- Sprint 3 focused suite: **34 passed**.
- Subject validation suite: **38 passed**.
- Full Django suite: **179 passed**.
- Frontend production build: **passed**.
- File diagnostics: **no errors**.
- `git diff --check`: **passed**.

## Live Browser Check

Passed on Subject Management at `http://127.0.0.1:5176/subjects`:

- New subject creation showed active grade levels only.
- Archived Grade 9, Grade 12, and legacy archived grades were absent from the new-subject dropdown.
- Existing historical subject `MATH9` remained readable.
- Editing `MATH9` retained its archived Grade 9 selection without changing the record.

## Notes

`makemigrations --check --dry-run` still reports unrelated pre-existing migration drift in `accounts` and a section index. No unrelated migration changes were added.

## Subject Grade-Level Root Cause

The GradeLevel API already returned all grade levels with the correct `is_active` field, and the backend Subject serializer correctly rejected archived grades while accepting active grades. `SubjectsPage.jsx` was rendering `gradeLevels.map(...)` for new and edit forms, so archived grades appeared in new-subject creation. The fix filters only create mode; edit mode continues to show an existing archived association.

## Verdict

**PASS**: subject grade-level behavior and the broader Sprint 3 Phase 1 validation passed.
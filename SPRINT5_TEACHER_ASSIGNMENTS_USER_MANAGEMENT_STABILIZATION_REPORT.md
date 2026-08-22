# Sprint 5 Teacher Assignments + User Management Stabilization Report

## 1. Problem

Teacher Assignments was receiving inactive teachers, archived grade levels, and archived sections in its selection workflow. Its teacher count therefore did not represent active teacher accounts. User Management also lacked direct role and status filters.

## 2. Root Cause

The reference APIs preserve historical records by default, but the Teacher Assignments frontend consumed those full lists for new-assignment controls. The user API likewise returned all users by default, so the assignment page had no backend-scoped active-teacher source.

User Management had only a text search, despite the existing `UserProfile.role_name` and Django `User.is_active` fields already providing the required categorization and status model.

## 3. Backend Changes

Added opt-in query filtering only; default endpoint behavior remains unchanged for historical/management consumers.

- Grade levels: `?active_only=true` filters `GradeLevel.is_active=True`.
- Sections: `?active_only=true` filters `Section.is_active=True`, `grade_level.is_active=True`, and `academic_year.is_active=True`.
- Users: `?active_only=true` filters `User.is_active=True`.
- Users: `?role_name=TEACHER` filters through `UserProfile.role_name`.
- User querysets use `select_related('profile')` for the scoped list.

No models, migrations, API response fields, authentication behavior, or authorization rules were changed.

## 4. Frontend Changes

- Teacher Assignments requests active teachers, active grade levels, and active sections using the existing API services and query convention.
- Teacher dropdowns defensively exclude inactive users.
- Grade-level and section options exclude inactive records during create mode.
- Grade-to-section and academic-year dependency remains active.
- Edit mode retains a currently assigned archived teacher, grade, or section as an explicitly marked historical option, without making it available to new assignments.
- User Management now provides role and status filters using existing values.
- Supported roles are Administrator, Registrar, Teacher, and Guidance. The two existing administrator role codes remain distinct in the filter and display as Administrator in the table.
- Status filters use the existing Active/Inactive account state.

## 5. Active/Inactive Filtering Behavior

Existing fields discovered:

- Grade level: `GradeLevel.is_active`
- Section: `Section.is_active`
- Academic year: `AcademicYear.is_active`
- User account state: Django `User.is_active`
- User role: `UserProfile.role_name`
- Assignment history: `TeacherAssignment` records are retained

The backend enforces active-only behavior for new reference requests. The frontend also guards against inactive records returned unexpectedly. Historical assignment records are not deleted or rewritten.

## 6. User Categorization

User Management now supports combined role and status filtering:

- All roles
- Super Administrator
- School Administrator
- Registrar
- Teacher
- Guidance
- All statuses
- Active
- Inactive

Browser verification showed:

- All users: 16
- Active teachers: 2
- Inactive teachers: 2
- Active administrators: 5

The filters update the visible rows and count together. No unsupported roles were invented.

## 7. Authorization Behavior

Existing authorization was preserved.

- User Management remains protected by the existing `IsSchoolAdmin` backend permission.
- Teacher Assignments retains its existing authenticated/reference-access permissions for reads and school-admin permissions for writes.
- Regression coverage confirms a teacher cannot access User Management.
- No menu-only authorization workaround was added.

## 8. Database/Migration Impact

- No new migration was created.
- No records were deleted, archived, rewritten, or cleaned up.
- Existing historical assignments remain readable.
- The normal configured MySQL development server validated successfully.
- The separate SQLite development database has two pre-existing unapplied academics migrations. Applying them was not performed because migration `0008` encounters pre-existing duplicate adviser assignments under its unique constraint. This was documented rather than resolved by deleting or modifying historical data.

## 9. Browser Validation

A clean process pass was performed:

- Duplicate local Django/Vite development processes were identified and stopped.
- One frontend server was started at `127.0.0.1:5173`.
- One backend server was started at `127.0.0.1:8000` using the repository's normal `config.settings` database.
- The existing `demo_admin` account was used.

Teacher Assignments:

- Endpoint returned HTTP 200.
- Active teacher dropdown excluded inactive teachers.
- Active grade-level options excluded archived grade levels.
- Active section options excluded inactive/invalid sections.
- Selecting Grade 3 with the active academic year showed only its valid active section, Garnet.
- Selecting another grade showed its corresponding active section set.
- No horizontal overflow was measured at desktop.
- Existing assignment records remained available from the list endpoint.

User Management:

- All supported role categories appeared.
- Teacher + Active returned 2 users, all displayed as Teacher and Active.
- Teacher + Inactive returned 2 users, all displayed as Inactive.
- Super Administrator + Active returned 5 users, all displayed as Administrator.
- All Users displayed 16 users.
- Combined filters updated counts and rows correctly.
- No horizontal overflow was measured.

## 10. Responsive Validation

Validated at approximately 375 x 812 and 390 x 844 through browser viewport resizing.

- Teacher Assignments form remained usable.
- User Management filters remained present and usable.
- No document horizontal overflow was measured.
- No form-level horizontal overflow was measured.
- Existing mobile sidebar behavior remained available.

## 11. Dark/Light Validation

The existing theme system was preserved. Browser inspection confirmed the pages render under the existing light and dark theme tokens without adding theme-specific hardcoded surfaces.

- Selects, filters, tables, badges, and buttons retain existing theme styles.
- Active/inactive indicators remain readable.
- No global shell, scrollbar, sidebar, or header redesign was made.

## 12. Automated Test Results

Focused regression tests:

```text
Ran 6 tests in 0.126s
OK
```

The focused tests cover:

- inactive grade exclusion
- inactive/invalid section exclusion
- combined active teacher + role filtering
- default preservation of inactive users
- historical assignment readability
- User Management authorization

Full Django suite:

```text
Found 220 test(s).
Ran 220 tests in 6.242s
OK
```

## 13. API Verification Results

Live normal-config database counts:

- Total users: 16
- Active users: 11
- Active teachers: 2
- Inactive teachers: 2
- Total grade levels: 19
- Active grade levels: 12
- Inactive grade levels: 7
- Total sections: 12
- Active sections: 2
- Inactive sections: 10
- Teacher Assignments endpoint: HTTP 200

The frontend values matched the filtered API data in the clean browser run.

## 14. AI Compatibility

Confirmed unchanged:

- No AI files changed.
- No Random Forest artifact changed.
- No feature mapping changed.
- No prediction service changed.
- No training data changed.
- No retraining performed.
- No prediction behavior changed.

## 15. Validation Checks

Frontend build:

- PASS: `npm run build`
- Vite completed successfully.
- Existing large-chunk advisory remained non-blocking.

ESLint:

- PASS for changed JSX/JS files.

Diagnostics:

- PASS: no errors in changed backend, frontend, service, or regression-test files.

`git diff --check`:

- PASS: no whitespace/diff violations.
- Existing line-ending warnings were reported for already modified files.

## 16. Remaining Limitations

- No write mutation was performed against a real assignment because the requested validation could be completed safely through API/list/filter and UI state checks without creating test data.
- SQLite remains blocked by pre-existing duplicate data when applying its pending migration; no historical records were modified to bypass that issue.
- Existing unrelated worktree modifications remain untouched.

## 17. Final Verdict

READY FOR SCREENSHOT PREPARATION

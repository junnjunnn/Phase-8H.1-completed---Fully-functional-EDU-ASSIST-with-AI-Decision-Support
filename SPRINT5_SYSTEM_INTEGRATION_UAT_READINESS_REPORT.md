# Sprint 5 — System Integration and UAT Readiness Report

## 1. Objective

Sprint 5 integrated and smoke-tested the completed Sprint 1-4 modules, fixed confirmed cross-module defects, validated role boundaries, and assessed readiness for final UAT without changing the AI architecture or paper.

## 2. System Areas Tested

Validated through backend tests, read-only API matrices, frontend route smoke tests, and browser checks:

- Authentication and health
- Dashboards and shared navigation
- Academic structure, subjects, exact grade applicability, and teacher assignments
- Students and enrollment routes
- Grade encoding, attendance, and behavior routes
- Interventions, predictions, and reports routes
- Profile, settings, logout, sidebar, and header behavior
- User-management authorization
- Existing Phase 4 AI contract regression through the full backend suite

## 3. Administrator Validation

**PASS:** `demo_admin` login, dashboard, academic structure, subjects, teacher assignments, students, enrollment, grade encoding, attendance, behavior, interventions, predictions, reports, audit logs, profile, and settings routes loaded without UI alerts.

**PASS:** Admin API access returned 200 for the protected reference, academic, student, report, prediction, audit, and user-management reads checked in the matrix.

## 4. Registrar Validation

**PASS:** `registrar_test` authenticated successfully. Browser routes for Students, Enrollment, Subjects, and Grade Encoding loaded. Restricted User Management and Settings routes returned Access denied. API access to students, enrollments, reference data, subjects, and reports was available; restricted academic-record, attendance, behavior, intervention, prediction, audit, and user-list reads returned 403.

**BLOCKED:** Registrar dashboard is not currently supported. `/dashboard` is rejected by the frontend role guard and `/api/dashboard-summary/` returns 403. This conflicts with the broad dashboard-validation requirement but is consistent with the stated registrar workflow beginning at Students/Registration/Enrollment. No authorization was weakened.

## 5. Teacher Validation

**PASS:** `test1` authenticated successfully. Dashboard, My Classes, Students, Grade Encoding, Attendance, Behavior, Predictions, Reports, Profile, and Settings loaded without UI alerts. The My Classes header title was corrected from the fallback Dashboard label to My Classes.

**PASS:** Subjects and User Management routes returned the existing 403 Access denied behavior. Teacher API access remained role-scoped by existing authorization tests and matrices.

## 6. Guidance Validation

**PASS:** `test4` authenticated successfully. Dashboard, Students, Behavior, Interventions, Predictions, Reports, Profile, and Settings loaded. Subjects and User Management routes returned 403. Guidance API access to authorized student-support areas remained available; audit and user-management reads were restricted.

## 7. Academic Structure Validation

**PASS:** Existing Phase 5 coverage and full Django tests preserve Elementary, JHS, SHS, strands, exact selected grade applicability, generated subject identifiers, and assignment compatibility. No academic data was changed during Sprint 5 validation.

## 8. Grade Encoding Validation

**PASS by automated regression:** Existing grade-encoding, grading-period isolation, persistence, duplicate prevention, authorization, and archived-year tests remain included in the full backend suite. The route loaded successfully in browser smoke testing.

## 9. Attendance Validation

**PASS by automated regression and route smoke:** Attendance authorization and record workflows remain covered by the full suite; the Attendance route loaded for authorized roles and was blocked for registrar API access.

## 10. Behavior Validation

**PASS by automated regression and route smoke:** DepEd Core Values, behavior statements, AO/SO/RO/NO ratings, bulk behavior, authorization, and persistence remain covered by the full suite. Behavior loaded for teacher and guidance roles.

## 11. AI Prediction Validation

**PASS by regression:** The full Django suite passed with the unchanged 71-feature Phase 4 model contract and prediction tests. No AI/ML files, artifacts, feature mapping, prediction service, probability logic, or model behavior were modified in Sprint 5.

**PASS:** Prediction routes and API reads loaded for admin, teacher, and guidance. Unsupported-domain safety remains covered by Phase 3/4 tests.

## 12. Reports Validation

**PASS:** Reports route and `/api/reports/center/` loaded for authorized roles. Existing report authorization and aggregation tests remain in the full suite. No report redesign was made.

## 13. Authentication and Authorization

**PASS:** Active admin, registrar, guidance, and teacher accounts authenticated. Anonymous student access returned 401.

**HIGH FIXED:** `/api/auth/users/` previously returned all user records, including usernames, emails, roles, phone numbers, and assigned sections, to teacher and guidance roles. The endpoint now requires `IsSchoolAdmin`; admin receives 200, while registrar, guidance, and teacher receive 403. Focused permission tests pass.

## 14. UI/UX Findings

**FIXED:** Shared header labels for My Classes, Teacher Assignments, Enrollment, and Settings no longer fall back to Dashboard.

**UX:** Existing functional validation scripts contain stale assumptions, including an obsolete admin password, `/api/token/` references, and an outdated dashboard response shape. They were not used as final evidence and were not rewritten because this Sprint did not require validation-tool refactoring.

**UX:** Full frontend lint reports 19 errors and 12 warnings in unrelated pre-existing files. Changed Sprint 5 frontend files are diagnostics-clean and the changed layout component passes focused lint.

**UX:** Existing large frontend build-chunk warning remains.

## 15. Screenshot Readiness

**PASS for smoke-tested surfaces:** Login, dashboard, academic structure, subjects, profile/settings, and major teacher/guidance pages loaded without visible error alerts. The existing sidebar/header polish from Phase 5 remained stable.

**LIMITATION:** Full screenshot-by-screenshot review of every role/page was not completed in this pass. Temporary Sprint 4 validation subjects were already archived; no new demo data was created or altered.

## 16. Bugs Fixed

- Restricted user-list reads to school administrators.
- Corrected shared top-bar labels for My Classes, Teacher Assignments, Enrollment, and Settings.
- Updated contradictory user-permission tests to enforce the intended role boundary.

## 17. Remaining Issues

- **BLOCKED / requirements clarification:** Registrar dashboard is denied by both frontend and backend. Decide whether registrar should have a dashboard before UAT; do not grant access without defining its permitted metrics.
- **LOW/UX:** Full-project frontend lint baseline remains non-clean in unrelated components.
- **LOW/UX:** Existing validation scripts are stale and should be refreshed before a future repeatable UAT run.
- **LOW/UX:** Frontend build retains the existing large-chunk warning.
- **LIMITATION:** Browser testing used route/workflow smoke checks; destructive or data-creating end-to-end mutations were not performed against live records.

## 18. Automated Test Results

- Focused auth/user-permission tests: **16 passed**
- Full Django suite with SQLite settings: **214 passed**
- Frontend production build: **passed** with existing chunk-size warning
- Changed `AppLayout` lint: **passed**
- Touched-file diagnostics: **clean**
- `git diff --check`: **passed**
- Migration check: only pre-existing `academics` and `accounts` drift reported; no Sprint 5 migration created

## 19. Browser Validation

- Admin route smoke: **PASS** across dashboard, academic, student, enrollment, records, AI, reports, admin, profile, and settings pages.
- Teacher route smoke: **PASS** for allowed workflows; **PASS** 403 restrictions for subjects and users.
- Guidance route smoke: **PASS** for allowed workflows; **PASS** 403 restrictions for subjects and users.
- Registrar route smoke: **PASS** Students, Enrollment, Subjects, Grade Encoding; **PASS** restrictions for Users and Settings; **BLOCKED** Dashboard.
- Shared header title correction: **PASS**.
- Authentication/logout and profile/settings route behavior: **PASS**.

## 20. UAT Readiness Assessment

The system is stable across the tested admin, teacher, guidance, registrar, academic, behavior, attendance, reports, and AI surfaces. A confirmed HIGH user-data exposure was fixed without changing the AI or database schema. The remaining registrar-dashboard behavior requires a product decision because the backend currently intentionally denies that metric endpoint.

## 21. Final Verdict

**NOT READY FOR UAT**

Exact blockers:

1. Registrar dashboard behavior is unresolved: the UAT matrix requests a registrar dashboard, but the current authorization contract denies it at both frontend and backend.
2. Full-project frontend lint remains non-clean due to unrelated existing errors. Changed Sprint 5 files are clean.

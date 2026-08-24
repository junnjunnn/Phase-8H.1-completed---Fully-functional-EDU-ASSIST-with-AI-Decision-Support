# Priority 4: My Advisory Class Report

## A. Files inspected

- `BACKEND/common/authorization.py`
- `BACKEND/predictions/api.py`
- `BACKEND/students/api.py`
- `BACKEND/students/models.py`
- `BACKEND/students/serializers.py`
- `BACKEND/academics/models.py`
- `BACKEND/academics/api.py`
- `BACKEND/tests/test_adviser_student_authorization.py`
- `FRONTEND/src/routes/AppRoutes.jsx`
- `FRONTEND/src/config/navigation.js`
- `FRONTEND/src/components/layout/SidebarNav.jsx`
- `FRONTEND/src/pages/academics/MyClassesPage.jsx`
- `FRONTEND/src/pages/students/StudentDetailPage.jsx`
- `FRONTEND/src/services/academicsService.js`
- `FRONTEND/src/services/predictionService.js`
- `FRONTEND/src/App.css`

## B. Files changed

- `BACKEND/predictions/api.py`
- `BACKEND/tests/test_adviser_student_authorization.py`
- `FRONTEND/src/pages/academics/MyAdvisoryClassPage.jsx`
- `FRONTEND/src/routes/AppRoutes.jsx`
- `FRONTEND/src/config/navigation.js`
- `FRONTEND/src/components/layout/SidebarNav.jsx`
- `FRONTEND/src/services/predictionService.js`
- `FRONTEND/src/App.css`

## C. Backend changes

The existing `/api/adviser-dashboard/` endpoint now accepts:

- `section`: validated against the authenticated adviser's active authorized sections;
- `search`: applied server-side to student name, middle name, last name, or LRN.

The endpoint returns a complete `students` roster for the filtered active enrollments, including enrollment, academic, attendance, behavior, intervention, and stored prediction fields. The existing `students_requiring_attention` response remains available for dashboard compatibility.

## D. Frontend changes

Added `/my-advisory-class` and `MyAdvisoryClassPage` with:

- authorized advisory-section selector;
- backend name/LRN search;
- active student roster;
- LRN, grade, section, enrollment status, average, attendance, behavior, risk, and intervention fields;
- links to the existing student detail page;
- empty states for no advisory class, no students, and missing monitoring records;
- responsive roster styling compatible with the existing shell and theme.

The sidebar displays `My Advisory Class` for teachers. `My Classes` remains unchanged and continues to separate advisory classes from subject assignments.

## E. API changes

`getAdviserDashboard(params)` now forwards query parameters to `/api/adviser-dashboard/`.

No new models or migrations were added.

## F. Authorization changes

No new authorization system was introduced. The endpoint continues to derive scope from:

`authenticated teacher -> active adviser sections -> active enrollments`

An unassigned section returns `404` and does not return roster data. Archived sections and inactive enrollments remain excluded by the existing authorization boundary and active-section query.

## G. Database changes

None. No production or historical records were modified.

## H. Tests

- Focused adviser suite: `15/15 passed`
- Django system check: passed
- Frontend ESLint on changed files: passed
- Frontend production build: passed
- Diagnostics: no errors
- `git diff --check`: passed

## I. Browser validation

Previously authenticated Priority 3 browser validation confirmed `test1` has role `TEACHER`, active advisory sections `Garnet` and `Onyx`, and one authorized active student.

For Priority 4, source/build validation completed, but a fresh authenticated browser login was not completed in this run because the shared JWT had expired and the password for the fresh login was not supplied. Therefore the following are **NOT TESTED** in this run:

- authenticated Priority 4 section switching in the browser;
- authenticated Priority 4 search by name or LRN;
- authenticated student-detail navigation from the new page;
- authenticated light/dark theme checks on the new page;
- authenticated admin and ordinary-teacher regression sessions.

## J. Known limitations

The roster currently defaults to active enrollments, matching the requirement for the current advisory class. Historical enrollment status filtering is not exposed on this current-roster page.

The live `test1` data currently has no academic, attendance, behavior, intervention, or prediction records, so the UI correctly displays `N/A`, `No record`, or `No prediction` for those fields.

## K. Manual testing checklist

| Test | Result |
|---|---|
| 1. Login as Adviser | NOT TESTED: fresh password unavailable |
| 2. Open My Advisory Class | NOT TESTED in fresh authenticated session |
| 3. Verify assigned advisory sections | PASS by live database/API inspection: Garnet and Onyx |
| 4. Select each advisory section | NOT TESTED in browser |
| 5. Verify only authorized students appear | PASS by focused backend tests |
| 6. Search by student name | PASS by focused backend test; browser NOT TESTED |
| 7. Search by LRN | PASS by endpoint implementation; browser NOT TESTED |
| 8. Open a student | NOT TESTED in browser |
| 9. Verify academic summary | PASS by endpoint implementation/tests; no live records available |
| 10. Verify attendance summary | PASS by endpoint implementation/tests; no live records available |
| 11. Verify behavioral summary | PASS by endpoint implementation/tests; no live records available |
| 12. Verify intervention status | PASS by endpoint implementation/tests; no live records available |
| 13. Verify prediction information | PASS by endpoint implementation/tests; no live records available |
| 14. Attempt unauthorized student access | PASS through existing authorization suite |
| 15. Verify mobile layout | NOT TESTED in browser for this page |
| 16. Verify dark mode | NOT TESTED in browser for this page |

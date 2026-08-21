# Sprint 4 Phase 5 Follow-Up: Subject Identifier and UI Stability Report

## 1. Problem

Subject management exposed `Subject.code` as a user-entered field even though the field is an internal unique identifier. The application layout also allowed the profile menu to affect header layout and did not explicitly isolate main-content scrolling from the sidebar.

## 2. Existing Subject Code Architecture

`Subject.code` is a required unique `CharField(max_length=30)`. It is not used as a foreign-key target. `TeacherAssignment.subject` and `AcademicRecord.subject` reference `Subject.id`. Reports use subject IDs for filtering and subject names for human-readable aggregation. The prediction service reads `Subject.name` for the existing 71-feature contract and does not read `Subject.code`.

The live SQLite database contains 15 subjects and no blank codes. Existing values such as `MATH9`, `GE101`, `GE2221`, `123`, and other historical/test values were inspected and preserved.

## 3. Why Source Documents Do Not Define a Subject Code

The authoritative files in `F:\edu_new\Docx` are report-card templates. They list learning areas and SHS subject groupings, but do not define an official subject-code system. The generated identifier is therefore an EDU ASSIST internal identifier only. It is not a DepEd code, school curriculum code, or official abbreviation.

## 4. New Internal Identifier Design

New or blank-coded subjects receive a server-generated identifier in the form:

`SUBJ-<12 uppercase hexadecimal characters>`

Example: `SUBJ-8A701D4DC2BB`.

Generation occurs in `Subject.save()`, uses UUID entropy, retries on uniqueness collisions, and leaves valid existing codes untouched. The identifier remains stable when the subject name changes. The serializer exposes `code` as read-only, so normal API create/update requests cannot manually assign or overwrite it.

## 5. Existing-Record Preservation

No existing valid subject identifiers were regenerated. Blank identifiers, if encountered, are populated on save. No subjects, academic records, enrollments, teacher assignments, reports, or historical relationships were deleted or converted.

## 6. Database/Migration Changes

No migration was required for identifier generation because the existing `code` column and uniqueness constraint already support the new behavior. The previously applied `0007_subject_grade_levels` migration remains unchanged. Existing unrelated migration drift was not modified.

## 7. Academic Division Compatibility

The Phase 5 division workflow remains intact:

- Division supplies eligible grade candidates.
- Administrators select exact applicable `grade_levels`.
- The backend validates division/grade compatibility.
- SHS strand selection remains conditional and optional.
- Elementary/JHS strands remain rejected.

The generated identifier does not affect `Subject.grade_level`, `Subject.grade_levels`, or assignment filtering.

## 8. Teacher Assignment Compatibility

Teacher assignments continue to use `Subject.id`. Existing grade compatibility validation and applicable-grade filtering remain unchanged.

## 9. Grade Encoding Compatibility

Grade encoding continues to select and persist subjects through the existing subject primary-key relationship. No identifier field was introduced into academic-record or grade-encoding contracts.

## 10. Reports Compatibility

Reports continue to filter by subject ID and aggregate by subject name. No report query or response contract was changed. Existing subject codes remain available where administrative displays expose them.

## 11. AI Compatibility

**AI architecture unchanged.** No Random Forest artifact, label encoder, feature mapping, training data, prediction service, model feature count, feature order, probability logic, or risk criteria was modified. Subject identifiers are not AI features. The 71-feature Phase 4 contract remains unchanged.

## 12. Sidebar Fix

The application shell now occupies the viewport with `height: 100dvh` and hidden outer overflow. The sidebar fills the shell and has its own overflow behavior, while `.page-content` is the independently scrollable region. This prevents main-page scrolling from moving the sidebar.

## 13. Header/Profile Fix

The top bar is a fixed-size flex item inside the content area. The profile wrapper establishes a positioning context, and `.profile-dropdown` is absolutely positioned with its own z-index, width, surface, border, and shadow. Opening the menu overlays content instead of changing header dimensions.

## 14. Automated Tests

- Focused subject/academic suite: **49 passed**.
- Full Django suite with `config.settings_sqlite`: **214 passed**.
- Frontend production build: **passed** with the existing large-chunk warning.
- Focused lint for `SubjectsPage` and `academicsService`: **passed**.
- Touched-file diagnostics: **clean**.
- `git diff --check`: **passed**, with existing LF/CRLF warnings only.
- Coverage includes generated IDs, uniqueness format, preservation, stability after rename, blank-code backfill, API overwrite protection, academic divisions, exact grade applicability, SHS strands, authorization, assignments, and historical records.

## 15. Browser Validation

Using the existing `demo_admin` account on the local app:

- Subject Management loaded successfully.
- No editable `Subject code` textbox was present.
- New-subject UI displayed `Automatically generated after saving`.
- Academic division and exact applicable-grade controls remained available.
- Main content had independent scrolling (`overflow-y: auto`, scroll height greater than client height).
- Sidebar remained at the same viewport position after main content scrolling.
- Header height was `222.47px` before and after opening the profile dropdown.
- Profile dropdown appeared as an overlay below the profile control.

The existing teacher account `test1` remains unauthorized for Subject Management, preserving the prior 403 boundary.

## 16. Remaining Limitations

- Full-project frontend lint still contains unrelated pre-existing errors outside the changed subject-management pages, including existing Grade Encoding lint issues.
- The current database has historical user-supplied codes; they are intentionally not normalized into the new `SUBJ-*` format.
- Browser validation verified identifier display and layout geometry, but did not create new persistent data in this follow-up.

## 17. Files Changed

- `BACKEND/academics/models.py`
- `BACKEND/academics/serializers.py`
- `BACKEND/academics/admin.py`
- `BACKEND/academics/tests.py`
- `BACKEND/academics/tests_subject_validation.py`
- `FRONTEND/src/App.css`
- `FRONTEND/src/pages/academics/SubjectsPage.jsx`
- `FRONTEND/src/pages/academics/AcademicStructurePage.jsx`
- `SPRINT4_PHASE5_SUBJECT_IDENTIFIER_UI_STABILITY_REPORT.md`

No AI/ML files were changed.

## 18. Final Verdict

**FINAL VERDICT: NOT READY TO CLOSE** because full-project frontend lint still reports unrelated pre-existing errors outside the changed subject-management pages. The implementation itself preserves existing relationships, keeps AI unchanged, generates safe internal identifiers, and stabilizes the layout.

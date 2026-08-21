# Sprint 4 Phase 5 — Final Validation Report

## 1. Problem Identified

Subject creation previously required selecting one primary `GradeLevel`. That did not match the school's division-oriented workflow and could not express that one subject applies across all grades in Elementary, Junior High School, or Senior High School.

## 1. Objective

Verify the implemented academic-division and subject-applicability workflow against the authoritative DOCX files, then correct any unsupported assumptions without changing the AI architecture.

## 2. Source Documents

The following files were inspected from `F:\edu_new\Docx`:

- `ELEMENTARY.docx`
- `JUNIORHS.docx`
- `SENIORHS.docx`

The DOCX files are report-card templates. They define division-specific subject lists and examples, but they do not explicitly enumerate every grade to which each subject applies.

## 3. Source-Derived Academic Structure

| Source | Academic Level | Grade | Subject | Strand | Notes |
|---|---|---|---|---|---|
| `ELEMENTARY.docx` | Elementary | Grade 6 shown in sample (`6 - Onyx`) | See subject table below | Not specified in source | Transfer section references Grade 7; document does not state a complete Grade 1-6 applicability rule |
| `JUNIORHS.docx` | Junior High School | Grade 10 shown in sample (`10 - Ruby`) | See subject table below | Not specified in source | Transfer section references Grade 11; document does not state a complete Grade 7-10 applicability rule |
| `SENIORHS.docx` | Senior High School | Grade 11 shown in sample (`11 - Jasper`) | See subject table below | HUMSS shown in sample | Transfer section references Grade 12; subject roster is presented as Grade 11 first/second semester content; strand-specific applicability is not specified |

The repository migration remains the project-defined structural reference for the grade groups:

- Elementary: Grade 1 through Grade 6 (`G1`-`G6`)
- Junior High School: Grade 7 through Grade 10 (`G7`-`G10`)
- Senior High School: Grade 11 and Grade 12 (`G11`-`G12`)
- SHS strands: STEM, ABM, HUMSS, GAS, TVL-ICT, TVL-HE

## 4. Source-Derived Subject Structure

| Source | Academic Level | Grade | Subject | Strand | Notes |
|---|---|---|---|---|---|
| `ELEMENTARY.docx` | Elementary | Grade 6 sample; exact applicability not specified | English: Language, Reading, Writing, Filipino, Mathematics, Geometry, Science, HeKaSi, MAPE, Music, Arts, Physical Education, Values Education, EPP / HELE, Nihongo, Computer, Homeroom | Not specified in source | Music/Arts/Physical Education appear under MAPE |
| `JUNIORHS.docx` | Junior High School | Grade 10 sample; exact applicability not specified | English, Filipino, Mathematics, Science, Araling Panlipunan (AP), MAPEH, Music, Arts, Physical Education, Health, Values Education, TLE, Nihongo, Computer, Homeroom | Not specified in source | Music/Arts/Physical Education/Health appear under MAPEH |
| `SENIORHS.docx` | Senior High School | Grade 11 sample; Grade 12 transfer reference only | Oral Communication in Context, Komunikasyon at Pananaliksik sa Wika at Kulturang Pilipino, Media and Information Literacy, General Mathematics, Earth and Life Science, Physical Education and Health, English for Academic and Professional Purposes, Entrepreneurship, Introduction to World Religions, Computer, Reading and Writing Skills, Pagbasa at Pagsusuri ng Iba't-Ibang Teksto Tungo sa Pananaliksik, 21st Century Literature from the Philippines and the World, Statistics and Probability, Physical Science, Practical Research 1, Empowerment Technologies, Disciplines in the Social Sciences, Nihongo | HUMSS shown in sample; per-subject strand applicability not specified | First and second semester subject groups are explicitly shown; Core versus Applied and Specialized headings are present |

The documents also contain the same DepEd observed-value statements and AO/SO/RO/NO markings used by the existing behavior architecture.

## 5. Comparison With Existing Implementation

`GradeLevel.school_level` already distinguishes `Elementary`, `Junior High School`, and `Senior High School`. `Section` and `Enrollment` retain explicit grade-level and strand relationships. Elementary/JHS strand rejection and SHS strand validation already existed and remain intact.

## 4. Existing Subject Architecture

`Subject` originally had a nullable primary `grade_level` foreign key and optional `strand`. Academic records, teacher assignments, reports, and frontend filtering consume the primary grade-level relationship. No existing many-grade subject applicability model was found.

## 6. New Academic-Division Workflow

A centralized backend resolver now supports:

- `ELEMENTARY`
- `JUNIOR_HIGH_SCHOOL`
- `SENIOR_HIGH_SCHOOL`

Subject creation accepts `academic_division`; the backend resolves the eligible active grade levels from `GradeLevel.school_level`. Because the DOCX files do not establish that every subject applies to every grade in a division, the administrator must select the exact applicable grades. The backend stores only those selected grades in `Subject.grade_levels` and keeps the first selected grade in the legacy primary `grade_level` field.

The API endpoint `GET /api/subjects/academic-divisions/` returns division labels and resolved grade summaries for the frontend. The backend remains authoritative; frontend mappings are not trusted for persistence.

## 7. Grade-Level Eligibility Mapping

| Academic division | Resolved grade levels |
|---|---|
| Elementary | Eligible candidates: Grade 1 through Grade 6 from repository migration; source DOCX shows Grade 6 but does not enumerate all grades |
| Junior High School | Eligible candidates: Grade 7 through Grade 10 from repository migration; source DOCX shows Grade 10 but does not enumerate all grades |
| Senior High School | Eligible candidates: Grade 11 and Grade 12 from repository migration; source DOCX shows Grade 11 and references Grade 12 transfer |

## 8. SHS Strand Handling

The division workflow does not automatically assign a strand or all SHS grades. The strand control is shown only for Senior High School. The source sample shows HUMSS, but does not state per-subject strand applicability; the implementation therefore preserves optional strand selection and does not invent strand mappings. Existing model and serializer rules continue to reject strands for Elementary/JHS and inactive strands.

## 9. Corrections Made

The previous implementation incorrectly treated an academic division as proof that a subject applied to every grade in that division. This was corrected after inspecting the DOCX files. Division now supplies eligible grade candidates, while exact applicability is explicitly selected and validated. No correction to the division identifiers or repository grade-group boundaries was required, but those boundaries are documented as repository-defined rather than fully enumerated by the DOCX templates.

## 10. Backend Changes

- Added `BACKEND/academics/academic_divisions.py` as the single division resolver.
- Added `Subject.grade_levels` many-to-many applicability relation.
- Added migration `BACKEND/academics/migrations/0007_subject_grade_levels.py`.
- Existing subjects were backfilled from their primary grade level by the migration.
- Extended `SubjectSerializer` with division input, writable exact `grade_levels`, and resolved grade output.
- Added division API action to `SubjectViewSet`.
- Added teacher-assignment validation to reject a subject not applicable to the selected grade.
- Preserved existing code/name/category/strand/authorization validation.

## 11. Frontend Changes

- `SubjectsPage` now loads the backend division options.
- The form offers an Academic Division selector and checkboxes for exact applicable grades within that division.
- Legacy single-grade selection remains available only when no division is selected.
- SHS category and strand controls are conditional.
- The combined `AcademicStructurePage` uses the same division API.
- Grade Encoding and Teacher Assignments now filter subjects using `grade_levels`, with fallback to the legacy `grade_level` field.
- Existing subject list/edit behavior remains available, including archived historical subjects.

## 12. Validation Rules

- Unsupported division values are rejected.
- Empty subject names and duplicate codes remain rejected.
- Resolved grades must belong to one school-level division.
- A division-only subject submission is rejected because the source documents do not establish universal subject applicability.
- Archived grades are not selected by the division resolver.
- Elementary/JHS strands remain invalid.
- SHS strands remain optional and must be active.
- Subject assignments must match the selected class grade.
- Subject-management writes remain restricted to existing school-admin permissions.

## 13. Database/Migration Impact

Migration `0007_subject_grade_levels` was created and applied to the existing SQLite database. It adds one many-to-many table and copies each existing subject's primary grade relationship into the new applicability relation. No subjects, academic records, enrollments, assignments, or historical records were deleted or rewritten.

The repository still reports unrelated pre-existing migration drift in `academics` and `accounts`; no drift migration was generated for this phase.

## 14. Backward Compatibility

The original `Subject.grade_level` field remains. Existing consumers and records continue to work. New multi-grade subjects expose both the explicit `grade_levels` relation and the first resolved grade through the legacy field. Downstream grade-encoding and teacher-assignment filtering now prefer explicit applicability and fall back to the old field for historical records.

## 15. Authorization

Subject writes remain restricted to existing school-admin permissions. Teacher access to Subject Management remains denied.

## 16. AI Compatibility

**AI architecture unchanged.** No Random Forest artifact, feature mapping, training dataset, prediction algorithm, prediction criteria, probability logic, or prediction service was modified in Phase 5. The subject-management change only improves upstream academic relationships. Phase 4's AI contract remains available; unsupported subject values are still handled by its existing runtime policy.

## 17. Automated Testing

- Focused academic and subject suite: **146 passed** after the final applicability correction.
- New coverage includes Elementary/JHS/SHS division resolution, invalid divisions, edit behavior, SHS strand compatibility, assignment compatibility, and historical records.
- Touched-file diagnostics: **no errors**
- Frontend production build: **passed**; existing large-chunk warning remains.
- Targeted frontend lint: new `SubjectsPage`, service, and changed filtering code are clean. Existing unrelated lint errors remain in `AcademicStructurePage` and `GradeEncodingPage`.
- Full backend Django suite: **209 passed** after migration.

## 18. Browser Validation

**VERIFIED with existing `demo_admin` account:**

- Teacher `test1` was denied access to `/subjects` with HTTP/UI 403, confirming permissions were not weakened.
- Admin opened Subject Management successfully.
- The final browser pass displayed division candidates as selectable eligible grades, not automatic applicability.
- `PH5_TEST_ELEMENTARY` was saved only to Grade 1 and Grade 6.
- `PH5_TEST_JHS` was saved only to Grade 7.
- `PH5_TEST_SHS` was saved only to Grade 11 with HUMSS strand.
- Exact persisted relationships were verified through SQLite and all three temporary records were archived afterward.
- Teacher `test1` received the existing 403 Access denied response for Subject Management.
- Strand control was hidden for JHS and shown for SHS.
- Elementary, JHS, and SHS subjects were saved through the UI.
- Temporary validation subjects were archived afterward; no active temporary records remain.

The DOCX files were available and inspected. Their lack of complete per-grade applicability is the reason the final workflow requires explicit selected grades.

## 19. Remaining Limitations

- The source templates do not provide a complete grade-by-grade subject applicability matrix. A school-approved subject matrix is still required to automate exact grade selection.
- Existing frontend lint debt outside the changed subject page remains.
- The model does not gain a new subject feature or retraining from this phase.
- Division resolution currently includes all active grade levels in the relevant `school_level`; future source documents may require a reviewed configuration update.

## 20. Final Verdict

**NOT READY TO CLOSE**

The source documents are verified, the unsupported full-division applicability assumption is corrected, browser validation is complete, and the full Django suite passes. The phase remains **NOT READY TO CLOSE** because the DOCX templates do not provide a complete school-approved subject-to-grade matrix; exact automatic applicability cannot be derived for every subject without that matrix.

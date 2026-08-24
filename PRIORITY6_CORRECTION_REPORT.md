# Priority 6 Correction and Transparency Report

## A. Issues Investigated

- Missing explicit View Student action in My Advisory Class.
- Academic summary provenance and general-average calculation.
- Quarter/semester academic filtering.
- Attendance school-day source and calendar support.
- Behavioral category source and legacy seed values.
- Prediction generation reachability and failure reporting.
- Cross-module authorization and consistency.

## B. Root Causes

- My Advisory Class linked student names to the existing profile but did not provide a clearly labeled action.
- Student profile calculated its average from `final_grade` with a raw `grade` fallback, while the existing Adviser Dashboard calculation uses stored non-null `final_grade` values.
- The profile did not send the existing `grading_period_type` filter.
- The prediction generation button was rendered only when a prediction already existed, making generation unreachable from the no-prediction state.
- Attendance stores monthly aggregate `school_days`, `days_present`, `absences`, and `times_tardy`; no date-level school calendar model exists.
- The canonical behavior reference catalog contains the four DepEd core values, but demo seed data also contains legacy `Discipline` and `Respect` records. Historical records were not renamed or destroyed.

## C. Existing Functionality Reused

- Existing `/students/<id>/` Student Monitoring Profile.
- Existing authorized enrollment-related APIs.
- Existing academic `grading_period_type`, `quarter`, and `semester` fields.
- Existing Random Forest prediction endpoint and feature-contract diagnostics.
- Existing AO/SO/RO/NO ratings and behavior reference synchronization.
- Existing centralized adviser authorization helpers.

## D. Backend Changes

**IMPLEMENTED**:

- Added `subject_name`, `academic_year_name`, and `encoded_by_name` to `AcademicRecordSerializer`.
- Existing academic API filtering by `grading_period_type` is reused.
- Existing adviser academic-record access fix remains in place: subject assignment filtering applies only to teachers with active SUBJECT assignments.
- Added focused tests for authorized academic records, quarter/semester filters, provenance, and related endpoint authorization.

**NOT IMPLEMENTED**: No new monitoring endpoint, calendar subsystem, behavior migration, or prediction algorithm was added.

## E. Frontend Changes

**IMPLEMENTED**:

- Added explicit `View Student` action linking to the existing Student Monitoring Profile.
- Added Academic Period filter: All, Quarter, Semester.
- Filtered academic records recalculate the visible profile summary.
- Academic table now shows subject, teacher/encoder, period, raw grade, final grade, and academic year.
- Profile general average now follows the existing dashboard method: average of stored non-null `final_grade` values.
- Prediction generation is available from the no-prediction state for authorized staff.
- Prediction contract diagnostics are shown when the existing generation endpoint returns them.
- Existing AO/SO/RO/NO values and stored behavior category names remain unchanged.

## F. Database/Migration Changes

**IMPLEMENTED**: No migrations and no production-like records were changed.

## G. Prediction Workflow Findings

**IMPLEMENTED AND TESTED**:

- Generation is triggered by `POST /api/predictions/predict/<student_id>/`.
- The endpoint requires authentication, authorized staff access, and an authorized student.
- Teachers can generate for students in their authorized scope; the existing frontend role gate permits the established teacher/admin roles.
- The service loads the existing Random Forest model, label map, and feature mapping.
- The feature vector uses the latest enrollment plus academic, attendance, behavior, and intervention data.
- Subject names must exist in the saved model vocabulary; unsupported subjects produce `422` feature-contract diagnostics.
- Existing stored predictions, probabilities, factors, and explanations remain the only displayed prediction data.
- No prediction is fabricated or manually inserted.

## H. Attendance School-Day Findings

**ARCHITECTURE LIMITATION**:

- `AttendanceRecord.school_days` is a manually stored monthly aggregate.
- There is no date-level school calendar, holiday, suspension, or school-activity model in the inspected implementation.
- The current system can transparently display stored school-day totals and calculate the ratio `days_present / school_days`, but cannot verify official calendar dates.
- No dates were fabricated and no calendar subsystem was introduced in this correction pass.
- A future administrative calendar capability should be designed separately with administrator-only management and migration planning.

## I. Behavioral Category Findings

**ALREADY SUPPORTED**:

- `behavior/reference_data.py` defines Maka-Diyos, Makatao, Maka-Kalikasan, and Makabansa with DepEd indicators.
- The sync command can deactivate non-canonical reference categories without deleting historical assessments.

**DATA-QUALITY LIMITATION**:

- The demo seed command still creates legacy `Discipline` and `Respect` categories for demo assessments. They were not silently renamed because doing so would alter historical meaning.
- AO, SO, RO, and NO remain stored and displayed as the existing rating terminology.

## J. Academic Calculation Findings

**IMPLEMENTED AND ALIGNED**:

- Existing Adviser Dashboard calculation averages non-null `AcademicRecord.final_grade` values.
- The profile now uses the same final-grade-only method.
- Raw `grade` and `final_grade` are both shown so the calculation is inspectable.
- Failed-subject indication uses the established below-75 rule on stored final grades.
- Quarter and semester records remain distinct and filterable.

## K. Tests Performed

**TESTED**:

- Focused correction and adviser suites: 17 tests passed.
- Focused adviser plus prediction suites: 37 tests passed.
- Existing prediction generation and feature-contract tests passed.
- Frontend ESLint for the changed Student Monitoring Profile and My Advisory Class files: passed.
- Frontend production build: passed.
- Diagnostics: no errors in changed backend/frontend files.
- `git diff --check`: passed.

**NOT TESTED**: New authenticated browser workflow validation.

## L. Browser Validation

**NOT TESTED**: Browser validation was not performed for this correction pass. No browser result is claimed.

## M. Remaining Limitations

- Official date-level attendance validation requires a future administrator-managed school-calendar capability.
- Legacy demo behavior categories remain as historical/demo data; canonical DepEd categories are available through the existing reference catalog and sync mechanism.
- Prediction generation can legitimately fail when current student subjects or categorical values are absent from the saved model vocabulary; the existing diagnostics are now surfaced.
- No overall Improving/Stable/Declining classifier or trend chart was introduced without a supported methodology.
- Detailed mobile UI stabilization remains deferred.

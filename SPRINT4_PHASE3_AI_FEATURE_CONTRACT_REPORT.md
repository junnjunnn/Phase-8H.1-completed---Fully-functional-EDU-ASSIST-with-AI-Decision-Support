# Sprint 4 Phase 3: AI Feature-Contract Repair Report

## 1. Problem

The saved Random Forest accepts 62 columns in a fixed order, but the application previously converted several valid current database values into silent all-zero categorical groups and discarded unrecognized subject grades. Student 8 demonstrates the risk: `EDUCATION=99` contributed to `general_average` but to none of the eight subject-grade features.

This sprint repaired application-side contract handling only. The Random Forest, label encoder, feature mapping artifacts, prediction algorithm, database records, and schema were not changed. The model was not retrained.

## 2. Existing 62-Feature Contract

The persisted artifacts agree on 62 features. The model order is numeric features first, followed by one-hot categorical features. `risk_model.pkl` reports `n_features_in_ = 62` and its `feature_names_in_` matches the encoded columns generated from `feature_mapping.json`.

The training pipeline uses `OneHotEncoder(handle_unknown='ignore')`. Its source vocabulary is synthetic and contains school years `2024-2025`, `2025-2026`; grade levels `Grade 4` through `Grade 10`; sections `A` through `D`; legacy behavior values; AO/SO/RO/NO; intervention categories; and intervention outcomes. Unknown values were previously accepted by the service as all-zero groups.

## 3. Database-to-Feature Mapping

| Database field | Service field | Mapping field | Encoded model feature(s) |
|---|---|---|---|
| `AcademicRecord.final_grade` or `grade` for subject `Mathematics` | `mathematics_grade` | numeric `mathematics_grade` | `mathematics_grade` |
| `AcademicRecord.final_grade` or `grade` for `English` | `english_grade` | numeric `english_grade` | `english_grade` |
| `AcademicRecord.final_grade` or `grade` for `Science` | `science_grade` | numeric `science_grade` | `science_grade` |
| `AcademicRecord.final_grade` or `grade` for `Filipino` | `filipino_grade` | numeric `filipino_grade` | `filipino_grade` |
| `AcademicRecord.final_grade` or `grade` for `Araling Panlipunan` | `araling_panlipunan_grade` | numeric `araling_panlipunan_grade` | `araling_panlipunan_grade` |
| `AcademicRecord.final_grade` or `grade` for `ESP` | `esp_grade` | numeric `esp_grade` | `esp_grade` |
| `AcademicRecord.final_grade` or `grade` for `MAPEH` | `mapeh_grade` | numeric `mapeh_grade` | `mapeh_grade` |
| `AcademicRecord.final_grade` or `grade` for `TLE` | `tle_grade` | numeric `tle_grade` | `tle_grade` |
| all selected academic grades | `general_average` | numeric `general_average` | `general_average` |
| academic grades below 75 | `failed_subjects` | numeric `failed_subjects` | `failed_subjects` |
| `AttendanceRecord.days_present` | `present_days` | numeric `present_days` | `present_days` |
| `AttendanceRecord.absences` | `absent_days` | numeric `absent_days` | `absent_days` |
| `AttendanceRecord.times_tardy` | `late_days` | numeric `late_days` | `late_days` |
| no current database field | `excused_absences=0` | numeric `excused_absences` | `excused_absences` |
| attendance aggregate | `attendance_rate` | numeric `attendance_rate` | `attendance_rate` |
| attendance aggregate | `absent_percentage` | numeric `absent_percentage` | `absent_percentage` |
| attendance aggregate | `late_percentage` | numeric `late_percentage` | `late_percentage` |
| academic grades at least 90 | `high_grade_count` | numeric `high_grade_count` | `high_grade_count` |
| existence of `Intervention` rows | `has_intervention` | numeric `has_intervention` | `has_intervention` |
| count of `Intervention` rows | `number_of_interventions` | numeric `number_of_interventions` | `number_of_interventions` |
| `Enrollment.academic_year.name` | `school_year` | categorical `school_year` | `school_year_2024-2025`, `school_year_2025-2026` |
| `Enrollment.grade_level.name` | `grade_level` | categorical `grade_level` | `grade_level_Grade 10`, `grade_level_Grade 4`, `grade_level_Grade 5`, `grade_level_Grade 6`, `grade_level_Grade 7`, `grade_level_Grade 8`, `grade_level_Grade 9` |
| `Enrollment.section.name` | `section` | categorical `section` | `section_A`, `section_B`, `section_C`, `section_D` |
| `BehavioralAssessment.core_value.name` | `behavior_core_value` | categorical `behavior_core_value` | `behavior_core_value_Compassion`, `behavior_core_value_Excellence`, `behavior_core_value_Integrity`, `behavior_core_value_Respect`, `behavior_core_value_Responsibility` |
| `BehavioralAssessment.behavior_indicator.name` | `behavior_indicator` | categorical `behavior_indicator` | `behavior_indicator_Completes assignments on time`, `behavior_indicator_Demonstrates effort and perseverance`, `behavior_indicator_Displays kindness and empathy`, `behavior_indicator_Practices honesty`, `behavior_indicator_Shows respect to teachers and peers` |
| most common `BehavioralAssessment.rating.code` | `behavior_teacher_rating` | categorical `behavior_teacher_rating` | `behavior_teacher_rating_AO`, `behavior_teacher_rating_NO`, `behavior_teacher_rating_RO`, `behavior_teacher_rating_SO` |
| latest `Intervention.intervention_type`, or no intervention | `intervention_type` | categorical `intervention_type` | `intervention_type_Academic Monitoring`, `intervention_type_Attendance Monitoring`, `intervention_type_Behavioral Monitoring`, `intervention_type_Counseling`, `intervention_type_Guidance Referral`, `intervention_type_Mentoring`, `intervention_type_Parent/Guardian Conference`, `intervention_type_Tutoring`, `intervention_type_Unknown` |
| no persisted outcome field; service default | `intervention_outcome` | categorical `intervention_outcome` | `intervention_outcome_Improved`, `intervention_outcome_No Change`, `intervention_outcome_Not Yet Evaluated`, `intervention_outcome_Ongoing`, `intervention_outcome_Unknown`, `intervention_outcome_Worsened` |

The encoded feature order is the 20 numeric fields above, then the 42 one-hot fields in the category order listed in `feature_mapping.json`.

## 4. Subject Vocabulary Findings

`Subject` is grade-level aware and supports Elementary, Junior High School, and Senior High School structures. The current database therefore can contain subjects that differ by educational level. The saved model is fixed to eight synthetic learning-area names and has no `EDUCATION` feature.

`EDUCATION` is a real current subject value, not evidence that the record should be Mathematics or another learning area. It is not silently converted. The service now reports, for example: `Subject 'EDUCATION' is not represented in the current model vocabulary; grade 99.0 was not encoded.` Prediction is blocked until a compatible contract exists.

Recognized subject names continue to populate their corresponding numeric features. No subject taxonomy was changed and no model artifact was expanded.

## 5. Academic-Year Findings

The model vocabulary contains only `2024-2025` and `2025-2026`. `New School Year` cannot safely be mapped to either value. It is now reported as an incompatible categorical value and is not arbitrarily encoded.

## 6. Grade-Level Findings

The model vocabulary contains `Grade 4` through `Grade 10`. Current academic structure includes Elementary `Grade 1` through `Grade 6` and Senior High School `Grade 11` and `Grade 12`. `Grade 1` is not mapped to Grade 4 or any other level. It is reported and prediction is blocked for that row.

## 7. Section Findings

The model vocabulary contains sections `A`, `B`, `C`, and `D`. `Moonstone` is a valid current section name but is not representable by this artifact. It is reported and is not mapped to an arbitrary section.

## 8. Behavior Mapping

The application preserves the authoritative source rating codes exactly: `AO`, `SO`, `RO`, and `NO`. The persisted model order is verified as:

1. `behavior_teacher_rating_AO`
2. `behavior_teacher_rating_NO`
3. `behavior_teacher_rating_RO`
4. `behavior_teacher_rating_SO`

The current DepEd Core Values and indicators are not falsely mapped to legacy model categories. Their source names remain in `feature_values`; if they are outside the persisted vocabulary, the service records a diagnostic and refuses inference. The old hard-coded `Respect` and `Shows respect to teachers and peers` defaults were removed. Core Value and indicator slots are used by the model, but the current source vocabulary is not compatible with those slots without retraining or an approved mapping.

## 9. Intervention Mapping

The current service now uses the latest persisted intervention type instead of always using `Academic Monitoring`. With no intervention rows:

- `has_intervention = 0`
- `number_of_interventions = 0`
- `intervention_type = Unknown`, which is an existing persisted training vocabulary slot
- `intervention_outcome = Not Yet Evaluated`

`No Intervention` is not sent as a categorical value because it is absent from the persisted vocabulary. The numeric fields remain logically consistent. The application does not claim that `Unknown` is a new learned no-intervention category; this is the documented compatibility fallback available in the unchanged artifact. A future retraining contract should add an explicit no-intervention category if that distinction is required.

The application model has intervention status but no separate persisted intervention outcome. Therefore `intervention_outcome` remains `Not Yet Evaluated` rather than inventing a status-to-outcome meaning.

## 10. Unknown-Category Handling

`build_feature_vector()` now attaches `contract_diagnostics` to the returned source values. Diagnostics identify unmapped subjects and unknown categorical values, including the value that would otherwise activate an all-zero group. `validate_feature_frame()` verifies:

- exactly 62 columns;
- exact saved model feature names and order;
- numeric/coercible finite values with no missing values;
- all source categorical values are recognized or explicitly handled;
- no valid subject grade is silently discarded.

`predict_for_student()` calls this validation before `predict()` or `predict_proba()`. Incompatible data produces HTTP 422 with a safe general error and structured domain diagnostics. Diagnostics are also logged server-side. Normal users do not receive model internals or serialized artifact details.

## 11. Changes Made

- Added `FeatureContractError` and pre-inference feature validation.
- Replaced silent unknown one-hot behavior with structured diagnostics and blocked unsafe inference.
- Preserved unrecognized subject grades in diagnostics rather than silently treating them as valid zeroes.
- Removed false legacy behavior defaults and preserve actual source values.
- Used actual latest intervention type and explicit `Unknown` for no intervention.
- Corrected prediction-factor wording: global feature importance is described as influential, not causal; factor direction is `Informational`, not `Positive`.
- Surfaced the safe prediction-unavailable message beside the generation action and kept detailed contract diagnostics out of normal-user UI errors.
- Added focused regression coverage.
- No migrations were created. No SQLite data, passwords, users, predictions, factors, or model artifacts were changed.

## 12. Tests

Focused prediction suite: 19 tests passed. Coverage includes recognized grades, `EDUCATION=99` diagnostics, unknown academic year/grade/section diagnostics, no-intervention consistency, AO/SO/RO/NO one-hot order, exact 62-feature order, full model inference/persistence, duplicate prevention, authorization, and historical factor immutability.

Validation completed so far:

- behavior and academic tests: **153 passed**;
- focused prediction tests: **19 passed**;
- full Django suite: **203 passed**;
- frontend production build: **passed** with the existing large-chunk warning;
- `makemigrations --check --dry-run`: reports pre-existing drift in `academics` (`0007_section_academics_s_strand__9275c2_idx`) and `accounts` (`0002_alter_userprofile_role_name`); no migration was created.
- modified-file diagnostics: no errors;
- `git diff --check`: passed (only existing line-ending warnings from unrelated files).

## 13. Browser Validation

Authenticated browser validation was performed with `test1` using the existing Student 8 record. The UI showed the academic grade `99.00`, two 100% attendance rows, and five AO behavior assessments, including current DepEd Core Values and indicators. The existing prediction remained visible after refresh with probability `52%`, risk `High`, Random Forest, and five factors.

Generating again returned HTTP 422 because Student 8 contains `EDUCATION`, `New School Year`, `Grade 1`, `Moonstone`, and current behavior vocabulary that the unchanged artifact cannot represent. The retry did not create a new prediction: the database remained at one prediction and five factors for the student. The live database contains no fully compatible existing student for a successful new browser inference; creating or modifying records solely for this test was intentionally avoided.

## 14. AI Impact

Structural compatibility remains intact: the saved Random Forest still receives 62 columns in the exact expected order for compatible rows. Semantic compatibility is now enforced rather than assumed. For incompatible current-domain rows, no model prediction is produced, which is safer than returning a structurally valid but semantically misleading result.

Model prediction itself remains unchanged for a compatible vector. Explanation quality is improved only in wording: global feature importance is not presented as an individual causal contribution. Real-world reliability remains unproven because the model was trained on synthetic data with synthetic category distributions and labels.

## 15. Whether Retraining Is Required

Retraining is not performed in this sprint. It is required before the model can reliably represent current Elementary/JHS/SHS subject taxonomies, current DepEd Core Values and indicators, `Grade 1`, `Moonstone`, `New School Year`, and any explicit no-intervention distinction. An approved vocabulary and data-contract design should precede retraining.

## 16. Remaining Limitations

- The saved model cannot safely infer for all current school values; the API now exposes that limitation instead of hiding it.
- `excused_absences` has no current database source and remains zero.
- Intervention outcomes are not persisted as a separate field.
- A single most-common behavior rating is used when multiple assessments exist.
- Global Random Forest feature importance is still not a per-student contribution method.
- Synthetic training data and injected label noise limit claims about real-world accuracy.

## 17. Final Recommendation

Keep the unchanged model artifact for structurally compatible regression tests only. Do not present predictions for rows with unresolved contract diagnostics as reliable student-risk assessments. Approve a separate data-contract and retraining effort that defines current subject taxonomy, academic context vocabularies, DepEd behavior vocabulary, intervention outcome/no-intervention semantics, and validation data before replacing or retraining the Random Forest.

The feature construction layer is now explicit about what it can and cannot represent. The AI is not declared fixed: structural safety and semantic diagnostics are repaired, while model validity for the current school domain remains unresolved.

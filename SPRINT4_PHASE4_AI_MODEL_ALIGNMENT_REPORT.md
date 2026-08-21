# Sprint 4 Phase 4: AI Training Data and Model Contract Alignment

## 1. Problem

Phase 3 correctly rejected inference when current database values were outside the persisted model vocabulary. The old training artifacts still described a different domain: eight subject slots omitted `EDUCATION`, behavior categories were legacy values instead of the DepEd source vocabulary, academic context was narrow, and preprocessing could mark explicit no-intervention rows as having an intervention.

## 2. Existing AI Architecture

The application still uses scikit-learn `RandomForestClassifier`, pandas preprocessing, `PredictionService`, `ExplanationService`, `RiskPrediction`, `PredictionFactor`, the existing prediction endpoint, authorization, and audit logging. The model is persisted as `AI (ML)/models/risk_model.pkl`, with `label_encoder.pkl` and `feature_mapping.json` generated from the same preprocessing run.

## 3. Previous Phase 3 Findings

Phase 3 proved that unknown categories and unsupported subjects must not become silent all-zero groups. Its HTTP 422 behavior and no-persistence safety remain in place. This phase changes the contract and artifacts, but does not remove that validation gate.

## 4. Actual Database Vocabulary

**VERIFIED from the current SQLite database:** academic years include `Current`, `2026-2027`, `2025-2026`, and generated test variants; grade levels include `Grade 3 - Garnet`, `Grade 9`, `Grade 12 - Garnet`, and generated Grade 11 variants; sections include `Garnet`, `9A`, `9B`, several generated A sections, and Grade 12 section names; subjects include `English 9`, `ESP`, `filipino`, `Mathematics`, `Mathematics 9`, and `Science 9`; current rows contain `Discipline` and `Respect` core values with `Compliance with school rules` and `Respectful Behavior`; ratings are `AO`, `SO`, `RO`, `NO`; no intervention rows currently exist.

**VERIFIED:** the current database contains no Student 8. The prior Student 8 values (`EDUCATION`, `Grade 1`, `Moonstone`, `New School Year`, DepEd behavior records) are retained as Phase 3 investigation evidence, not as a live row in this SQLite snapshot.

**LIMITATION:** many live values are test/fixture variants and are not an approved school-domain taxonomy. They were not all promoted into the canonical contract merely because they exist in the database.

## 5. Training Vocabulary

The regenerated contract contains academic years `2025-2026`, `2026-2027`, `Current`, and `New School Year`; grades `Grade 1` through `Grade 12`; sections `A` through `D` and `Moonstone`; the four DepEd Core Values and seven indicators from `behavior/reference_data.py`; exact ratings `AO`, `NO`, `RO`, `SO`; all intervention choices plus `No Intervention`; and intervention outcomes `Improved`, `No Change`, `Not Yet Evaluated`, `Ongoing`, and `Worsened`.

## 6. Final Canonical Feature Contract

The contract is checked in at `AI (ML)/models/canonical_feature_contract.json`. Both generation/preprocessing and runtime inference consume the generated `AI (ML)/models/feature_mapping.json` derived from it. Unknown categorical values use the explicit `reject` policy.

The final model has `71` features: `21` numeric fields followed by one-hot categorical fields. `education_grade` is a first-class numeric feature. Runtime uses the same subject map and case-insensitive matching; unsupported subjects still produce contract diagnostics and block prediction.

## 7. Feature-by-Feature Mapping

| Source | Canonical representation | Unknown policy |
|---|---|---|
| Enrollment academic year | `school_year` categorical | Reject |
| Enrollment grade level | `grade_level` categorical | Reject |
| Enrollment section | `section` categorical | Reject |
| Subject Mathematics / Mathematics 9 | `mathematics_grade` | Reject |
| Subject English / English 9 | `english_grade` | Reject |
| Subject Science / Science 9 | `science_grade` | Reject |
| Subject Filipino / case-normalized filipino | `filipino_grade` | Reject |
| Subject Araling Panlipunan | `araling_panlipunan_grade` | Reject |
| Subject ESP, MAPEH, TLE | matching numeric grade slot | Reject |
| Subject EDUCATION | `education_grade` | Reject if another subject is encountered |
| Current DepEd Core Value | exact `behavior_core_value` | Reject |
| Current DepEd indicator | exact `behavior_indicator` | Reject |
| Rating | exact AO/SO/RO/NO code | Reject |
| Intervention rows | latest `intervention_type`; count and boolean from actual rows | Reject |
| No intervention rows | `No Intervention`, `has_intervention=0`, count `0` | Explicit category |
| Intervention outcome | `Not Yet Evaluated` because no persisted outcome field exists | Explicit default |
| Missing excused absence source | numeric `0` | Documented limitation |

Aliases were added only for observed same-learning-area names such as `Mathematics 9`, `English 9`, `Science 9`, and case variation in `filipino`. `EDUCATION` is not renamed to another learning area; it has its own feature.

## 8. Training Dataset Changes

The generator now reads the canonical contract, generates `education_grade`, includes it in the average and high-grade count, generates DepEd Core Value/indicator values, and writes explicit `No Intervention` and `Not Yet Evaluated` values. Preprocessing uses the same fixed categorical lists and carries the subject map into the runtime mapping. The no-intervention derivation bug is fixed.

Generated dataset: `1000` rows, `448 At Risk`, `552 Not At Risk`, no duplicate IDs. The dataset remains synthetic and is not evidence of real-world model accuracy.

## 9. Label-Generation Criteria

The existing documented synthetic rule was preserved: general average, absences, lateness, behavior rating, intervention presence, and failed subjects contribute to a score; score `>=4` is `At Risk`. No adviser-approved external criteria were found in the repository. The rule is therefore documented as synthetic label logic, not a discovered causal rule.

## 10. Decision Regarding Random Label Flipping

Random label flipping was removed. The repository contained no approved justification for stochastic corruption, while its documentation described a deterministic rule. Removing it makes labels reproducible and faithful to the only documented synthetic criterion. This does not make the labels real-world truth.

## 11. Model Training Configuration

The retained production algorithm is `RandomForestClassifier(n_estimators=200, random_state=42)`. The training comparison still runs Decision Tree and Logistic Regression for reference, but persistence is explicitly forced to Random Forest. The model, label map, and feature mapping were regenerated together.

## 12. Model Evaluation Metrics

**SYNTHETIC, VERIFIED:** 800 training rows and 200 test rows.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Random Forest | 0.9850 | 1.0000 | 0.9667 | 0.9831 | 0.9995 |
| Decision Tree | 0.9850 | 0.9780 | 0.9889 | 0.9834 | 0.9854 |
| Logistic Regression | 0.9400 | 0.9535 | 0.9111 | 0.9318 | 0.9923 |

The Random Forest confusion matrix is not emitted by the current comparison CSV; the evaluation script records it in its in-memory result only. This is a reporting gap, not a claim that the metric was independently re-derived here.

## 13. Old Model vs New Model

Old model: `62` features, legacy behavior vocabulary, Grade 4-10, A-D, no `EDUCATION` slot, and accidental no-intervention semantics.

New model: `71` features, current contract categories, Grade 1-12, explicit `education_grade`, explicit `No Intervention`, and strict runtime mapping. Direct numeric comparison of model quality is not meaningful because the feature contract and label data changed.

## 14. Feature Count and Ordering

**VERIFIED:** preprocessing output, `feature_mapping.json`, and `risk_model.pkl.feature_names_in_` agree on `71` columns in the same order. The numeric prefix is followed by the categorical one-hot groups in mapping order. Runtime validation compares against model feature names and `n_features_in_` rather than a stale hard-coded count.

## 15. Student 8 Feature Representation

**INFERRED from Phase 3 evidence, not live-verified in this database:** `EDUCATION=99` maps to `education_grade=99.0`; it is no longer silently discarded. `Grade 1`, `Moonstone`, `New School Year`, and current DepEd behavior values are represented by the canonical vocabulary. Student 8 was not recreated or modified for testing.

## 16. Student 8 Prediction

**LIMITATION:** no Student 8 exists in the current SQLite database, so no new browser prediction was generated in this phase. No expected classification was forced.

## 17. Good-Student and At-Risk Validation

The generated synthetic test set contains both classes and the Random Forest evaluation covers both labels. The focused Django tests exercise successful inference for a low-grade case and persistence/duplicate behavior. A dedicated live-domain good/at-risk browser pair could not be completed because the current database does not contain the previously referenced Student 8 and no test records were to be fabricated for browser claims.

## 18. Explanation and Factor Behavior

The existing explanation behavior remains global feature importance, not individual causal contribution. Runtime wording continues to call factors influential/informational and does not claim that a feature caused an individual outcome.

## 19. Authorization Validation

The focused prediction suite verifies that a teacher cannot generate a prediction for an unrelated student. Existing centralized authorization and audit paths were not removed.

## 20. Regression Results

**VERIFIED:** focused prediction suite: `20 passed`. This includes supported EDUCATION, unsupported-subject rejection, current-domain academic categories, explicit no-intervention, rating-code compatibility, exact runtime/model columns, persistence, duplicate prevention, audit behavior, and authorization.

Full backend, behavior, academic, attendance, intervention, frontend build/lint, browser, migration, and diagnostics suites were not rerun after this artifact replacement in this session. They remain required before release closure.

## 21. Browser Validation

**NOT COMPLETED:** browser validation was not honestly possible against Student 8 because the live database has no such student. Existing shared browser pages point at `/students/8`, but the current database query returned no row. No account reset or fabricated browser fixture was used.

## 22. Limitations

- The dataset remains synthetic.
- Current SQLite vocabulary includes fixture-generated values and does not establish an adviser-approved production taxonomy.
- Subject aliases are limited to observed same-learning-area names; unsupported subjects remain rejected.
- `excused_absences` has no current source field.
- Intervention outcomes are not persisted separately.
- Global feature importance is not per-student causality.
- Existing migration drift is unrelated and was not changed.

## 23. Final Recommendation

The implementation establishes a shared, strict, reproducible training/runtime contract and preserves Phase 3 safety. It is not ready to be called production-valid until the school approves the canonical vocabulary, real labeled data replaces synthetic labels, the full regression suite is rerun, and browser validation is performed against valid current-domain records. Do not interpret the synthetic metrics as operational accuracy.

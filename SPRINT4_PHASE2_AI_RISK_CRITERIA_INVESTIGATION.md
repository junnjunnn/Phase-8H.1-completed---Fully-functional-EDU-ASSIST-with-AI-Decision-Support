# Sprint 4 Phase 2: AI Risk Criteria Investigation

## Scope and Safety

This is an investigation of the existing implementation and persisted artifacts. The SQLite database, Student 8 records, model file, feature mapping, threshold behavior, and training data were not modified. No model was retrained.

## 1. Current Prediction Result

Student 8's current UI result was:

- General average: `99.0`
- Attendance rate: `100.0%`
- Behavior rating: `AO` (Always Observed)
- Displayed prediction: `At Risk`
- Displayed probability: `52%`
- Model: Random Forest
- Stored prediction: `RiskPrediction` ID `3`, risk level `High`, probability `0.5150`
- Stored factors: five

The live service reconstruction produced the same raw result and a `(1, 62)` feature frame.

## 2. Prediction Path

The active path is:

`POST /api/predictions/predict/<student_id>/` -> `predict_student_view()` -> `PredictionService.predict_for_student()` -> `build_feature_vector()` -> persisted Random Forest -> `ExplanationService` -> `RiskPrediction` and `PredictionFactor`.

Relevant implementation files are [prediction_service.py](BACKEND/predictions/services/prediction_service.py), [explanation_service.py](BACKEND/predictions/services/explanation_service.py), [predictions/models.py](BACKEND/predictions/models.py), and [views.py](BACKEND/predictions/views.py).

## 3. Exact Model Input for Student 8

The service selects Student 8's latest enrollment, ID `9`, school year `New School Year`, grade `Grade 1`, section `Moonstone`.

The table gives the feature name, runtime source value, and exact encoded value supplied to the model. For one-hot columns, the source value is the category represented by that column when it is `1`; `0` means that category was not selected.

### Numeric features (features 1-20)

| # | Feature | Runtime value | Encoded value |
|---:|---|---:|---:|
| 1 | mathematics_grade | 0.0 | 0.0 |
| 2 | english_grade | 0.0 | 0.0 |
| 3 | science_grade | 0.0 | 0.0 |
| 4 | filipino_grade | 0.0 | 0.0 |
| 5 | araling_panlipunan_grade | 0.0 | 0.0 |
| 6 | esp_grade | 0.0 | 0.0 |
| 7 | mapeh_grade | 0.0 | 0.0 |
| 8 | tle_grade | 0.0 | 0.0 |
| 9 | general_average | 99.0 | 99.0 |
| 10 | failed_subjects | 0 | 0.0 |
| 11 | present_days | 2 | 2.0 |
| 12 | absent_days | 0 | 0.0 |
| 13 | late_days | 0 | 0.0 |
| 14 | excused_absences | 0 (service default; DB field does not exist) | 0.0 |
| 15 | attendance_rate | 100.0 | 100.0 |
| 16 | absent_percentage | 0.0 | 0.0 |
| 17 | late_percentage | 0.0 | 0.0 |
| 18 | high_grade_count | 1 | 1.0 |
| 19 | has_intervention | 0 | 0.0 |
| 20 | number_of_interventions | 0 | 0.0 |

Student 8 has one academic record, subject name `EDUCATION`, grade/final grade `99.00`. The runtime subject map recognizes only `Mathematics`, `English`, `Science`, `Filipino`, `Araling Panlipunan`, `ESP`, `MAPEH`, and `TLE`; therefore the `EDUCATION` record is not copied into any subject-grade feature. `general_average` is still calculated from the record, which creates the inconsistent combination of average `99` and eight subject grades of `0`.

### One-hot features (features 21-62)

| # | Feature | Runtime category/value | Encoded value |
|---:|---|---|---:|
| 21 | school_year_2024-2025 | `New School Year` (unlisted) | 0 |
| 22 | school_year_2025-2026 | `New School Year` (unlisted) | 0 |
| 23 | grade_level_Grade 10 | `Grade 1` (unlisted) | 0 |
| 24 | grade_level_Grade 4 | `Grade 1` (unlisted) | 0 |
| 25 | grade_level_Grade 5 | `Grade 1` (unlisted) | 0 |
| 26 | grade_level_Grade 6 | `Grade 1` (unlisted) | 0 |
| 27 | grade_level_Grade 7 | `Grade 1` (unlisted) | 0 |
| 28 | grade_level_Grade 8 | `Grade 1` (unlisted) | 0 |
| 29 | grade_level_Grade 9 | `Grade 1` (unlisted) | 0 |
| 30 | section_A | `Moonstone` (unlisted) | 0 |
| 31 | section_B | `Moonstone` (unlisted) | 0 |
| 32 | section_C | `Moonstone` (unlisted) | 0 |
| 33 | section_D | `Moonstone` (unlisted) | 0 |
| 34 | behavior_core_value_Compassion | service model default is `Respect` | 0 |
| 35 | behavior_core_value_Excellence | service model default is `Respect` | 0 |
| 36 | behavior_core_value_Integrity | service model default is `Respect` | 0 |
| 37 | behavior_core_value_Respect | service model default is `Respect` | 1 |
| 38 | behavior_core_value_Responsibility | service model default is `Respect` | 0 |
| 39 | behavior_indicator_Completes assignments on time | service model default is `Shows respect to teachers and peers` | 0 |
| 40 | behavior_indicator_Demonstrates effort and perseverance | service model default is `Shows respect to teachers and peers` | 0 |
| 41 | behavior_indicator_Displays kindness and empathy | service model default is `Shows respect to teachers and peers` | 0 |
| 42 | behavior_indicator_Practices honesty | service model default is `Shows respect to teachers and peers` | 0 |
| 43 | behavior_indicator_Shows respect to teachers and peers | service model default is `Shows respect to teachers and peers` | 1 |
| 44 | behavior_teacher_rating_AO | `AO` | 1 |
| 45 | behavior_teacher_rating_NO | `AO` | 0 |
| 46 | behavior_teacher_rating_RO | `AO` | 0 |
| 47 | behavior_teacher_rating_SO | `AO` | 0 |
| 48 | intervention_type_Academic Monitoring | `No Intervention` (unlisted) | 0 |
| 49 | intervention_type_Attendance Monitoring | `No Intervention` (unlisted) | 0 |
| 50 | intervention_type_Behavioral Monitoring | `No Intervention` (unlisted) | 0 |
| 51 | intervention_type_Counseling | `No Intervention` (unlisted) | 0 |
| 52 | intervention_type_Guidance Referral | `No Intervention` (unlisted) | 0 |
| 53 | intervention_type_Mentoring | `No Intervention` (unlisted) | 0 |
| 54 | intervention_type_Parent/Guardian Conference | `No Intervention` (unlisted) | 0 |
| 55 | intervention_type_Tutoring | `No Intervention` (unlisted) | 0 |
| 56 | intervention_type_Unknown | `No Intervention` (unlisted) | 0 |
| 57 | intervention_outcome_Improved | `Not Yet Evaluated` | 0 |
| 58 | intervention_outcome_No Change | `Not Yet Evaluated` | 0 |
| 59 | intervention_outcome_Not Yet Evaluated | `Not Yet Evaluated` | 1 |
| 60 | intervention_outcome_Ongoing | `Not Yet Evaluated` | 0 |
| 61 | intervention_outcome_Unknown | `Not Yet Evaluated` | 0 |
| 62 | intervention_outcome_Worsened | `Not Yet Evaluated` | 0 |

The five behavior records are all `AO`, but the runtime deliberately uses persisted model defaults for core value and indicator. Their source values remain available only in the non-encoded explanation values.

## 4. Model Metadata and Raw Output

The unmodified [risk_model.pkl](AI%20(ML)/models/risk_model.pkl) loads as `sklearn.ensemble._forest.RandomForestClassifier`.

- Algorithm: `RandomForestClassifier`
- `n_estimators`: `200`
- `classes_`: `[0, 1]`
- `n_features_in_`: `62`
- `feature_names_in_`: exactly the 62 names listed above, in the same order
- `criterion`: `gini`
- `max_depth`: `None`
- `min_samples_split`: `2`
- `min_samples_leaf`: `1`
- `max_features`: `sqrt`
- `class_weight`: `None`
- `bootstrap`: `True`
- `random_state`: `42`

For Student 8:

```text
predict()       -> [1]
predict_proba() -> [[0.485, 0.515]]
```

The persisted label map in `label_encoder.pkl` is `{0: "Not At Risk", 1: "At Risk"}`. Therefore the raw class `1` is directly mapped to `At Risk`; the application does not transform another class into that label.

## 5. Classification and Probability Rules

The service calls `model.predict(feature_frame)` and maps `0` to `Not At Risk` and `1` to `At Risk`. There is no application probability threshold, custom score, rule-based override, or hybrid logic. The probability is selected as `predict_proba()[0][prediction]`; for Student 8, predicted class `1` selects the second probability, `0.515`, displayed as approximately `52%`.

The persistence layer maps `At Risk` to database `risk_level=High` and every other service result to `Low`. The service does not generate the database `Moderate` level. Thus the system has two model output classes (`Not At Risk`, `At Risk`) but the database choice field has an unused `Moderate` option for this path.

## 6. Five Stored Prediction Factors

Student 8's five factors are stored in `PredictionFactor` ID records for prediction `3`:

| Factor name | Category/impact | Value | Contribution | Explanation |
|---|---|---:|---:|---|
| Attendance Rate | Positive | 100 | 0.0493 | Attendance Rate had low influence with value 100. |
| ESP Grade | Positive | 0 | 0.0490 | ESP Grade had low influence with value 0. |
| Failed Subjects | Positive | 0 | 0.0708 | Failed Subjects had low influence with value 0. |
| General Average | Positive | 99 | 0.1151 | General Average had moderate influence with value 99. |
| Teacher Behavior Rating (AO) | Positive | 1 | 0.0595 | Teacher Behavior Rating (AO) had low influence with value 1. |

These are not local causal contributions. `ExplanationService` ranks the model's global `feature_importances_`, takes the top five positive features, and reports their current values. The `Positive` direction is assigned whenever importance is at least `0.03`; it does not mean the feature increased risk. Consequently, the five factors do not explain why this individual row crossed a risk boundary. In particular, the application stores global importance as `contribution`, not a per-student contribution score.

## 7. Training Labels and Criteria

The repository contains the generator, dataset, preprocessing artifacts, and training script. [generate_synthetic_dataset.py](AI%20(ML)/dataset/generate_synthetic_dataset.py) assigns the target as follows:

```text
risk_score = 0
general_average < 78:       +2
general_average < 85:       +1
absent_days >= 4:            +2
absent_days >= 2:            +1
late_days >= 5:              +1
behavior RO or NO:          +2
behavior SO:                +1
intervention present:       +1
failed_subjects >= 1:       +1
risk_status = At Risk when risk_score >= 4; otherwise Not At Risk
```

After that rule, the generator randomly flips 8% of `Not At Risk` labels to `At Risk` and 12% of `At Risk` labels to `Not At Risk`. The target was not manually assigned and was not based only on general average. The training script compares models and saves the best ROC-AUC model, with the current saved Random Forest configured for 200 estimators. The dataset is synthetic; no historical student performance feature or previous grading-period feature is actually included in the 62-feature model contract.

## 8. Feature Mapping and Preprocessing Verification

Verified facts:

- The persisted mapping declares eight categorical source columns and twenty numeric source columns.
- The mapping declares 62 encoded columns.
- The runtime frame has 62 columns and its names/order exactly match `model.feature_names_in_`.
- Runtime numeric values are coerced with `pd.to_numeric(..., errors='coerce').fillna(0)`.
- Runtime missing numeric values and absent `excused_absences` are represented as `0`.
- Runtime categorical values are matched against the persisted category lists; an unknown value activates no one-hot column.
- Training preprocessing uses numeric columns first followed by one-hot categorical columns, matching the saved model's actual feature names/order.

The contract is therefore structurally compatible but semantically mismatched for Student 8:

1. The application database has `New School Year`, `Grade 1`, and `Moonstone`, while training categories cover only the values in `feature_mapping.json`; all corresponding school-year, grade-level, and section one-hot groups are zero.
2. The database subject is `EDUCATION`, but runtime subject mapping has no `EDUCATION` entry; all eight subject-grade inputs are zero despite the 99 grade.
3. `No Intervention` is the runtime no-intervention value but is not one of the persisted intervention categories, so all intervention-type one-hot inputs are zero. `has_intervention=0` and `number_of_interventions=0` still represent no intervention numerically.
4. Actual behavior core-value and indicator records are not sent to their source categories; the service always sends model defaults `Respect` and `Shows respect to teachers and peers` for the encoded slots. The AO rating itself is compatible and encoded correctly.

There are no previous grading-period or historical-performance features in the model input, and there are no intervention-history features beyond current intervention existence/count and the categorical placeholders.

## 9. Root-Cause Classification

**Primary classification: B. FEATURE CONSTRUCTION BUG.**

The model received a 62-column frame in the right structural order, but several values were not faithful representations of the current database record. Most importantly, the only subject grade (`EDUCATION=99`) was discarded from all subject-grade features and replaced by zeros. Several categorical values were also outside the training vocabulary and encoded as all zeros. This is sufficient evidence that the model was not evaluated on the intended representation of Student 8.

There is also a secondary **E. MODEL PERFORMANCE/LIMITATION** concern: the model was trained on synthetic data and its label generator includes random flips. Even with a corrected feature contract, the model is not evidence of a reliable real-world risk assessment. The present result should not be classified as expected model behavior because the input construction defect occurs first.

The explanation is additionally misleading (**D. DISPLAY/EXPLANATION BUG** as an explanation limitation, not the root cause): the UI/factors present global feature importance as if it were a reason for this prediction, and label the direction `Positive` based only on importance magnitude. The raw prediction and probability themselves are correctly represented.

## 10. Answer: Why Student 8 Was At Risk

Student 8 received `At Risk` because the Random Forest actually saw class-1-indicating inputs including eight subject grades of `0.0`, rather than the intended `EDUCATION=99` subject value, plus all-zero one-hot groups for the current school year, grade level, section, and no-intervention category. With that constructed vector, the unmodified model returned class `1` with probability `0.515`. The displayed 52% is the class-1 (`At Risk`) probability. The visible `99`, `100%`, and `AO` values do not describe the complete vector supplied to the model.

## 11. Actual EDU ASSIST AI Criteria

At application runtime, classification is exactly:

- `predict() == 0` -> `Not At Risk` -> database risk level `Low`.
- `predict() == 1` -> `At Risk` -> database risk level `High`.
- No probability threshold is applied.
- `Moderate` is not produced by this prediction service.

The model learned from 62 inputs: eight subject grades, general average, failed-subject count, attendance counts/rates/percentages, high-grade count, intervention existence/count, and one-hot school-year, grade-level, section, behavior core-value, behavior indicator, behavior rating, intervention type, and intervention outcome. The repository's explicit training-label criteria were the weighted score listed in Section 7, with the documented random label flips. Those are the available target-generation criteria; the trained Random Forest itself does not expose a single human-readable rule equivalent to that score.

## 12. Validation and Recommended Next Step

Validation completed without AI artifact changes:

- Dedicated prediction suite: **14/14 passed**.
- Confirmed 62 feature columns and exact model feature-name/order match.
- Confirmed model loads and raw `predict`/`predict_proba` output.
- Confirmed AO, SO, RO, and NO compatibility through the existing tests.
- Confirmed prediction endpoint, persistence, factors, audit logging, and unauthorized-student rejection through the existing tests.
- Broader `manage.py test predictions tests`: 20 passed, with two unrelated existing errors in `tests/test_authorization.py` (wrong `Enrollment` import) and `test_advisers_api` (missing user profile setup).

No code fix is required for this investigation report, and no broader AI redesign was implemented. The recommended next step is a separate, explicitly approved feature-contract repair: reconcile subject names and academic categories between the database and training data, define unknown-category and no-intervention behavior deliberately, then evaluate/retrain only after the corrected contract and label strategy are agreed. Do not interpret new predictions for records with unmapped source values as reliable until that work is complete.
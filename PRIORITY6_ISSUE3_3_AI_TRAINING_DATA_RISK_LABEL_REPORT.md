# Priority 6 Issue 3.3 — AI Training Data and Risk-Label Transparency

## A. Training dataset

### Source and pipeline
The actual training pipeline is located in:

- [AI (ML)/dataset/generate_synthetic_dataset.py](AI%20(ML)/dataset/generate_synthetic_dataset.py)
- [AI (ML)/preprocessing/preprocess_dataset.py](AI%20(ML)/preprocessing/preprocess_dataset.py)
- [AI (ML)/training/train_models.py](AI%20(ML)/training/train_models.py)
- [AI (ML)/README.md](AI%20(ML)/README.md)

The dataset used for model training is:

- [AI (ML)/dataset/synthetic_student_dataset.csv](AI%20(ML)/dataset/synthetic_student_dataset.csv)

The project explicitly states that this is a synthetic dataset and not a production school dataset.

### Training record count
The dataset description says:

- approximately 1000 student records
- 800 used for training
- 200 used for testing

The evaluation report confirms:

- Training size: 800
- Testing size: 200

### Feature count and actual model features
The feature matrix used by the trained model is derived in [AI (ML)/preprocessing/preprocess_dataset.py](AI%20(ML)/preprocessing/preprocess_dataset.py), and the loaded model exposes the exact trained feature names via `model.feature_names_in_`.

The live model currently uses these feature columns, in order:

- `mathematics_grade`
- `english_grade`
- `science_grade`
- `filipino_grade`
- `araling_panlipunan_grade`
- `esp_grade`
- `mapeh_grade`
- `tle_grade`
- `education_grade`
- `general_average`
- `failed_subjects`
- `present_days`
- `absent_days`
- `late_days`
- `excused_absences`
- `attendance_rate`
- `absent_percentage`
- `late_percentage`
- `high_grade_count`
- `has_intervention`
- `number_of_interventions`
- `school_year_2025-2026`
- `school_year_2026-2027`
- `school_year_Current`
- `school_year_New School Year`
- `grade_level_Grade 1`
- `grade_level_Grade 2`
- `grade_level_Grade 3`
- `grade_level_Grade 4`
- `grade_level_Grade 5`
- `grade_level_Grade 6`
- `grade_level_Grade 7`
- `grade_level_Grade 8`
- `grade_level_Grade 9`
- `grade_level_Grade 10`
- `grade_level_Grade 11`
- `grade_level_Grade 12`
- `section_A`
- `section_B`
- `section_C`
- `section_D`
- `section_Moonstone`
- `behavior_core_value_Maka-Diyos (Love for God)`
- `behavior_core_value_Makatao (Love for Fellowmen)`
- `behavior_core_value_Maka-Kalikasan (Love for Nature)`
- `behavior_core_value_Makabansa (Love for Country)`
- `behavior_indicator_Expresses one's spiritual beliefs while respecting the spiritual beliefs of others`
- `behavior_indicator_Shows adherence to ethical principles by upholding truth`
- `behavior_indicator_Is sensitive to individual, social, and cultural differences`
- `behavior_indicator_Demonstrate contributions toward solidarity`
- `behavior_indicator_Cares for the environment and utilizes resources wisely, judiciously, and economically`
- `behavior_indicator_Demonstrates pride in being a Filipino; exercises the rights and responsibilities of a Filipino Citizen`
- `behavior_indicator_Demonstrates appropriate behavior in carrying out activities in the school, community, and country`
- `behavior_teacher_rating_AO`
- `behavior_teacher_rating_NO`
- `behavior_teacher_rating_RO`
- `behavior_teacher_rating_SO`
- `intervention_type_Academic Monitoring`
- `intervention_type_Attendance Monitoring`
- `intervention_type_Behavioral Monitoring`
- `intervention_type_Counseling`
- `intervention_type_Guidance Referral`
- `intervention_type_Mentoring`
- `intervention_type_No Intervention`
- `intervention_type_Parent/Guardian Conference`
- `intervention_type_Tutoring`
- `intervention_outcome_Improved`
- `intervention_outcome_No Change`
- `intervention_outcome_Not Yet Evaluated`
- `intervention_outcome_Ongoing`
- `intervention_outcome_Worsened`

### Features actually used by the trained model
The model uses the processed, one-hot encoded features above. In practice, the relevant data categories are:

- academic performance: grades and general average
- academic struggle: failed subjects, high grade count
- attendance: present days, absent days, late days, excused absences, attendance rate, absent percentage, late percentage
- behavior: behavior core value, behavior indicator, teacher rating
- intervention: intervention presence and type
- school context: section, grade level, school year

### Fields present in the app but not used by the trained model
The model preprocessing script intentionally drops or ignores certain fields.

These are not used in the trained model features:

- `teacher_remarks`
- `intervention_date`
- `intervention_reason`
- `improved_after_intervention` (not in the final encoded feature set)
- raw text fields and date fields retained in the application but not in the model contract

The preprocessing script also explicitly discards duplicate student rows and transforms the final training data to a student-snapshot feature matrix. It does not use free-text teacher remarks or date-derived features in the current model.

---

## B. Exact target and risk labels

### Target variable
The training pipeline uses `risk_status` as the target label and then converts it to `risk_label` in preprocessing:

- `At Risk` -> `1`
- `Not At Risk` -> `0`
- `Unknown` -> `-1`

This is implemented in [AI (ML)/preprocessing/preprocess_dataset.py](AI%20(ML)/preprocessing/preprocess_dataset.py).

The model artifact saves the label map in [AI (ML)/training/train_models.py](AI%20(ML)/training/train_models.py):

- `1: 'At Risk'`
- `0: 'Not At Risk'`

This is also confirmed in the backend loader at [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py).

### Exact meaning of the labels
The model predicts a binary class:

- `class 1` = `At Risk`
- `class 0` = `Not At Risk`

This is not `Low / Moderate / High` in the trained model. The saved model returns numeric class values and the application maps them to the display labels.

### How labels were created
The synthetic dataset defined the target label using a weighted risk score in [AI (ML)/dataset/generate_synthetic_dataset.py](AI%20(ML)/dataset/generate_synthetic_dataset.py):

- general average below 78 adds 2 points
- general average below 85 adds 1 point
- absent days >= 4 adds 2 points
- absent days >= 2 adds 1 point
- late days >= 5 adds 1 point
- `RO` or `NO` behavior adds 2 points
- `SO` adds 1 point
- intervention present adds 1 point
- failed subjects >= 1 adds 1 point

Then:

- `risk_status = 'At Risk' if risk_score >= 4 else 'Not At Risk'`

This is the actual training-target rule. It is rule-based, not random.

### Class distribution in the synthetic training set
The dataset description reports:

- Not At Risk: 552
- At Risk: 448

Percentages:

- Not At Risk: 55.2%
- At Risk: 44.8%

This is a mild class imbalance, not an extreme one, but it is still not perfectly balanced.

---

## C. Training process and evaluation

### Preprocessing
The preprocessing script does the following:

- removes duplicate rows by `student_id`
- fills missing numeric values with medians
- clips grades and attendance values to valid ranges
- one-hot encodes categorical values
- derives engineered features:
  - `absent_percentage`
  - `late_percentage`
  - `high_grade_count`
  - `has_intervention`
  - `number_of_interventions`
  - `risk_label`

### Model selection and configuration
The training script compares:

- Decision Tree
- Random Forest
- Logistic Regression

The selected final model is:

- `RandomForestClassifier(random_state=42, n_estimators=200)`

### Evaluation evidence
The actual evaluation report in [AI (ML)/evaluation/model_evaluation.md](AI%20(ML)/evaluation/model_evaluation.md) reports:

- Decision Tree: Accuracy 0.985, Precision 0.978, Recall 0.9889, F1 0.9834, ROC-AUC 0.9854
- Random Forest: Accuracy 0.985, Precision 1.0, Recall 0.9667, F1 0.9831, ROC-AUC 0.9995
- Logistic Regression: Accuracy 0.94, Precision 0.9535, Recall 0.9111, F1 0.9318, ROC-AUC 0.9923

The project explicitly identifies Random Forest as the selected model because it had the highest ROC-AUC.

### Stored evaluation evidence found
Evidence found:

- [AI (ML)/evaluation/model_comparison.csv](AI%20(ML)/evaluation/model_comparison.csv)
- [AI (ML)/evaluation/model_evaluation.md](AI%20(ML)/evaluation/model_evaluation.md)
- [AI (ML)/evaluation/feature_importance.csv](AI%20(ML)/evaluation/feature_importance.csv)

There is no separate independent validation dataset stored beyond the train/test split. The evaluation is a standard train/test split, not a holdout from a separate production dataset.

---

## D. Global feature importance

The Random Forest feature importances are stored in [AI (ML)/evaluation/feature_importance.csv](AI%20(ML)/evaluation/feature_importance.csv).

Top importances are:

1. `general_average` — 0.1709
2. `failed_subjects` — 0.1169
3. `behavior_teacher_rating_AO` — 0.0818
4. `high_grade_count` — 0.0578
5. `attendance_rate` — 0.0476
6. `absent_percentage` — 0.0400
7. `present_days` — 0.0391
8. `absent_days` — 0.0376
9. `mapeh_grade` — 0.0339
10. `education_grade` — 0.0334

This is global feature importance at the dataset level. It does not mean the model has identified a causal explanation for any single student. The current backend explanation text correctly states this distinction.

---

## E. Edizon case: actual live model output

Current student used for investigation:

- name: `edizon Gempesaw`
- student id: 30
- enrollment id: 31

The actual live model run on the current application data produced:

- general_average = 71.86
- failed_subjects = 6
- attendance_rate = 100.0
- high_grade_count = 3
- behavior_teacher_rating = `NO`

The exact current model output from the application was:

- classes = `[0, 1]`
- raw prediction = `1`
- `predict_proba()` = `[0.235, 0.765]`
- probability for predicted class = `0.765` (76.5%)

Because the label map is:

- `0 -> Not At Risk`
- `1 -> At Risk`

the actual interpretation is:

- raw class `1` = `At Risk`
- probability `0.765` corresponds to the `At Risk` class
- the model is currently predicting `At Risk`, not `Low Risk` or `Not At Risk`

This is the exact current live evidence from the saved model and the application feature vector.

### Why the model can still classify a student with poor academic indicators as At Risk
Because the target rule in the synthetic training data is not a strict `General Average < 75 => At Risk` rule. The training label was generated using a weighted risk score from multiple signals, including:

- grade average
- failed subjects
- absences
- lateness
- behavior rating
- interventions
- intervention type/outcome

The actual score logic is a multi-factor composite risk model, not a single academic threshold rule. A student can therefore have poor grades and still be at risk because the model is also learning from attendance, behavior, and intervention patterns, and because the synthetic labels were assigned from that weighted combination rather than from a single academic criterion.

### Why this is not a simple “academic concern” rule
The application has a separate academic rule:

- `General Average below 75` is used for display as an academic concern in the student monitoring UI

But the AI model is not using that as a hard threshold for the target label. The model target was generated from the composite synthetic risk score described above.

This is the key distinction:

- Academic concern rule = monitoring / dashboard interpretation
- AI risk prediction = trained model output based on weighted synthetic risk score

They are not identical.

---

## F. Why the current output may differ from a previous “Low Risk / 57% / Not At Risk” result
The exact older output described in the issue (`Low / 57% / Not At Risk`) does not match the current live application state.

The current live application state for the actual Edizon record produces:

- `At Risk`
- `76.5%`

That means the old result is not the current model output for the actual Edizon record. It likely reflects either:

- a different student state or snapshot at another time;
- older data in a previous run;
- a snapshot that did not match the current model feature vector;
- or a historical report based on a different dataset state.

The current code and model artifact do not support the claim that this student should be `Not At Risk` under the current feature vector.

---

## G. Explanation transparency and model interpretation

The explanation pipeline in [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py) and [BACKEND/predictions/services/explanation_service.py](BACKEND/predictions/services/explanation_service.py) does the following:

- builds the current feature vector from the student’s live records
- validates the vector against the saved model contract
- calls `model.predict_proba()`
- obtains the model’s top feature importances
- stores the highest-ranked features in `PredictionFactor`
- writes the summary text and explanation fields

The generated explanation is therefore:

- global Random Forest feature importance combined with the student’s current feature values
- not a patient-specific causal claim
- not a diagnosis of root cause
- not a direct proof that a feature “caused” this risk outcome

This matches the current implementation and the UI wording: the system is decision support, not causal explanation.

---

## H. Model limitations

The major limitation is that the model is trained on a synthetic dataset rather than real student outcomes. The project documentation itself says this is a synthetic baseline and warns that it should be retrained when real school data becomes available.

Additional limitations:

- The target label is rule-based and synthetic, not a real-world outcome variable.
- The model does not hard-code a `General Average < 75` rule as the decision threshold.
- The model learns a composite risk score from multiple signals rather than a direct academic-failure rule.
- The app’s UI and the model’s output should not be treated as equivalent to a teacher’s academic concern judgment.

---

## I. Alignment assessment

### Conclusion
The current model is best described as:

- functional as a synthetic baseline,
- not fully aligned with a real-world academic-risk definition,
- suitable only as decision support,
- not appropriate as a direct replacement for teacher judgment or academic concern monitoring.

### Evidence
- The synthetic dataset was created with a weighted risk formula, not a direct GPA rule.
- The project explicitly warns that the dataset is synthetic and should be replaced with real data.
- The model is trained on generated patterns rather than verified student outcomes.
- The current live Edizon case shows a multi-factor risk classification rather than a simple academic threshold.

---

## J. Recommendation for future model revision
A future model revision should include:

- real historical student outcomes and teacher-validated risk labels
- explicit labeling rules agreed by school staff
- data collection for actual academic, attendance, behavior, and intervention outcomes
- separate treatment of academic concern versus AI risk prediction
- threshold review and model validation using independent real-world data
- explicit model governance and monitoring for false positives / false negatives

This is a recommendation only; it was not implemented in this issue.

---

## K. Validation performed

The following validations were performed:

1. Backend prediction tests:
   
   ```bash
   Set-Location 'F:\edu_new\BACKEND'; .\venv\Scripts\python.exe manage.py test predictions.tests --keepdb -v 2
   ```
   
   Result: passed

2. Frontend build:
   
   ```bash
   Set-Location 'F:\edu_new\FRONTEND'; npm run build
   ```
   
   Result: passed

3. Git diff check:
   
   ```bash
   Set-Location 'F:\edu_new'; git diff --check
   ```
   
   Result: passed

No dedicated AI/ML model test suite was found beyond the existing Django prediction tests. The investigation therefore relies on the actual training and preprocessing code, the saved model artifact, and the live model output from the application.

---

## L. Files inspected

- [AI (ML)/dataset/generate_synthetic_dataset.py](AI%20(ML)/dataset/generate_synthetic_dataset.py)
- [AI (ML)/dataset/synthetic_student_dataset.csv](AI%20(ML)/dataset/synthetic_student_dataset.csv)
- [AI (ML)/dataset/dataset_description.md](AI%20(ML)/dataset/dataset_description.md)
- [AI (ML)/preprocessing/preprocess_dataset.py](AI%20(ML)/preprocessing/preprocess_dataset.py)
- [AI (ML)/training/train_models.py](AI%20(ML)/training/train_models.py)
- [AI (ML)/evaluation/model_evaluation.md](AI%20(ML)/evaluation/model_evaluation.md)
- [AI (ML)/evaluation/model_comparison.csv](AI%20(ML)/evaluation/model_comparison.csv)
- [AI (ML)/evaluation/feature_importance.csv](AI%20(ML)/evaluation/feature_importance.csv)
- [AI (ML)/models/canonical_feature_contract.json](AI%20(ML)/models/canonical_feature_contract.json)
- [BACKEND/predictions/services/prediction_service.py](BACKEND/predictions/services/prediction_service.py)
- [BACKEND/predictions/services/explanation_service.py](BACKEND/predictions/services/explanation_service.py)

## Final conclusion

The current AI model is not a direct “General Average < 75 => risk” classifier. It is a synthetic, multi-feature Random Forest trained on a composite risk score that includes grades, attendance, behavior, and interventions. The live current Edizon feature vector predicts `At Risk` with a 76.5% probability, and the model’s label map confirms that class `1` corresponds to `At Risk`. The model should therefore be treated as decision support and not as a hard academic failure rule.

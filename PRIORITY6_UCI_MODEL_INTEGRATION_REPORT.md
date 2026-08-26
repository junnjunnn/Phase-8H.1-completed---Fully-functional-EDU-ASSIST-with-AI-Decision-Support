# PRIORITY 6 — UCI Model Integration Report

## A. Dataset files inspected

Files inspected in `AI (ML)/dataset/student_performance`:

- `student-mat.csv`
- `student-por.csv`
- `student.txt`
- `student-merge.R`

## B. Dataset structure

The dataset is a two-course student dataset with 33 columns per row:

- school and family context variables
- personal and home-support factors
- study and social variables
- attendance variable (`absences`)
- grade variables (`G1`, `G2`, `G3`)

The two CSVs are not separate semesters or periods in the EDU ASSIST sense; they are separate subject tables (Math and Portuguese) for the same general student population.

## C. Data quality findings

- `student-mat.csv`: 395 rows, 0 missing values, 0 duplicates
- `student-por.csv`: 649 rows, 0 missing values, 0 duplicates
- No invalid literal values or obvious malformed schema in the raw CSVs
- Data is internally clean, but not aligned with EDU ASSIST’s operational risk schema
- The raw files do not provide a student ID, enrollment record, section, or grade-level context required by the current model contract

## D. Target-label analysis

The dataset has no explicit target of `At Risk` or `Not At Risk`.

The closest outcome label is `G3`, the final subject grade. It is numeric and includes a course performance value, but it is not a risk label for schoolwide student support.

This cannot be mapped safely to EDU ASSIST’s target without inventing a new rule such as:

- `G3 < 10` => At Risk
- `failures > 0` => At Risk
- `absences > threshold` => At Risk

These rules are not evidence-based for this project and would not match the current risk definition or live database semantics. They would also create a target with leakage risk because the grade is part of the same subject-performance process being modeled.

## E. EDU ASSIST feature mapping

| UCI field | EDU ASSIST concept | Existing model feature | Transformation required | Compatibility | Reason |
|---|---|---|---|---|---|
| `school` | School context | not present | none; context only | Incompatible | School is not a live enrollment or school-year model feature in the current production contract |
| `sex` | Demographic attribute | not present | none; demographic only | Incompatible | Not used in the EDU ASSIST risk model and not a live risk signal |
| `age` | Student age | not present | none | Incompatible | No current model feature for age |
| `address` | Home context | not present | none | Incompatible | Not represented in current risk pipeline |
| `Medu` / `Fedu` | Family context | not present | none | Incompatible | No equivalent feature in the model |
| `traveltime`, `studytime` | School access / study effort | not present | none | Incompatible | No current feature contract for these values |
| `failures` | Prior academic struggles | `failed_subjects` | aggregate and threshold | Partially compatible | This is a proxy for academic risk, but not a direct match to EDU ASSIST academic risk logic |
| `absences` | Attendance | `absent_days` / `attendance_rate` | aggregate and map to current attendance schema | Partially compatible | Attendance exists in EDU ASSIST, but UCI does not model periodized school attendance records |
| `G1`, `G2`, `G3` | Subject academic performance | `general_average`, subject grades | map to subject-grade features | Partially compatible | Course grades are similar in concept but not same as EDU ASSIST appraisal fields and not at the same schema level |
| `schoolsup`, `famsup`, `paid` | Support and intervention proxy | `has_intervention`, `number_of_interventions` | convert support flags to intervention indicators | Partially compatible | Conceptually related, but not equivalent to intervention records and teacher action history |
| `higher`, `internet`, `romantic` | Student context | not present | none | Incompatible | No such features in the current model |
| `guardian`, `reason`, `Mjob`, `Fjob` | Family and context variables | not present | none | Incompatible | Not part of current feature contract |

## F. Missing and incompatible fields

The following EDU ASSIST fields are not present in the UCI dataset:

- `student_id` or any stable student key
- `grade_level`
- `section`
- `academic_year`
- `assessment_quarter`
- `behavior_core_value`
- `behavior_indicator`
- `behavior_teacher_rating`
- `intervention_type`
- `intervention_outcome`
- `teacher_remarks`
- `school_year`
- `attendance_records` over multiple terms
- `risk_status`

This means the dataset cannot be mapped into the live model without creating unsupported, synthetic values or a new model schema.

## G. Leakage analysis

The UCI dataset contains serious leakage risks if someone tries to create a target from `G3` or related course grades:

- `G3` is in the same subject-performance family as the input features (`G1`, `G2`, `G3`)
- `failures` is derived from prior academic performance and overlaps with the target concept
- `absences` and support variables may be correlated with academic outcome but are not a valid risk target definition in the current system
- There is no defense against using future-visible information as a target label

There is also no safe “prediction time” equivalence because the dataset lacks the live EDU ASSIST data arrangement where prediction uses current enrollment records rather than course grades from the same subject period.

## H. Compatibility decision

Decision: D. NOT SUITABLE FOR THE CURRENT RISK MODEL

### Why

1. The UCI files do not contain the required student-risk target (`At Risk` / `Not At Risk`).
2. There is no stable student ID or enrollment key.
3. The dataset has no section, grade-level, or academic-period structure that matches the live EDU ASSIST model contract.
4. The data represents course-level performance in Math and Portuguese, not student risk across interventions, attendance, and behavior.
5. The current production model expects a synthetic-feature record built from live enrollment/academic/attendance/behavior/intervention records.
6. A custom target threshold would be invented rather than defensible.

## I. Training methodology

No UCI model training was performed, because the required conditions for safe training were not met.

The project does not have a defensible risk target in the UCI data, so the safe branch was not taken.

## J. Model evaluation

No UCI model evaluation was produced because the dataset failed the target-label viability gate.

A valid training pipeline would require a separate, documented, defensible target definition and feature mapping, but no such target exists here.

## K. Old vs UCI comparison

| Item | Old model | UCI dataset |
|---|---|---|
| Dataset | Synthetic EDU ASSIST training data | UCI course performance data |
| Target definition | `risk_status` = `At Risk` / `Not At Risk` defined by synthetic feature logic | No valid risk target; only subject grade (`G3`) |
| Feature set | academic, attendance, behavior, intervention, context | demographic, family, study habits, absences, grades |
| Preprocessing | explicit model contract and one-hot encoding | not aligned with current feature contract |
| Student identity | stable DB enrollment + student | no true student ID |
| Academic period | supported by EDU ASSIST enrollment model | absent |
| Risk semantics | designed for EDU ASSIST risk monitoring | not a school risk definition |
| Decision | existing production baseline | rejected for current model |

## L. Model artifact locations

No new UCI model artifact was created.

The existing model and mapping remain preserved in:

- `AI (ML)/models/risk_model.pkl`
- `AI (ML)/models/label_encoder.pkl`
- `AI (ML)/models/feature_mapping.json`

## M. Production integration decision

Decision: do not integrate into production.

Requirements for production integration were not satisfied:

- no defensible target
- no documented feature mapping for live EDU ASSIST data
- no reproducible preprocessing contract aligned to the current risk system
- no safe leakage review pass
- no successful model evaluation for EDU ASSIST-compatible risk classes

## N. Prediction explanation implications

Because no UCI model was trained or integrated, there is no new prediction explanation to alter.

The existing explanation language remains limited to the current synthetic model and should continue to avoid causal claims such as:

- “Attendance caused the student to become at risk.”

The recommended wording remains:

- “The model considered attendance among the features that influenced its prediction.”

## O. Tests performed

- Dataset inspection via `pandas` to validate file count, shapes, dtypes, missing values, duplicates, and field ranges
- Schema review against the current model contract in `AI (ML)/models/feature_mapping.json`
- Current backend prediction tests were checked for regression stability
- `git diff --check` was run to validate the report creation and ensure no formatting issues in repository changes

## P. Test results

- UCI schema inspection succeeded and confirmed the actual file contents and limitations
- The UCI dataset failed the safety and compatibility gate for the current risk model
- No model training or production behavior change occurred
- No claims of end-to-end UCI model success are made

## Q. Limitations

- The UCI data is course-level and not aligned with the live EDU ASSIST student-risk workflow
- No valid risk target exists in the raw data
- No stable student identity or enrollment key is supplied
- The dataset does not model current behavior, intervention, or section-level risk structures
- The project must not be forced to use this dataset simply because it is called “student performance” data

## R. Final recommendation

Do not integrate the UCI student-performance dataset into the current EDU ASSIST risk model.

The correct action is to preserve the current synthetic baseline, keep the existing artifact intact, and treat the UCI dataset as a separate future research dataset only if a new, clearly defined target and feature pipeline are intentionally designed for a different project objective.

The data is academically interesting, but it is not trustworthy for the current At Risk / Not At Risk production model without a new, explicit risk-label methodology and a separate training pipeline built around that methodology.

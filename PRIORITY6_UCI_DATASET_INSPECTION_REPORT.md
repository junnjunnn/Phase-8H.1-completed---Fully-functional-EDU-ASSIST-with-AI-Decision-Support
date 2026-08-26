# PRIORITY 6 — UCI Dataset Inspection Report

## Executive summary

The UCI student-performance dataset provided in `AI (ML)/dataset/student_performance` is a classroom performance dataset for two school subjects, not a live EDU ASSIST student-risk dataset. The files contain 395 math records and 649 Portuguese records, with 33 columns per row, but there is no student identifier, no grade-level/section/enrollment context, no attendance or behavior records, and no explicit At Risk / Not At Risk target. The files are therefore not suitable for direct use in the current EDU ASSIST risk-classification model without creating a new, unsupported target definition.

## 1) Files inspected

The folder `F:\edu_new\AI (ML)\dataset\student_performance` contains:

- `student-mat.csv` — 395 rows
- `student-por.csv` — 649 rows
- `student.txt` — dataset attribute documentation
- `student-merge.R` — merge script showing how the two course datasets are related

## 2) File formats and structure

### `student-mat.csv`
- Format: CSV
- Delimiter: semicolon (`;`)
- Shape: `395 x 33`
- Missing values: 0
- Duplicate rows: 0

### `student-por.csv`
- Format: CSV
- Delimiter: semicolon (`;`)
- Shape: `649 x 33`
- Missing values: 0
- Duplicate rows: 0

### `student.txt`
- Text/markdown attribute document describing the schema.
- Confirms that both CSVs represent course-specific data for Math and Portuguese.

### `student-merge.R`
- R script merges the two files by common demographics and indicates that 382 students appear in both datasets.
- This does not create a unique student identifier; it only shows overlap by common attribute values.

## 3) Exact column list

The datasets use the following columns:

- `school`
- `sex`
- `age`
- `address`
- `famsize`
- `Pstatus`
- `Medu`
- `Fedu`
- `Mjob`
- `Fjob`
- `reason`
- `guardian`
- `traveltime`
- `studytime`
- `failures`
- `schoolsup`
- `famsup`
- `paid`
- `activities`
- `nursery`
- `higher`
- `internet`
- `romantic`
- `famrel`
- `freetime`
- `goout`
- `Dalc`
- `Walc`
- `health`
- `absences`
- `G1`
- `G2`
- `G3`

## 4) Data types and value ranges

### Numeric fields
- `age`: integer, 15 to 22
- `Medu`: 0 to 4
- `Fedu`: 0 to 4
- `traveltime`: 1 to 4
- `studytime`: 1 to 4
- `failures`: numeric count, typically `0..3` with `4` representing multiple failures
- `famrel`: 1 to 5
- `freetime`: 1 to 5
- `goout`: 1 to 5
- `Dalc`: 1 to 5
- `Walc`: 1 to 5
- `health`: 1 to 5
- `absences`: number of absences, range observed in dataset is 0 to 93
- `G1`, `G2`, `G3`: course grades from 0 to 20

### Categorical fields
- `school`: `GP`, `MS`
- `sex`: `F`, `M`
- `address`: `U`, `R`
- `famsize`: `LE3`, `GT3`
- `Pstatus`: `T`, `A`
- `Mjob`: `teacher`, `health`, `services`, `at_home`, `other`
- `Fjob`: same categories as `Mjob`
- `reason`: `home`, `reputation`, `course`, `other`
- `guardian`: `mother`, `father`, `other`
- `schoolsup`: `yes`, `no`
- `famsup`: `yes`, `no`
- `paid`: `yes`, `no`
- `activities`: `yes`, `no`
- `nursery`: `yes`, `no`
- `higher`: `yes`, `no`
- `internet`: `yes`, `no`
- `romantic`: `yes`, `no`

## 5) Missing values and duplicates

- `student-mat.csv`: no missing values, no duplicate rows
- `student-por.csv`: no missing values, no duplicate rows
- No null or malformed ID or key fields
- There is also no explicit `student_id` column or natural unique row key

## 6) What the files represent

The data is not a cross-subject student-risk snapshot. Instead:

- `student-mat.csv` is for a Math course
- `student-por.csv` is for a Portuguese course
- both tables are course-level, student-level observational records
- the `student.txt` doc explicitly says the grades are related to the course subject, Math or Portuguese
- the `student-merge.R` script merges the two files by personal and family attributes to identify overlapping students

These files therefore represent:

- demographic context
- family context
- study habits
- alcohol/family/freetime traits
- absences
- course grades per subject

They do not represent:

- academic year
- grade level
- section/classroom
- enrollment record
- attendance history over a school period
- behavior assessments
- intervention plans
- teacher rating rubrics
- risk labels derived from academic concern

## 7) Student identity and joins

### Student identifier
There is no explicit student identifier such as `student_id`, `lrn`, `student_number`, or stable enrollment key.

### Joinability
The files can be joined only by a weak set of attributes such as:

- `school`
- `sex`
- `age`
- `address`
- `famsize`
- `Pstatus`
- `Medu`
- `Fedu`
- `Mjob`
- `Fjob`
- `reason`
- `nursery`
- `internet`

The `student-merge.R` script confirms that 382 students are shared across both datasets using this attribute pattern. This is not a proper relational student key and cannot safely serve as a production student identity for EDU ASSIST.

## 8) Actual meaning of columns

The columns are descriptive student and family features and course outcomes, not EDU ASSIST risk features. Examples:

- `school`: two possible schools
- `sex`: student sex
- `age`: numeric age
- `address`: urban vs rural residence
- `famsize`: small vs large family size
- `Medu` / `Fedu`: parent education levels
- `Mjob` / `Fjob`: parent occupational categories
- `traveltime` / `studytime`: time burden
- `failures`: past academic failures
- `schoolsup`, `famsup`, `paid`: support services and tutoring
- `activities`, `higher`, `internet`, `romantic`: extracurricular and personal context
- `absences`: counts of absences for the subject period
- `G1`, `G2`, `G3`: course grade milestones for the subject, with `G3` often treated as the final grade

## 9) Does an outcome or target exist?

The dataset does not have an explicit `At Risk` or `Not At Risk` column.

The closest outcome is:

- `G3` = final grade in the subject, numeric 0..20

This is not equivalent to the EDU ASSIST risk target because:

- it is a direct course grade, not a risk classification
- it is measured for a single subject and not a schoolwide student risk context
- it is not a binary risk label
- it is not aligned to the existing model contract (`At Risk` vs `Not At Risk`)
- it is highly likely to be a leakage source if used as the target, because it is directly in the same feature family as the course performance data

## 10) Can a valid risk target be constructed?

Not safely.

A defensible `At Risk` / `Not At Risk` target would require a clear rule based on a valid risk concept, such as repeated academic failure, chronic absences, disciplinary issues, intervention need, and context across records. The UCI dataset provides none of these as a canonical prediction target:

- no behavior rating
- no intervention history
- no enrollment/section/academic-year snapshot
- no explicit risk label
- no cross-period academic-risk event
- no student-level risk definition tied to school operations

Any custom target, such as `G3 < 10` or `failures > 0`, would be an invented label. That would not be a faithful representation of EDU ASSIST risk and would create a misleading training target.

## 11) Data-quality findings

- No missing values
- No duplicate rows in either file
- No invalid numeric ranges detected in the raw files
- No obvious schema corruption
- However, the files are not aligned with the live EDU ASSIST database schema or model target

## 12) Compatibility verdict

This dataset is not currently safe for the EDU ASSIST risk model because it lacks the required live-risk definition, student identity, enrollment context, behavior/intervention data, and At Risk / Not At Risk target label.

The dataset is useful only as a general educational-data reference, not as direct training data for the current production student-risk classifier.

## 13) Final conclusion

The UCI student-performance dataset should be treated as a separate academic-performance dataset with no direct compatibility to the EDU ASSIST risk model. It should not be used to retrain or replace the current synthetic model unless a new, documented, defensible target definition is created and a separate risk pipeline is intentionally designed around that new target.

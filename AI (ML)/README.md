# EDU ASSIST Phase 8A — AI Dataset and Machine Learning Foundation Specification

This document defines the AI dataset design for EDU ASSIST using a synthetic-only approach. The design is intended for future synthetic record generation and later model training.

## 1. Design Assumptions

- The dataset will be created as a student-level snapshot per school year and grading period.
- Each row represents one student at one assessment period (for example, one quarter).
- The target label is whether the student is classified as At Risk or Not At Risk.
- Because actual historical records are unavailable, the dataset is designed so that synthetic records can realistically mirror the school’s evaluation process.
- Behavioral ratings remain categorical and are preserved as teacher-entered values: AO, SO, RO, and NO.

## 2. Dataset Schema

| Column Name | Description | Data Type | Allowed Values | Required | Used for AI |
|---|---|---|---|---|---|
| student_id | Unique identifier for each student | String | Any unique string | Yes | Yes |
| school_year | School year of the record | String | Example: 2024-2025 | Yes | Yes |
| grade_level | Student grade level | Categorical | Grade 1 to Grade 12 or applicable school levels | Yes | Yes |
| section | Student section or class | String | Any valid section name | Yes | Yes |
| assessment_quarter | Quarter being evaluated | Categorical | 1, 2, 3, 4 | Yes | Yes |
| mathematics_grade | Mathematics grade | Numeric | 0–100 | No | Yes |
| english_grade | English grade | Numeric | 0–100 | No | Yes |
| science_grade | Science grade | Numeric | 0–100 | No | Yes |
| filipino_grade | Filipino grade | Numeric | 0–100 | No | Yes |
| araling_panlipunan_grade | Araling Panlipunan grade | Numeric | 0–100 | No | Yes |
| esp_grade | ESP grade | Numeric | 0–100 | No | Yes |
| mapeh_grade | MAPEH grade | Numeric | 0–100 | No | Yes |
| tle_grade | TLE grade | Numeric | 0–100 | No | Yes |
| general_average | Overall average for the period | Numeric | 0–100 | Yes | Yes |
| failed_subjects | Number of failed subjects | Numeric | 0–8 or more depending on school policy | No | Yes |
| present_days | Number of days present | Numeric | 0 or higher | No | Yes |
| absent_days | Number of absences | Numeric | 0 or higher | No | Yes |
| late_days | Number of tardiness incidents | Numeric | 0 or higher | No | Yes |
| excused_absences | Number of excused absences | Numeric | 0 or higher | No | Yes |
| attendance_rate | Percentage attendance for the period | Numeric | 0–100 | No | Yes |
| behavior_core_value | Core value being assessed | Categorical | Values defined by the school’s behavior framework | Yes | Yes |
| behavior_indicator | Specific behavior indicator | Categorical | Values defined by the school’s behavior rubric | Yes | Yes |
| behavior_teacher_rating | Teacher-entered behavior rating | Categorical | AO, SO, RO, NO | Yes | Yes |
| behavior_quarter | Quarter when the behavior assessment was recorded | Categorical | 1, 2, 3, 4 | Yes | Yes |
| teacher_remarks | Teacher comments about the student | Text | Any free-text remark | No | No |
| intervention_type | Type of intervention given | Categorical | Academic Monitoring, Tutoring, Counseling, Parent/Guardian Conference, Attendance Monitoring, Mentoring, Guidance Referral, Behavioral Monitoring | No | Yes |
| intervention_date | Date the intervention was recorded | Date | Valid date | No | No |
| intervention_reason | Reason for intervention | Text | Any short explanatory text | No | Yes |
| intervention_outcome | Outcome of the intervention | Categorical | Improved, Ongoing, No Change, Worsened, Not Yet Evaluated | No | Yes |
| improved_after_intervention | Whether the student improved after intervention | Boolean | True, False, Unknown | No | Yes |
| risk_status | Target label | Categorical | At Risk, Not At Risk | Yes | Yes |

## 3. Purpose of Every Feature

### Student Information

- student_id: Provides a unique reference for each student and allows traceability during dataset validation and later model monitoring.
- school_year: Helps the model distinguish performance across academic periods and supports the synthetic generation of year-based trends.
- grade_level: Grade level often influences expected academic difficulty and risk patterns.
- section: Section may reflect classroom environment, teacher expectations, or peer-group effects.
- assessment_quarter: Risk can be tied to timing; students may worsen in later quarters due to accumulated challenges.

### Academic Information

- mathematics_grade: Strong predictor of academic struggle when multiple subject grades decline simultaneously.
- english_grade: Often indicates reading comprehension and writing difficulties that may affect overall school performance.
- science_grade: Helps capture performance in analytical and concept-heavy subjects.
- filipino_grade: Relevant because language-based learning difficulties can affect comprehension and output.
- araling_panlipunan_grade: Useful for identifying broader academic performance issues across non-math subject areas.
- esp_grade: Adds signal for values education and classroom behavior alignment.
- mapeh_grade: Captures performance in arts, physical education, and health, which may reflect overall engagement.
- tle_grade: Useful for vocational and practical learning areas, especially in higher grade levels.
- general_average: Strong aggregate indicator of overall academic standing.
- failed_subjects: A direct indicator of cumulative academic risk.

### Attendance

- present_days: Indicates sustained school engagement.
- absent_days: High absenteeism often correlates with declining academic performance and increased risk.
- late_days: Frequent tardiness may signal poor routine, disengagement, or transportation issues.
- excused_absences: Helps distinguish between unavoidable absences and potentially avoidable absentee patterns.
- attendance_rate: Strong summary metric for school participation and academic consistency.

### Behavior

- behavior_core_value: Captures the specific core value being evaluated and helps connect behavior with school expectations.
- behavior_indicator: Provides context for the specific conduct concern or strength being observed.
- behavior_teacher_rating: The school’s behavioral rubric is directly relevant to risk because behavior difficulties often coincide with academic struggles.
- behavior_quarter: Behavior may change over time; repeated concerns in later quarters may signal increasing risk.
- teacher_remarks: Useful for qualitative context, although it may be treated as a later NLP feature rather than a primary baseline feature.

### Intervention

- intervention_type: Different interventions are associated with varying levels of student need and severity.
- intervention_date: A raw date field can later be transformed into recency or duration features.
- intervention_reason: Helps explain the nature of the problem and can indicate whether the intervention was triggered by attendance, academics, or behavior.
- intervention_outcome: Indicates whether the intervention appears to have worked.
- improved_after_intervention: A direct measure of intervention effectiveness and a useful predictor of current risk status.

### Target Label

- risk_status: This is the supervised output variable that the model will learn to predict.

## 4. Preprocessing Requirements Before Machine Learning

The following preprocessing steps will be needed later, but they are not implemented yet.

- Missing value handling:
  - Numeric features may require imputation for missing grades, attendance, or intervention values.
  - Categorical features may require a missing-category strategy.
- Categorical encoding:
  - One-hot encoding is recommended for nominal fields such as grade_level, section, school_year, behavior_core_value, behavior_indicator, intervention_type, and intervention_outcome.
  - Label encoding is not preferred for the behavior rating field because the school’s values are categorical and should not be treated as ordinal numbers.
- Scaling:
  - Logistic Regression will require feature scaling for numeric variables such as grades, attendance rate, and counts.
  - Tree-based models such as Random Forest do not strictly require scaling, but consistent preprocessing is still recommended.
- Outlier handling:
  - Grades and attendance metrics should be checked for impossible values or extreme outliers.
- Text preprocessing:
  - teacher_remarks would require tokenization and text cleaning if used in later NLP-based experiments.
- Date feature engineering:
  - intervention_date can be converted into derived features such as days since intervention, intervention recency, or intervention frequency.
- Feature aggregation:
  - Multiple intervention records may need aggregation to a single student-level representation.

## 5. Recommended Machine Learning Algorithm

### Comparison

- Decision Tree:
  - Easy to interpret and visualize.
  - Works well on tabular data but is prone to overfitting and can be unstable with small changes in data.
- Random Forest:
  - More robust than a single decision tree.
  - Handles nonlinear relationships well.
  - Performs reliably on mixed feature types and is less sensitive to overfitting.
  - Provides feature importance, which is helpful for educational interpretation.
- Logistic Regression:
  - Simple and interpretable.
  - Works well when relationships are approximately linear.
  - Less flexible for complex interactions between attendance, behavior, interventions, and academics.

### Recommendation

Random Forest is the most appropriate initial algorithm for EDU ASSIST because:

- The dataset will contain a mix of numeric, categorical, and behavioral features.
- The risk patterns are likely nonlinear and interaction-driven.
- The model should be robust enough for synthetic data and later real-world deployment.
- It offers explainability through feature importance, which is valuable for school staff and paper reporting.

A Logistic Regression model can still be used as a benchmark for interpretability, but Random Forest is the better primary choice for the first production-ready baseline.

## 6. Recommended AI Module Folder Structure

```text
AI (ML)/
├── README.md
├── dataset/
├── synthetic_data/
├── preprocessing/
├── training/
├── evaluation/
├── models/
├── prediction/
└── notebooks/
```

### Suggested purpose of each folder

- dataset/: Stores the raw and processed feature tables.
- synthetic_data/: Stores generator logic and synthetic dataset outputs.
- preprocessing/: Stores scripts and pipelines for cleaning, encoding, and scaling.
- training/: Stores training scripts and model configuration.
- evaluation/: Stores metrics, confusion matrices, and validation reports.
- models/: Stores serialized trained models.
- prediction/: Stores prediction scripts and API-facing utilities.
- notebooks/: Stores exploratory analysis and experimental notebooks.

## 7. Machine Learning Workflow

1. Dataset creation
   - Create the student-level feature table with academic, attendance, behavior, intervention, and target label columns.

2. Data validation
   - Check missing values, invalid grade ranges, invalid categorical values, and duplicate student records.

3. Data preprocessing
   - Handle missing values, encode categorical variables, and prepare the feature matrix for modeling.

4. Feature engineering
   - Create derived features such as intervention recency, cumulative absences, and behavior severity patterns.

5. Train/Test split
   - Split the dataset into training and testing subsets to evaluate generalization.

6. Model training
   - Train the selected model, starting with Random Forest as the baseline.

7. Model evaluation
   - Measure accuracy, precision, recall, F1-score, and confusion matrix performance.

8. Model serialization
   - Save the trained model and preprocessing pipeline for future reuse.

9. Django integration
   - Expose the model through the backend so the application can make predictions from incoming student data.

10. Prediction API
   - Provide an endpoint that accepts a student snapshot and returns the predicted risk status.

## 8. Summary

This specification provides a complete design for the AI dataset and machine learning foundation for EDU ASSIST. It is intentionally structured to support later synthetic data generation, preprocessing, model training, evaluation, and Django integration without introducing database or application changes in this phase.

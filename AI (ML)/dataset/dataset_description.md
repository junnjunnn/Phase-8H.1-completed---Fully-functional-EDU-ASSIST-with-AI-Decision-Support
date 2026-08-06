# Synthetic Student Dataset Description

## File
- synthetic_student_dataset.csv

## Purpose
This synthetic dataset mirrors a realistic school evaluation structure for EDU ASSIST AI development and testing. It contains approximately 1000 student records and includes academic, attendance, behavior, intervention, and target label information.

## Columns
- student_id: Unique student identifier.
- school_year: School year for the record.
- grade_level: Grade level of the student.
- section: Section or class name.
- assessment_quarter: Quarter represented by the record.
- mathematics_grade, english_grade, science_grade, filipino_grade, araling_panlipunan_grade, esp_grade, mapeh_grade, tle_grade: Subject grades in realistic school ranges.
- general_average: Average of the subject grades.
- failed_subjects: Number of failed academic subjects in the record.
- present_days, absent_days, late_days, excused_absences: Attendance-related counts.
- attendance_rate: Percentage attendance derived from attendance counts.
- behavior_core_value: School-aligned core value category.
- behavior_indicator: Specific behavior indicator.
- behavior_teacher_rating: Categorical teacher rating with allowed values AO, SO, RO, NO.
- behavior_quarter: Quarter when the assessment was recorded.
- teacher_remarks: Narrative teacher observation.
- intervention_type: Type of intervention if one was justified.
- intervention_date: Intervention date if present.
- intervention_reason: Brief explanation of the intervention.
- intervention_outcome: Outcome category for the intervention.
- improved_after_intervention: Boolean or blank value indicating whether improvement was observed.
- risk_status: Target label with allowed values At Risk or Not At Risk.

## Allowed Values
- behavior_teacher_rating: AO, SO, RO, NO
- risk_status: At Risk, Not At Risk
- intervention_outcome: Improved, Ongoing, No Change, Worsened, Not Yet Evaluated

## How Values Were Generated
- Student profiles were simulated using realistic grade-level and attendance patterns.
- Academic grades were drawn from a normal distribution centered on grade-level expectations.
- Attendance metrics were generated to be internally consistent with attendance rate and present/absent days.
- Behavior ratings were assigned according to a latent risk profile so that more vulnerable students were more likely to receive RO or NO.
- Intervention records were created only when academic, attendance, or behavior signals justified them.
- The risk label was assigned from a rule-based combination of academic, attendance, behavior, and intervention signals rather than randomly.

## Assumptions
- Grades are assumed to be school-style numeric values between 50 and 100.
- Attendance is represented as a school period with 100 possible school days for simplicity.
- The dataset is synthetic and intended for development and testing only.

## Target Label Logic
The target label was assigned using a weighted risk score:
- Low general average increased risk.
- Higher absences increased risk.
- Frequent tardiness increased risk.
- RO and NO behavior ratings increased risk.
- Intervention presence increased risk.
- Failing one or more subjects increased risk.
- Records with a total score of 4 or more were labeled At Risk; otherwise Not At Risk.

## Validation Summary
- Number of students: 1000
- Number of At Risk students: 394
- Number of Not At Risk students: 606
- Missing value count: 4358
- Duplicate count: 0
- Behavior rating distribution: {'NO': 164, 'AO': 311, 'SO': 268, 'RO': 257}
- Attendance rate summary: min=88.75, max=100.00, mean=97.54
- General average summary: min=57.18, max=93.99, mean=78.50

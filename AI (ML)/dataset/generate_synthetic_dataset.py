import csv
import random
from pathlib import Path
from collections import Counter

random.seed(42)

base_dir = Path(r'f:\edu_new\AI (ML)')
dataset_dir = base_dir / 'dataset'
dataset_dir.mkdir(parents=True, exist_ok=True)

num_students = 1000
school_years = ['2024-2025', '2025-2026']
grade_levels = ['Grade 4', 'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 'Grade 10']
sections = ['A', 'B', 'C', 'D']
quarters = [1, 2, 3, 4]
behavior_ratings = ['AO', 'SO', 'RO', 'NO']
intervention_types = ['Academic Monitoring', 'Tutoring', 'Counseling', 'Parent/Guardian Conference', 'Attendance Monitoring', 'Mentoring', 'Guidance Referral', 'Behavioral Monitoring']
outcomes = ['Improved', 'Ongoing', 'No Change', 'Worsened', 'Not Yet Evaluated']


def clamp(value, low, high):
    return max(low, min(high, value))


def generate_grade(base, variability=8):
    return round(clamp(random.gauss(base, variability), 50, 100), 2)


def generate_attendance_rate(absent, late):
    base = 100 - absent * 1.25 - late * 0.5
    return round(clamp(base, 40, 100), 2)


def generate_behavior_rating(risk_level):
    if risk_level == 'high':
        weights = {'NO': 0.45, 'RO': 0.3, 'SO': 0.15, 'AO': 0.1}
    elif risk_level == 'medium':
        weights = {'NO': 0.2, 'RO': 0.35, 'SO': 0.25, 'AO': 0.2}
    else:
        weights = {'NO': 0.05, 'RO': 0.15, 'SO': 0.3, 'AO': 0.5}
    return random.choices(behavior_ratings, weights=[weights[r] for r in behavior_ratings], k=1)[0]


rows = []
for i in range(1, num_students + 1):
    school_year = random.choice(school_years)
    grade_level = random.choice(grade_levels)
    section = random.choice(sections)
    quarter = random.choice(quarters)

    academic_struggle = random.random() < 0.3
    attendance_issue = random.random() < 0.25
    behavior_issue = random.random() < 0.2

    if grade_level in ['Grade 4', 'Grade 5', 'Grade 6']:
        base_avg = 86
    elif grade_level in ['Grade 7', 'Grade 8']:
        base_avg = 84
    else:
        base_avg = 82

    if academic_struggle:
        base_avg -= random.uniform(6, 15)
    if attendance_issue:
        base_avg -= random.uniform(2, 7)
    if behavior_issue:
        base_avg -= random.uniform(1, 5)
    base_avg = clamp(base_avg, 58, 98)

    math_grade = generate_grade(base_avg - 1.5)
    english_grade = generate_grade(base_avg - 0.8)
    science_grade = generate_grade(base_avg - 1.0)
    filipino_grade = generate_grade(base_avg - 0.5)
    araling_grade = generate_grade(base_avg - 0.7)
    esp_grade = generate_grade(base_avg + 0.5)
    mapeh_grade = generate_grade(base_avg + 1.0)
    tle_grade = generate_grade(base_avg - 0.2)

    general_average = round((math_grade + english_grade + science_grade + filipino_grade + araling_grade + esp_grade + mapeh_grade + tle_grade) / 8, 2)

    if attendance_issue:
        absent_days = int(random.uniform(1, 8))
        late_days = int(random.uniform(0, 6))
        excused_absences = int(random.uniform(0, 4))
    else:
        absent_days = int(random.uniform(0, 2))
        late_days = int(random.uniform(0, 3))
        excused_absences = int(random.uniform(0, 2))
    present_days = 100 - absent_days
    attendance_rate = round(generate_attendance_rate(absent_days, late_days), 2)

    if academic_struggle and attendance_issue:
        risk_level = 'high'
    elif academic_struggle or attendance_issue or behavior_issue:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    behavior_rating = generate_behavior_rating(risk_level)

    failed_subjects = 0
    if general_average < 75:
        failed_subjects += 1
    if general_average < 70:
        failed_subjects += 1
    if academic_struggle and general_average < 80:
        failed_subjects += 1
    failed_subjects = min(failed_subjects, 3)

    has_intervention = False
    intervention_type = ''
    intervention_reason = ''
    intervention_outcome = ''
    improved_after_intervention = ''
    if risk_level == 'high' or (academic_struggle and attendance_issue) or (behavior_issue and academic_struggle):
        has_intervention = True
        intervention_type = random.choice(intervention_types)
        intervention_reason = random.choice([
            'Declining grades and low class participation',
            'Frequent absences and missing assignments',
            'Behavior concerns affecting learning',
            'Need for academic support and monitoring',
            'Parent/guardian concern about performance',
            'Low attendance and poor engagement',
        ])
        intervention_outcome = random.choice(outcomes)
        improved_after_intervention = random.choice([True, False, False, None])

    risk_score = 0
    if general_average < 78:
        risk_score += 2
    elif general_average < 85:
        risk_score += 1
    if absent_days >= 4:
        risk_score += 2
    elif absent_days >= 2:
        risk_score += 1
    if late_days >= 5:
        risk_score += 1
    if behavior_rating in ['RO', 'NO']:
        risk_score += 2
    elif behavior_rating == 'SO':
        risk_score += 1
    if has_intervention:
        risk_score += 1
    if failed_subjects >= 1:
        risk_score += 1
    risk_status = 'At Risk' if risk_score >= 4 else 'Not At Risk'

    if risk_status == 'Not At Risk' and random.random() < 0.08:
        risk_status = 'At Risk'
    if risk_status == 'At Risk' and random.random() < 0.12:
        risk_status = 'Not At Risk'

    rows.append({
        'student_id': f'ST-{i:04d}',
        'school_year': school_year,
        'grade_level': grade_level,
        'section': section,
        'assessment_quarter': quarter,
        'mathematics_grade': math_grade,
        'english_grade': english_grade,
        'science_grade': science_grade,
        'filipino_grade': filipino_grade,
        'araling_panlipunan_grade': araling_grade,
        'esp_grade': esp_grade,
        'mapeh_grade': mapeh_grade,
        'tle_grade': tle_grade,
        'general_average': general_average,
        'failed_subjects': failed_subjects,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'excused_absences': excused_absences,
        'attendance_rate': attendance_rate,
        'behavior_core_value': random.choice(['Respect', 'Responsibility', 'Compassion', 'Integrity', 'Excellence']),
        'behavior_indicator': random.choice(['Shows respect to teachers and peers', 'Completes assignments on time', 'Displays kindness and empathy', 'Practices honesty', 'Demonstrates effort and perseverance']),
        'behavior_teacher_rating': behavior_rating,
        'behavior_quarter': quarter,
        'teacher_remarks': random.choice([
            'Shows potential but needs more consistency',
            'Improving steadily in class participation',
            'Needs follow-up on attendance and punctuality',
            'Demonstrates positive effort in class',
            'Requires regular monitoring for academic progress'
        ]),
        'intervention_type': intervention_type,
        'intervention_date': '' if not has_intervention else f'2025-0{quarter}-15',
        'intervention_reason': intervention_reason,
        'intervention_outcome': intervention_outcome,
        'improved_after_intervention': improved_after_intervention,
        'risk_status': risk_status,
    })

csv_path = dataset_dir / 'synthetic_student_dataset.csv'
fieldnames = [
    'student_id', 'school_year', 'grade_level', 'section', 'assessment_quarter',
    'mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade',
    'general_average', 'failed_subjects', 'present_days', 'absent_days', 'late_days', 'excused_absences', 'attendance_rate',
    'behavior_core_value', 'behavior_indicator', 'behavior_teacher_rating', 'behavior_quarter', 'teacher_remarks',
    'intervention_type', 'intervention_date', 'intervention_reason', 'intervention_outcome', 'improved_after_intervention', 'risk_status'
]
with csv_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

with csv_path.open('r', encoding='utf-8') as f:
    reader = list(csv.DictReader(f))

missing_values = sum(1 for row in reader for value in row.values() if value == '')
duplicate_ids = len(reader) - len({row['student_id'] for row in reader})
risk_counts = Counter(row['risk_status'] for row in reader)
behavior_counts = Counter(row['behavior_teacher_rating'] for row in reader)
avg_values = [float(row['general_average']) for row in reader]
attendance_values = [float(row['attendance_rate']) for row in reader]

summary_path = dataset_dir / 'dataset_description.md'
summary_path.write_text(
    f'''# Synthetic Student Dataset Description

## File
- {csv_path.name}

## Purpose
This synthetic dataset mirrors a realistic school evaluation structure for EDU ASSIST AI development and testing. It contains approximately {len(reader)} student records and includes academic, attendance, behavior, intervention, and target label information.

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
- Number of students: {len(reader)}
- Number of At Risk students: {risk_counts.get('At Risk', 0)}
- Number of Not At Risk students: {risk_counts.get('Not At Risk', 0)}
- Missing value count: {missing_values}
- Duplicate count: {duplicate_ids}
- Behavior rating distribution: {dict(behavior_counts)}
- Attendance rate summary: min={min(attendance_values):.2f}, max={max(attendance_values):.2f}, mean={sum(attendance_values)/len(attendance_values):.2f}
- General average summary: min={min(avg_values):.2f}, max={max(avg_values):.2f}, mean={sum(avg_values)/len(avg_values):.2f}
''', encoding='utf-8')

print(f'Generated {len(rows)} rows to {csv_path}')
print(f'  At Risk: {risk_counts.get("At Risk", 0)}')
print(f'  Not At Risk: {risk_counts.get("Not At Risk", 0)}')
print(f'  Missing values: {missing_values}')
print(f'  Duplicates: {duplicate_ids}')
print(f'  Behavior ratings: {dict(behavior_counts)}')
print(f'  Attendance rate min/max/mean: {min(attendance_values):.2f}/{max(attendance_values):.2f}/{sum(attendance_values)/len(attendance_values):.2f}')
print(f'  General average min/max/mean: {min(avg_values):.2f}/{max(avg_values):.2f}/{sum(avg_values)/len(avg_values):.2f}')

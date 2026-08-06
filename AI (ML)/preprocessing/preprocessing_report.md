# Preprocessing Report

## Dataset Summary
- Original row count: 1000
- Final row count: 1000
- Missing values removed: 4358
- Duplicate count: 0
- Engineered features: absent_percentage, late_percentage, high_grade_count, has_intervention, number_of_interventions, risk_label

## Quality Assessment
- Missing values before cleaning: see quality report in script output
- Duplicate rows: 0
- Invalid categorical values: none after correction to default categories
- Invalid attendance values: corrected to valid ranges
- Invalid grades: corrected to valid ranges
- Invalid behavior ratings: corrected to default category when missing
- Invalid intervention values: corrected to default category when missing

## Encoded Features
- Encoded categorical features using OneHotEncoder
- Final feature count: 62

## Splitting
- Training set size: 800
- Test set size: 200

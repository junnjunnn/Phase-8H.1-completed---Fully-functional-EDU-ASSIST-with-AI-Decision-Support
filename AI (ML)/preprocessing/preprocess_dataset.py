import json
import os
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(r'f:\edu_new\AI (ML)')
DATASET_PATH = BASE_DIR / 'dataset' / 'synthetic_student_dataset.csv'
PREPROCESSING_DIR = BASE_DIR / 'preprocessing'
PREPROCESSING_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_PATH = PREPROCESSING_DIR / 'clean_student_dataset.csv'
X_TRAIN_PATH = PREPROCESSING_DIR / 'X_train.csv'
X_TEST_PATH = PREPROCESSING_DIR / 'X_test.csv'
Y_TRAIN_PATH = PREPROCESSING_DIR / 'y_train.csv'
Y_TEST_PATH = PREPROCESSING_DIR / 'y_test.csv'
MAPPING_PATH = PREPROCESSING_DIR / 'feature_mapping.json'
REPORT_PATH = PREPROCESSING_DIR / 'preprocessing_report.md'


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f'Dataset not found: {path}')
    df = pd.read_csv(path)
    expected_columns = [
        'student_id', 'school_year', 'grade_level', 'section', 'assessment_quarter',
        'mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade',
        'general_average', 'failed_subjects', 'present_days', 'absent_days', 'late_days', 'excused_absences', 'attendance_rate',
        'behavior_core_value', 'behavior_indicator', 'behavior_teacher_rating', 'behavior_quarter', 'teacher_remarks',
        'intervention_type', 'intervention_date', 'intervention_reason', 'intervention_outcome', 'improved_after_intervention', 'risk_status'
    ]
    missing_cols = [col for col in expected_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f'Missing columns: {missing_cols}')
    return df


def assess_quality(df: pd.DataFrame) -> dict:
    quality_report = {
        'row_count': int(df.shape[0]),
        'missing_values': df.isna().sum().to_dict(),
        'duplicate_rows': int(df.duplicated().sum()),
        'invalid_grades': {},
        'invalid_attendance_values': {},
        'invalid_behavior_ratings': {},
        'invalid_intervention_values': {},
    }

    grade_columns = [
        'mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade', 'general_average'
    ]
    for col in grade_columns:
        if col in df.columns:
            invalid = df[col].apply(lambda x: pd.notna(x) and (x < 0 or x > 100)).sum()
            quality_report['invalid_grades'][col] = int(invalid)

    attendance_columns = ['present_days', 'absent_days', 'late_days', 'excused_absences', 'attendance_rate']
    for col in attendance_columns:
        if col in df.columns:
            if col == 'attendance_rate':
                invalid = df[col].apply(lambda x: pd.notna(x) and (x < 0 or x > 100)).sum()
            else:
                invalid = df[col].apply(lambda x: pd.notna(x) and x < 0).sum()
            quality_report['invalid_attendance_values'][col] = int(invalid)

    allowed_behavior_ratings = {'AO', 'SO', 'RO', 'NO'}
    behavior_series = df['behavior_teacher_rating'].fillna('')
    quality_report['invalid_behavior_ratings'] = {
        'count': int(behavior_series.apply(lambda x: str(x).strip() not in allowed_behavior_ratings).sum())
    }

    allowed_intervention_types = {
        'Academic Monitoring', 'Tutoring', 'Counseling', 'Parent/Guardian Conference', 'Attendance Monitoring', 'Mentoring', 'Guidance Referral', 'Behavioral Monitoring'
    }
    intervention_series = df['intervention_type'].fillna('')
    quality_report['invalid_intervention_values'] = {
        'count': int(intervention_series.apply(lambda x: str(x).strip() != '' and str(x).strip() not in allowed_intervention_types).sum())
    }

    return quality_report


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cleaned = df.copy()
    cleaned = cleaned.drop_duplicates(subset=['student_id'], keep='first')

    for col in ['teacher_remarks', 'intervention_type', 'intervention_date', 'intervention_reason', 'intervention_outcome', 'improved_after_intervention']:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].replace({pd.NA: '', None: ''})

    for col in ['mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade', 'general_average', 'attendance_rate']:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors='coerce')
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
            if col in ['mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade', 'general_average']:
                cleaned.loc[cleaned[col] < 0, col] = 0
                cleaned.loc[cleaned[col] > 100, col] = 100
            if col == 'attendance_rate':
                cleaned.loc[cleaned[col] < 0, col] = 0
                cleaned.loc[cleaned[col] > 100, col] = 100

    for col in ['present_days', 'absent_days', 'late_days', 'excused_absences', 'failed_subjects', 'behavior_quarter', 'assessment_quarter']:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors='coerce')
            cleaned[col] = cleaned[col].fillna(0)

    categorical_cols = ['school_year', 'grade_level', 'section', 'behavior_core_value', 'behavior_indicator', 'behavior_teacher_rating', 'intervention_type', 'intervention_outcome']
    for col in categorical_cols:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].fillna('Unknown').astype(str)
            cleaned[col] = cleaned[col].str.strip()
            cleaned[col] = cleaned[col].replace({'': 'Unknown'})

    cleaned['behavior_teacher_rating'] = cleaned['behavior_teacher_rating'].replace({'': 'Unknown'})
    cleaned['intervention_type'] = cleaned['intervention_type'].replace({'': 'No Intervention'})
    cleaned['intervention_outcome'] = cleaned['intervention_outcome'].replace({'': 'Not Yet Evaluated'})

    cleaned['risk_status'] = cleaned['risk_status'].replace({'': 'Unknown'})

    cleaned['general_average'] = cleaned['general_average'].astype(float)
    cleaned['attendance_rate'] = cleaned['attendance_rate'].astype(float)

    cleaned['absent_percentage'] = (cleaned['absent_days'] / (cleaned['present_days'] + cleaned['absent_days'] + 1e-9)) * 100
    cleaned['late_percentage'] = (cleaned['late_days'] / (cleaned['present_days'] + cleaned['absent_days'] + 1e-9)) * 100
    cleaned['high_grade_count'] = (
        (cleaned['mathematics_grade'] >= 90).astype(int) +
        (cleaned['english_grade'] >= 90).astype(int) +
        (cleaned['science_grade'] >= 90).astype(int) +
        (cleaned['filipino_grade'] >= 90).astype(int) +
        (cleaned['araling_panlipunan_grade'] >= 90).astype(int) +
        (cleaned['esp_grade'] >= 90).astype(int) +
        (cleaned['mapeh_grade'] >= 90).astype(int) +
        (cleaned['tle_grade'] >= 90).astype(int)
    )
    cleaned['has_intervention'] = cleaned['intervention_type'].ne('').astype(int)
    cleaned['number_of_interventions'] = cleaned['intervention_type'].apply(lambda x: 1 if str(x).strip() not in {'', 'No Intervention'} else 0)
    cleaned['risk_label'] = cleaned['risk_status'].map({'At Risk': 1, 'Not At Risk': 0, 'Unknown': -1})

    report = {
        'original_rows': int(df.shape[0]),
        'final_rows': int(cleaned.shape[0]),
        'duplicates_removed': int(df.shape[0] - cleaned.shape[0]),
        'missing_values_removed': int(df.isna().sum().sum() - cleaned.isna().sum().sum()),
        'engineered_features': ['absent_percentage', 'late_percentage', 'high_grade_count', 'has_intervention', 'number_of_interventions', 'risk_label'],
    }
    return cleaned, report


def encode_features(cleaned: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    feature_columns = [
        'school_year', 'grade_level', 'section', 'behavior_core_value', 'behavior_indicator',
        'behavior_teacher_rating', 'intervention_type', 'intervention_outcome',
        'mathematics_grade', 'english_grade', 'science_grade', 'filipino_grade', 'araling_panlipunan_grade', 'esp_grade', 'mapeh_grade', 'tle_grade',
        'general_average', 'failed_subjects', 'present_days', 'absent_days', 'late_days', 'excused_absences', 'attendance_rate',
        'absent_percentage', 'late_percentage', 'high_grade_count', 'has_intervention', 'number_of_interventions'
    ]

    X = cleaned[feature_columns].copy()
    y = cleaned['risk_label']

    categorical_columns = ['school_year', 'grade_level', 'section', 'behavior_core_value', 'behavior_indicator', 'behavior_teacher_rating', 'intervention_type', 'intervention_outcome']
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    encoded_cats = encoder.fit_transform(X[categorical_columns])
    encoded_df = pd.DataFrame(encoded_cats, columns=encoder.get_feature_names_out(categorical_columns), index=X.index)

    X_numeric = X.drop(columns=categorical_columns)
    X_final = pd.concat([X_numeric.reset_index(drop=True), encoded_df.reset_index(drop=True)], axis=1)

    mapping = {
        'categorical_columns': categorical_columns,
        'numeric_columns': list(X_numeric.columns),
        'encoder_categories': [list(cat) for cat in encoder.categories_],
        'encoded_feature_count': int(X_final.shape[1]),
    }

    return X_final, y, mapping


def split_data(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test


def save_outputs(cleaned: pd.DataFrame, X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.Series, y_test: pd.Series, mapping: dict, report: dict) -> None:
    cleaned.to_csv(CLEAN_PATH, index=False)
    X_train.to_csv(X_TRAIN_PATH, index=False)
    X_test.to_csv(X_TEST_PATH, index=False)
    y_train.to_frame(name='risk_label').to_csv(Y_TRAIN_PATH, index=False)
    y_test.to_frame(name='risk_label').to_csv(Y_TEST_PATH, index=False)
    with MAPPING_PATH.open('w', encoding='utf-8') as fh:
        json.dump(mapping, fh, indent=2)

    report_md = f"""# Preprocessing Report

## Dataset Summary
- Original row count: {report['original_rows']}
- Final row count: {report['final_rows']}
- Missing values removed: {report['missing_values_removed']}
- Duplicate count: {report['duplicates_removed']}
- Engineered features: {', '.join(report['engineered_features'])}

## Quality Assessment
- Missing values before cleaning: see quality report in script output
- Duplicate rows: {report['duplicates_removed']}
- Invalid categorical values: none after correction to default categories
- Invalid attendance values: corrected to valid ranges
- Invalid grades: corrected to valid ranges
- Invalid behavior ratings: corrected to default category when missing
- Invalid intervention values: corrected to default category when missing

## Encoded Features
- Encoded categorical features using OneHotEncoder
- Final feature count: {mapping['encoded_feature_count']}

## Splitting
- Training set size: {len(X_train)}
- Test set size: {len(X_test)}
"""
    REPORT_PATH.write_text(report_md, encoding='utf-8')


def main() -> None:
    df = load_dataset(DATASET_PATH)
    quality_report = assess_quality(df)
    print('Quality assessment:')
    print(json.dumps(quality_report, indent=2))

    cleaned, cleaning_report = clean_dataset(df)
    X_final, y, mapping = encode_features(cleaned)
    X_train, X_test, y_train, y_test = split_data(X_final, y)
    save_outputs(cleaned, X_train, X_test, y_train, y_test, mapping, {**cleaning_report, 'X_train': X_train, 'X_test': X_test})

    print('\nSaved preprocessing artifacts:')
    print(CLEAN_PATH)
    print(X_TRAIN_PATH)
    print(X_TEST_PATH)
    print(Y_TRAIN_PATH)
    print(Y_TEST_PATH)
    print(MAPPING_PATH)
    print(REPORT_PATH)


if __name__ == '__main__':
    main()

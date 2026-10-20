import json
import logging
import pickle
import re
from pathlib import Path
from decimal import Decimal
from typing import Any, Dict, List, Tuple

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from academics.models import AcademicRecord, Enrollment
from attendance.models import AttendanceRecord
from behavior.models import BehavioralAssessment, BehavioralRating
from interventions.models import Intervention
from predictions.models import PredictionFactor, RiskPrediction
from students.models import Student
from common.authorization import active_enrollment_queryset
from .explanation_service import ExplanationService

ROOT_DIR = Path(settings.BASE_DIR).parent
MODEL_PATH = ROOT_DIR / 'AI (ML)' / 'models' / 'risk_model.pkl'
LABEL_MAP_PATH = ROOT_DIR / 'AI (ML)' / 'models' / 'label_encoder.pkl'
FEATURE_MAPPING_PATH = ROOT_DIR / 'AI (ML)' / 'models' / 'feature_mapping.json'

_MODEL = None
_LABELS = None
_FEATURE_MAPPING = None
logger = logging.getLogger(__name__)


class FeatureContractError(ValueError):
    """Raised when application data cannot be represented by the saved model."""

    def __init__(self, diagnostics: List[str]) -> None:
        self.diagnostics = diagnostics
        super().__init__('Prediction unavailable because the student data is not compatible with the current model.')


class PredictionService:
    ML_OUTPUT_LABELS = {
        1: 'At Risk',
        0: 'Not At Risk',
    }
    APPLICATION_RISK_MAP = {
        'At Risk': 'High',
        'Not At Risk': 'Low',
    }

    def __init__(self) -> None:
        self.model = self._load_model()
        self.label_map = self._load_label_map()
        self.feature_mapping = self._load_feature_mapping()
        self.explanation_service = ExplanationService()

    @classmethod
    def ml_prediction_label(cls, raw_prediction: int) -> str:
        """Canonical ML label contract. The trained Random Forest is binary and intentionally decodes to the application's active risk states."""
        if raw_prediction in cls.ML_OUTPUT_LABELS:
            return cls.ML_OUTPUT_LABELS[raw_prediction]
        return 'At Risk' if raw_prediction == 1 else 'Not At Risk'

    @classmethod
    def application_risk_level(cls, prediction_label: str) -> str:
        """Map the model's binary label to the application's active risk taxonomy without introducing unsupported states."""
        if prediction_label in cls.APPLICATION_RISK_MAP:
            return cls.APPLICATION_RISK_MAP[prediction_label]
        return 'High' if prediction_label == 'At Risk' else 'Low'

    def _load_model(self):
        global _MODEL
        if _MODEL is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(f'Risk prediction model not found at {MODEL_PATH}')
            try:
                with MODEL_PATH.open('rb') as fh:
                    _MODEL = pickle.load(fh)
            except Exception as e:
                raise RuntimeError(f'Failed to load risk prediction model: {str(e)}')
        return _MODEL

    def _load_label_map(self) -> Dict[int, str]:
        global _LABELS
        if _LABELS is None:
            if not LABEL_MAP_PATH.exists():
                raise FileNotFoundError(f'Label encoder model not found at {LABEL_MAP_PATH}')
            try:
                with LABEL_MAP_PATH.open('rb') as fh:
                    raw = pickle.load(fh)
                    _LABELS = raw.get('target_map', {1: 'At Risk', 0: 'Not At Risk'})
            except Exception as e:
                raise RuntimeError(f'Failed to load label encoder: {str(e)}')
        return _LABELS

    def _load_feature_mapping(self) -> Dict[str, Any]:
        global _FEATURE_MAPPING
        if _FEATURE_MAPPING is None:
            if not FEATURE_MAPPING_PATH.exists():
                raise FileNotFoundError(f'Feature mapping configuration not found at {FEATURE_MAPPING_PATH}')
            try:
                with FEATURE_MAPPING_PATH.open('r', encoding='utf-8') as fh:
                    _FEATURE_MAPPING = json.load(fh)
            except Exception as e:
                raise RuntimeError(f'Failed to load feature mapping: {str(e)}')
        return _FEATURE_MAPPING

    def _canonicalize_value(self, field_name: str, value: Any) -> Any:
        if value is None:
            return value

        normalized_value = str(value).strip()
        aliases = self.feature_mapping.get('value_aliases', {}).get(field_name, {})
        if not aliases:
            if field_name == 'section':
                legacy_match = re.fullmatch(r'(?i)(?:legacy|old)[-_ ]*([a-d])', normalized_value)
                if legacy_match:
                    return legacy_match.group(1).upper()
            return normalized_value

        for raw_value, canonical_value in aliases.items():
            if normalized_value.casefold() == str(raw_value).strip().casefold():
                return canonical_value

        if field_name == 'section':
            legacy_match = re.fullmatch(r'(?i)(?:legacy|old)[-_ ]*([a-d])', normalized_value)
            if legacy_match:
                return legacy_match.group(1).upper()

        return normalized_value

    def _resolve_subject_feature(self, subject_name: str) -> str:
        if not subject_name:
            return ''

        subject_map = self.feature_mapping.get('subject_feature_map', {})
        normalized_subject_map = {str(name).strip().casefold(): feature for name, feature in subject_map.items()}
        key = str(subject_name).strip().casefold()
        if key in normalized_subject_map:
            return normalized_subject_map[key]

        value_aliases = self.feature_mapping.get('subject_aliases', {})
        normalized_aliases = {str(name).strip().casefold(): feature for name, feature in value_aliases.items()}
        return normalized_aliases.get(key, '')

    def build_feature_vector(self, student_id: int, enrollment: Enrollment = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise FeatureContractError(['Student not found.'])

        enrollment = enrollment or Enrollment.objects.filter(student=student).order_by('-academic_year__start_date').first()
        if not enrollment:
            raise FeatureContractError(['No active enrollment found for the selected student snapshot.'])

        academic_records = AcademicRecord.objects.filter(enrollment=enrollment).select_related('subject')
        attendance_records = AttendanceRecord.objects.filter(enrollment=enrollment)
        behavior_assessments = BehavioralAssessment.objects.filter(enrollment=enrollment).select_related('rating')
        interventions = Intervention.objects.filter(enrollment=enrollment)

        grade_values = [float(record.final_grade or record.grade or 0) for record in academic_records]
        if grade_values:
            general_average = round(sum(grade_values) / len(grade_values), 2)
        else:
            general_average = 0.0

        failed_subjects = sum(1 for record in academic_records if (record.final_grade or record.grade or 0) < 75)
        high_grade_count = sum(1 for record in academic_records if (record.final_grade or record.grade or 0) >= 90)

        attendance_rows = list(attendance_records)
        if attendance_rows:
            present_days = sum(row.days_present for row in attendance_rows)
            absent_days = sum(row.absences for row in attendance_rows)
            late_days = sum(row.times_tardy for row in attendance_rows)
            school_days = sum(row.school_days for row in attendance_rows)
            attendance_rate = round((present_days / school_days * 100) if school_days else 0.0, 2)
        else:
            present_days = 0
            absent_days = 0
            late_days = 0
            school_days = 0
            attendance_rate = 0.0

        absent_percentage = round((absent_days / (school_days or 1) * 100), 2) if school_days else 0.0
        late_percentage = round((late_days / (school_days or 1) * 100), 2) if school_days else 0.0

        latest_behavior = behavior_assessments.order_by('-assessment_date', '-created_at').first()
        behavior_ratings = []
        for record in behavior_assessments:
            if record.rating and record.rating.code:
                behavior_ratings.append(record.rating.code)
        behavior_rating = max(set(behavior_ratings), key=behavior_ratings.count) if behavior_ratings else 'AO'
        default_core_value = 'Maka-Diyos'
        default_indicator = 'Shows adherence to ethical principles by upholding truth'
        source_core_value = latest_behavior.core_value.name if latest_behavior and latest_behavior.core_value else default_core_value
        source_indicator = latest_behavior.behavior_indicator.name if latest_behavior and latest_behavior.behavior_indicator else default_indicator

        feature_values = {
            'school_year': self._canonicalize_value('school_year', str(enrollment.academic_year.name) if enrollment.academic_year else 'Unknown'),
            'grade_level': self._canonicalize_value('grade_level', str(enrollment.grade_level.name) if enrollment.grade_level else 'Unknown'),
            'section': self._canonicalize_value('section', str(enrollment.section.name) if enrollment.section else 'Unknown'),
            'behavior_core_value': self._canonicalize_value('behavior_core_value', source_core_value),
            'behavior_indicator': self._canonicalize_value('behavior_indicator', source_indicator),
            'behavior_teacher_rating': self._canonicalize_value('behavior_teacher_rating', behavior_rating),
            'intervention_type': self._canonicalize_value('intervention_type', 'No Intervention' if not interventions.exists() else str(interventions.order_by('-created_at').first().intervention_type)),
            'intervention_outcome': self._canonicalize_value('intervention_outcome', 'Not Yet Evaluated'),
            'mathematics_grade': 0.0,
            'english_grade': 0.0,
            'science_grade': 0.0,
            'filipino_grade': 0.0,
            'araling_panlipunan_grade': 0.0,
            'esp_grade': 0.0,
            'mapeh_grade': 0.0,
            'tle_grade': 0.0,
            'general_average': general_average,
            'failed_subjects': failed_subjects,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'excused_absences': 0,
            'attendance_rate': attendance_rate,
            'absent_percentage': absent_percentage,
            'late_percentage': late_percentage,
            'high_grade_count': high_grade_count,
            'has_intervention': 1 if interventions.exists() else 0,
            'number_of_interventions': interventions.count(),
        }

        contract_diagnostics = []
        if academic_records.exists():
            for record in academic_records:
                subject_name = record.subject.name if record.subject else ''
                feature_key = self._resolve_subject_feature(subject_name)
                if feature_key:
                    feature_values[feature_key] = float(record.final_grade or record.grade or 0)
                else:
                    contract_diagnostics.append(
                        f"Subject '{subject_name or 'Unknown'}' is not represented in the current model vocabulary; "
                        f"grade {float(record.final_grade or record.grade or 0)} was not encoded."
                    )

        categorical_columns = self.feature_mapping.get('categorical_columns', [])
        numeric_columns = self.feature_mapping.get('numeric_columns', [])
        encoder_categories = self.feature_mapping.get('encoder_categories', [])
        dynamic_columns = set(self.feature_mapping.get('dynamic_categorical_columns', []))
        fixed_columns = set(self.feature_mapping.get('fixed_categorical_columns', []))

        for column, value, categories in zip(categorical_columns, (
            feature_values.get(column) for column in categorical_columns
        ), encoder_categories):
            if value is None:
                contract_diagnostics.append(f"{column} value is missing and cannot be encoded.")
                continue
            normalized_value = self._canonicalize_value(column, value)
            if normalized_value not in categories:
                if column in dynamic_columns:
                    contract_diagnostics.append(
                        f"{column} value '{value}' is an unseen dynamic categorical value; the encoder will keep the one-hot block at an all-zero row for compatibility with the persisted model."
                    )
                    feature_values[column] = normalized_value
                elif column in fixed_columns:
                    contract_diagnostics.append(
                        f"{column} value '{value}' is not represented in the current model vocabulary."
                    )
                    raise FeatureContractError([f"{column} value '{value}' is not represented in the current model vocabulary."])
                else:
                    contract_diagnostics.append(
                        f"{column} value '{value}' is not represented in the current model vocabulary."
                    )
                    feature_values[column] = normalized_value
            else:
                feature_values[column] = normalized_value

        encoded_feature_values = {col: feature_values.get(col, 0) for col in categorical_columns + numeric_columns}

        frame = pd.DataFrame([encoded_feature_values], columns=categorical_columns + numeric_columns)
        frame[numeric_columns] = frame[numeric_columns].apply(pd.to_numeric, errors='coerce').fillna(0)

        encoded_columns: List[str] = []
        encoded_values: List[float] = []
        for col in numeric_columns:
            encoded_columns.append(col)
            encoded_values.append(float(frame.iloc[0][col]))

        for col_idx, col in enumerate(categorical_columns):
            value = str(frame.iloc[0][col])
            for category in encoder_categories[col_idx]:
                encoded_columns.append(f'{col}_{category}')
                encoded_values.append(1.0 if value == category else 0.0)

        encoded_frame = pd.DataFrame([encoded_values], columns=encoded_columns)
        feature_values['contract_diagnostics'] = contract_diagnostics

        dynamic_columns = set(self.feature_mapping.get('dynamic_categorical_columns', []))
        fixed_columns = set(self.feature_mapping.get('fixed_categorical_columns', []))

        for col_idx, column in enumerate(self.feature_mapping.get('categorical_columns', [])):
            value = feature_values.get(column)
            if value is None:
                raise FeatureContractError([f'{column} value is missing and cannot be encoded.'])
            categories = self.feature_mapping.get('encoder_categories', [])[col_idx]
            if column in fixed_columns and str(value) not in categories:
                raise FeatureContractError([
                    f"{column} value '{value}' is not represented in the current model vocabulary."
                ])
            if column not in dynamic_columns and column not in fixed_columns and str(value) not in categories:
                raise FeatureContractError([
                    f"{column} value '{value}' is not represented in the current model vocabulary."
                ])

        return encoded_frame, feature_values

    def validate_feature_frame(self, feature_frame: pd.DataFrame, feature_values: Dict[str, Any]) -> pd.DataFrame:
        expected_columns = list(getattr(self.model, 'feature_names_in_', []))
        expected_count = int(getattr(self.model, 'n_features_in_', len(expected_columns)))
        if len(feature_frame.columns) != expected_count:
            raise FeatureContractError([f'Feature vector contains {len(feature_frame.columns)} columns; expected {expected_count}.'])

        if not expected_columns:
            raise FeatureContractError(['Saved model contract is missing feature names.'])

        missing_columns = [col for col in expected_columns if col not in feature_frame.columns]
        if missing_columns:
            raise FeatureContractError([f'Feature vector is missing required model columns: {missing_columns[:5]}.'])

        if list(feature_frame.columns) != expected_columns:
            raise FeatureContractError(['Feature names or order do not match the saved model contract.'])

        numeric_frame = feature_frame.apply(pd.to_numeric, errors='coerce')
        finite_frame = numeric_frame.replace([float('inf'), float('-inf')], pd.NA)
        if finite_frame.isna().any().any():
            raise FeatureContractError(['Feature vector contains a non-numeric or missing value.'])

        categorical_columns = self.feature_mapping.get('categorical_columns', [])
        encoder_categories = self.feature_mapping.get('encoder_categories', [])
        for col_idx, column in enumerate(categorical_columns):
            allowed = encoder_categories[col_idx] if col_idx < len(encoder_categories) else []
            encoded_group = [f'{column}_{category}' for category in allowed]
            missing_group = [name for name in encoded_group if name not in feature_frame.columns]
            if missing_group:
                raise FeatureContractError([f'Missing categorical feature group for {column}: {missing_group[:3]}.'])
            group_values = feature_frame[encoded_group].apply(pd.to_numeric, errors='coerce')
            if group_values.isna().any().any():
                raise FeatureContractError([f'Categorical feature group for {column} contains non-numeric values.'])
            if not ((group_values == 0) | (group_values == 1)).all().all():
                raise FeatureContractError([f'Categorical feature group for {column} must be encoded as binary one-hot values.'])
            if float(group_values.sum(axis=1).iloc[0]) not in {0.0, 1.0}:
                raise FeatureContractError([f'Categorical feature group for {column} must contain exactly one active category.'])

        diagnostics = feature_values.get('contract_diagnostics', [])
        if diagnostics:
            logger.warning('Prediction kept with explicit compatibility warnings: %s', diagnostics)

        return feature_frame

    def predict_for_student(self, student_id: int) -> Dict[str, Any]:
        student = Student.objects.filter(id=student_id, student_status='active').first()
        enrollment = active_enrollment_queryset(Enrollment.objects.filter(student=student)).order_by('-academic_year__start_date').first() if student else None
        if not enrollment:
            raise FeatureContractError(['No active enrollment found for the selected student snapshot.'])

        feature_frame, feature_values = self.build_feature_vector(student_id, enrollment=enrollment)
        feature_frame = self.validate_feature_frame(feature_frame, feature_values)
        prediction = int(self.model.predict(feature_frame)[0])
        probability = float(self.model.predict_proba(feature_frame)[0][prediction])
        prediction_label = self.ml_prediction_label(prediction)

        explanation = self.explanation_service.build_explanation(
            feature_frame,
            feature_values,
            prediction_label,
            round(probability, 4),
            timezone.now().isoformat(),
        )

        top_features = []
        for factor in explanation['top_factors']:
            direction = 'Informational'
            feature_name = factor['feature']
            current_value = factor['current_value']
            if 'General Average' in feature_name:
                if isinstance(feature_values.get('general_average'), (int, float)) and float(feature_values.get('general_average')) < 75:
                    explanation_text = (
                        f"This was one of the indicators considered by the model. The student's current general average is {current_value}, "
                        "which is below the school's academic concern threshold of 75."
                    )
                else:
                    explanation_text = (
                        f"This was one of the indicators considered by the model. The student's current general average is {current_value}, "
                        "which was reviewed alongside the other available indicators."
                    )
            elif 'Failed Subjects' in feature_name:
                explanation_text = (
                    f"This was one of the indicators considered by the model. The student currently has {current_value} failed subject(s) in the reviewed records."
                )
            elif 'Attendance Rate' in feature_name:
                explanation_text = (
                    f"This was one of the indicators considered by the model. The student's current attendance rate is {current_value}."
                )
            elif 'Teacher Behavior Rating' in feature_name:
                explanation_text = (
                    f"This was one of the indicators considered by the model. The latest behavior rating recorded for the student is {current_value}."
                )
            else:
                explanation_text = (
                    f"This was one of the indicators considered by the model while evaluating the student's current risk pattern. "
                    f"Current value: {current_value}."
                )

            top_features.append({
                'feature_name': factor['feature_name'],
                'feature_value': factor['current_value'],
                'importance': factor['importance'],
                'direction': direction,
                'explanation_text': explanation_text,
            })

        explanation_summary = self.explanation_service.build_summary(
            prediction_label,
            round(probability, 4),
            explanation['top_factors'],
        )

        return {
            'prediction': prediction_label,
            'probability': round(probability, 4),
            'prediction_date': timezone.now().isoformat(),
            'top_contributing_features': top_features,
            'explanation': explanation,
            'explanation_summary': explanation_summary,
        }

    def save_prediction(self, student_id: int, result: Dict[str, Any] = None) -> RiskPrediction:
        if result is None:
            result = self.predict_for_student(student_id)

        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise ValueError('Student not found')

        enrollment = active_enrollment_queryset(Enrollment.objects.filter(student=student)).order_by('-academic_year__start_date').first()
        if not enrollment:
            raise ValueError('No active enrollment found')

        with transaction.atomic():
            risk_level = self.application_risk_level(result['prediction'])
            prediction = RiskPrediction.objects.create(
                enrollment=enrollment,
                prediction_type='Academic Risk',
                risk_level=risk_level,
                probability=Decimal(str(result['probability'])),
                model_name='Random Forest',
                model_version='1.0',
                explanation=result.get('explanation_summary', ''),
                review_status='Pending',
            )
            for factor in result['top_contributing_features']:
                PredictionFactor.objects.create(
                    prediction=prediction,
                    feature_name=factor['feature_name'],
                    feature_value=factor['feature_value'],
                    contribution=Decimal(str(factor['importance'])),
                    direction=factor['direction'],
                    explanation_text=factor['explanation_text'],
                )
            return prediction

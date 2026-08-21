import json
import logging
import pickle
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
    def __init__(self) -> None:
        self.model = self._load_model()
        self.label_map = self._load_label_map()
        self.feature_mapping = self._load_feature_mapping()
        self.explanation_service = ExplanationService()

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

    def build_feature_vector(self, student_id: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise ValueError('Student not found')

        enrollment = Enrollment.objects.filter(student=student).order_by('-academic_year__start_date').first()
        if not enrollment:
            raise ValueError('No active enrollment found for student')

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
        source_core_value = latest_behavior.core_value.name if latest_behavior and latest_behavior.core_value else 'Not available'
        source_indicator = latest_behavior.behavior_indicator.name if latest_behavior and latest_behavior.behavior_indicator else 'Not available'

        feature_values = {
            'school_year': str(enrollment.academic_year.name) if enrollment.academic_year else 'Unknown',
            'grade_level': str(enrollment.grade_level.name) if enrollment.grade_level else 'Unknown',
            'section': str(enrollment.section.name) if enrollment.section else 'Unknown',
            'behavior_core_value': source_core_value,
            'behavior_indicator': source_indicator,
            'behavior_teacher_rating': behavior_rating,
            'intervention_type': 'No Intervention' if not interventions.exists() else str(interventions.order_by('-created_at').first().intervention_type),
            'intervention_outcome': 'Not Yet Evaluated',
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
            subject_map = self.feature_mapping.get('subject_feature_map', {})
            normalized_subject_map = {str(name).casefold(): feature for name, feature in subject_map.items()}
            for record in academic_records:
                subject_name = record.subject.name if record.subject else ''
                feature_key = normalized_subject_map.get(str(subject_name).casefold())
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
        for column, value, categories in zip(categorical_columns, (
            feature_values.get(column) for column in categorical_columns
        ), encoder_categories):
            if value not in categories:
                contract_diagnostics.append(
                    f"{column} value '{value}' is not represented in the current model vocabulary."
                )

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
        return encoded_frame, feature_values

    def validate_feature_frame(self, feature_frame: pd.DataFrame, feature_values: Dict[str, Any]) -> None:
        expected_columns = list(getattr(self.model, 'feature_names_in_', []))
        expected_count = int(getattr(self.model, 'n_features_in_', len(expected_columns)))
        if len(feature_frame.columns) != expected_count:
            raise FeatureContractError([f'Feature vector contains {len(feature_frame.columns)} columns; expected {expected_count}.'])
        if list(feature_frame.columns) != expected_columns:
            raise FeatureContractError(['Feature names or order do not match the saved model contract.'])
        numeric_frame = feature_frame.apply(pd.to_numeric, errors='coerce')
        finite_frame = numeric_frame.replace([float('inf'), float('-inf')], pd.NA)
        if finite_frame.isna().any().any():
            raise FeatureContractError(['Feature vector contains a non-numeric or missing value.'])

        diagnostics = feature_values.get('contract_diagnostics', [])
        if diagnostics:
            logger.warning('Prediction blocked by feature contract: %s', diagnostics)
            raise FeatureContractError(diagnostics)

    def predict_for_student(self, student_id: int) -> Dict[str, Any]:
        feature_frame, feature_values = self.build_feature_vector(student_id)
        self.validate_feature_frame(feature_frame, feature_values)
        prediction = int(self.model.predict(feature_frame)[0])
        probability = float(self.model.predict_proba(feature_frame)[0][prediction])
        prediction_label = self.label_map.get(prediction, 'At Risk' if prediction == 1 else 'Not At Risk')

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
            explanation_text = (
                f"{factor['feature']} was among the model's most influential features "
                f"with value {factor['current_value']}; this is global feature importance, "
                f"not a per-student causal contribution."
            )
            top_features.append({
                'feature_name': factor['feature'],
                'feature_value': factor['current_value'],
                'importance': factor['importance'],
                'direction': direction,
                'explanation_text': explanation_text,
            })

        explanation_summary = self.explanation_service.build_summary(prediction_label, explanation['top_factors'])

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

        enrollment = Enrollment.objects.filter(student=student).order_by('-academic_year__start_date').first()
        if not enrollment:
            raise ValueError('No enrollment found')

        with transaction.atomic():
            existing_prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
            if existing_prediction:
                return existing_prediction

            risk_level = 'High' if result['prediction'] == 'At Risk' else 'Low'
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

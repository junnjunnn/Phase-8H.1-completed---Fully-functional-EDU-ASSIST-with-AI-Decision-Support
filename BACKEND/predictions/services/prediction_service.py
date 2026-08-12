import json
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

        behavior_ratings = []
        for record in behavior_assessments:
            if record.rating and record.rating.code:
                behavior_ratings.append(record.rating.code)
        behavior_rating = max(set(behavior_ratings), key=behavior_ratings.count) if behavior_ratings else 'AO'

        feature_values = {
            'school_year': str(enrollment.academic_year.name) if enrollment.academic_year else 'Unknown',
            'grade_level': str(enrollment.grade_level.name) if enrollment.grade_level else 'Unknown',
            'section': str(enrollment.section.name) if enrollment.section else 'Unknown',
            'behavior_core_value': 'Respect',
            'behavior_indicator': 'Shows respect to teachers and peers',
            'behavior_teacher_rating': behavior_rating,
            'intervention_type': 'No Intervention' if not interventions.exists() else 'Academic Monitoring',
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

        if academic_records.exists():
            subject_map = {
                'Mathematics': 'mathematics_grade',
                'English': 'english_grade',
                'Science': 'science_grade',
                'Filipino': 'filipino_grade',
                'Araling Panlipunan': 'araling_panlipunan_grade',
                'ESP': 'esp_grade',
                'MAPEH': 'mapeh_grade',
                'TLE': 'tle_grade',
            }
            for record in academic_records:
                subject_name = record.subject.name if record.subject else ''
                feature_key = subject_map.get(subject_name)
                if feature_key:
                    feature_values[feature_key] = float(record.final_grade or record.grade or 0)

        categorical_columns = self.feature_mapping.get('categorical_columns', [])
        numeric_columns = self.feature_mapping.get('numeric_columns', [])
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
            for category in self.feature_mapping.get('encoder_categories', [])[col_idx]:
                encoded_columns.append(f'{col}_{category}')
                encoded_values.append(1.0 if value == category else 0.0)

        encoded_frame = pd.DataFrame([encoded_values], columns=encoded_columns)
        return encoded_frame, feature_values

    def predict_for_student(self, student_id: int) -> Dict[str, Any]:
        feature_frame, feature_values = self.build_feature_vector(student_id)
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
            direction = 'Positive' if factor['importance'] >= 0.03 else 'Neutral'
            explanation_text = (
                f"{factor['feature']} had {factor['influence'].lower()} with value {factor['current_value']}."
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

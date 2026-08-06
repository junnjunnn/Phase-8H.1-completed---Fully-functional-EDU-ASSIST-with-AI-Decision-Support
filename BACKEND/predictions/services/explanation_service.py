import json
import pickle
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from django.conf import settings

ROOT_DIR = Path(settings.BASE_DIR).parent
MODEL_PATH = ROOT_DIR / 'AI (ML)' / 'models' / 'risk_model.pkl'
FEATURE_MAPPING_PATH = ROOT_DIR / 'AI (ML)' / 'models' / 'feature_mapping.json'

_MODEL = None
_FEATURE_MAPPING = None


class ExplanationService:
    def __init__(self) -> None:
        self.model = self._load_model()
        self.feature_mapping = self._load_feature_mapping()

    def _load_model(self):
        global _MODEL
        if _MODEL is None:
            with MODEL_PATH.open('rb') as fh:
                _MODEL = pickle.load(fh)
        return _MODEL

    def _load_feature_mapping(self) -> Dict[str, Any]:
        global _FEATURE_MAPPING
        if _FEATURE_MAPPING is None:
            with FEATURE_MAPPING_PATH.open('r', encoding='utf-8') as fh:
                _FEATURE_MAPPING = json.load(fh)
        return _FEATURE_MAPPING

    def _humanize_feature_name(self, feature_name: str) -> str:
        mapping = {
            'general_average': 'General Average',
            'attendance_rate': 'Attendance Rate',
            'failed_subjects': 'Failed Subjects',
            'behavior_teacher_rating': 'Teacher Behavior Rating',
            'behavior_teacher_rating_AO': 'Teacher Behavior Rating (AO)',
            'behavior_teacher_rating_SO': 'Teacher Behavior Rating (SO)',
            'behavior_teacher_rating_RO': 'Teacher Behavior Rating (RO)',
            'behavior_teacher_rating_NO': 'Teacher Behavior Rating (NO)',
            'intervention_type': 'Intervention Type',
            'intervention_outcome': 'Intervention Outcome',
            'late_percentage': 'Late Percentage',
            'absent_percentage': 'Absence Percentage',
            'high_grade_count': 'High Grade Count',
            'has_intervention': 'Previous Intervention',
            'number_of_interventions': 'Intervention Count',
            'mathematics_grade': 'Mathematics Grade',
            'english_grade': 'English Grade',
            'science_grade': 'Science Grade',
            'filipino_grade': 'Filipino Grade',
            'araling_panlipunan_grade': 'Araling Panlipunan Grade',
            'esp_grade': 'ESP Grade',
            'mapeh_grade': 'MAPEH Grade',
            'tle_grade': 'TLE Grade',
            'present_days': 'Present Days',
            'absent_days': 'Absent Days',
            'late_days': 'Late Days',
            'excused_absences': 'Excused Absences',
            'school_year': 'School Year',
            'grade_level': 'Grade Level',
            'section': 'Section',
        }
        return mapping.get(feature_name, feature_name.replace('_', ' ').title())

    def _format_value(self, value: Any) -> str:
        if value is None:
            return 'Not available'
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}"
        return str(value)

    def _influence_level(self, importance: float) -> str:
        if importance >= 0.2:
            return 'High Influence'
        if importance >= 0.1:
            return 'Moderate Influence'
        return 'Low Influence'

    def build_summary(self, prediction: str, top_factors: List[Dict[str, Any]]) -> str:
        lines = [f'Prediction: {prediction}', '', 'Top Factors:']
        for factor in top_factors:
            lines.append(f"• {factor['feature']} ({factor['current_value']})")
        return '\n'.join(lines)

    def build_explanation(self, feature_frame, feature_values: Dict[str, Any], prediction: str, probability: float, prediction_date: str) -> Dict[str, Any]:
        if not hasattr(self.model, 'feature_importances_'):
            return {
                'prediction': prediction,
                'probability': round(probability, 4),
                'model': 'Random Forest',
                'prediction_timestamp': prediction_date,
                'top_factors': [],
            }

        importances = pd.Series(self.model.feature_importances_, index=feature_frame.columns)
        ranked = importances.sort_values(ascending=False)
        top_factors = []

        for feature_name, importance in ranked.head(5).items():
            current_value = feature_values.get(feature_name)
            if current_value is None:
                current_value = feature_frame.iloc[0][feature_name]
            if float(importance) <= 0:
                continue

            top_factors.append({
                'feature_name': feature_name,
                'feature': self._humanize_feature_name(feature_name),
                'current_value': self._format_value(current_value),
                'importance': round(float(importance), 4),
                'influence': self._influence_level(float(importance)),
            })

        return {
            'prediction': prediction,
            'probability': round(probability, 4),
            'model': 'Random Forest',
            'prediction_timestamp': prediction_date,
            'top_factors': top_factors,
        }

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from predictions.services.prediction_service import PredictionService
print('Service import OK')
service = PredictionService()
print('Model loaded:', type(service.model).__name__)
print('Feature mapping keys:', sorted(service.feature_mapping.keys()))

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAuthorizedStaff
from audit.models import AuditLog
from common.authorization import authorized_students_queryset
from students.models import Student
from .services.prediction_service import PredictionService


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAuthorizedStaff])
def predict_student_view(request, student_id):
    try:
        # Check if the user is authorized to access this student
        authorized_qs = authorized_students_queryset(request.user, Student.objects.all())
        if not authorized_qs.filter(id=student_id).exists():
            return Response(
                {'detail': 'You do not have permission to generate a prediction for this student.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service = PredictionService()
        result = service.predict_for_student(student_id)
        prediction = service.save_prediction(student_id, result=result)

        object_id = (
            f"student:{student_id};prediction:{prediction.id};"
            f"result:{result['prediction']};prob:{result['probability']}"
        )
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='PREDICTION_GENERATED',
            module='predictions',
            object_type='RiskPrediction',
            object_id=object_id,
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return Response({
            'student': student_id,
            'prediction': result['prediction'],
            'probability': result['probability'],
            'model': 'Random Forest',
            'generated_at': result['prediction_date'],
            'prediction_id': prediction.id,
            'explanation': result.get('explanation', {}),
        }, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

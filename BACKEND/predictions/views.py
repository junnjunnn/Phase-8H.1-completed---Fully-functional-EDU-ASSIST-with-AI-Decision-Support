from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAuthorizedStaff
from audit.models import AuditLog
from common.authorization import active_enrollment_queryset, authorized_students_queryset
from academics.models import Enrollment
from students.models import Student
from .services.prediction_service import FeatureContractError, PredictionService


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAuthorizedStaff])
def predict_student_view(request, student_id):
    try:
        # Check if the user is authorized to access this student
        authorized_qs = authorized_students_queryset(request.user, Student.objects.all(), include_archived=True)
        if not authorized_qs.filter(id=student_id).exists():
            return Response(
                {'detail': 'You do not have permission to generate a prediction for this student.'},
                status=status.HTTP_403_FORBIDDEN
            )

        student = authorized_qs.filter(id=student_id, student_status='active').first()
        eligible_enrollment = active_enrollment_queryset(Enrollment.objects.filter(student_id=student_id)).order_by('-academic_year__start_date').first()
        if not student or not eligible_enrollment:
            return Response(
                {'detail': 'Prediction generation is only available for students with an active enrollment and current academic context.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
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

        persisted_prediction_label = 'At Risk' if prediction.risk_level == 'High' else 'Not At Risk'
        return Response({
            'student': student_id,
            'prediction': persisted_prediction_label,
            'probability': float(prediction.probability),
            'model': 'Random Forest',
            'generated_at': prediction.prediction_date.isoformat(),
            'prediction_id': prediction.id,
            'explanation': prediction.explanation,
        }, status=status.HTTP_200_OK)
    except FeatureContractError as exc:
        return Response(
            {
                'error': str(exc),
                'diagnostics': exc.diagnostics,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except Exception as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

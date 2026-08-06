from rest_framework import generics, permissions

from accounts.models import UserProfile
from .models import Student
from .serializers import StudentSerializer


class StudentListView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Student.objects.none()

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Student.objects.none()

        role_name = profile.role_name if profile else 'NONE'
        if role_name in {'SUPER_ADMIN', 'SCHOOL_ADMIN'}:
            return Student.objects.all()
        if role_name in {'TEACHER', 'GUIDANCE'}:
            return Student.objects.filter(enrollments__section__in=profile.assigned_sections.all()).distinct()
        return Student.objects.none()

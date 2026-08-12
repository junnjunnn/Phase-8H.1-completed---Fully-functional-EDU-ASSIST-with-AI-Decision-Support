import django_filters
from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff, IsSchoolAdmin
from common.audit import AuditMixin
from common.authorization import authorized_students_queryset
from academics.models import AcademicYear, GradeLevel, Section
from .models import Student
from .serializers import StudentSerializer


class StudentFilter(django_filters.FilterSet):
    grade_level = django_filters.ModelChoiceFilter(field_name='enrollments__grade_level', queryset=GradeLevel.objects.all())
    section = django_filters.ModelChoiceFilter(field_name='enrollments__section', queryset=Section.objects.all())
    academic_year = django_filters.ModelChoiceFilter(field_name='enrollments__academic_year', queryset=AcademicYear.objects.all())

    class Meta:
        model = Student
        fields = ['student_status', 'grade_level', 'section', 'academic_year']


class StudentViewSet(AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Student.objects.prefetch_related('enrollments__grade_level', 'enrollments__section', 'enrollments__academic_year').order_by('last_name', 'first_name')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = StudentFilter
    search_fields = ['lrn', 'first_name', 'last_name']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        return authorized_students_queryset(self.request.user, qs)

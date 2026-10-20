from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter

from accounts.permissions import IsAuthorizedStaff, IsRegistrarOrSchoolAdmin, IsStudentAccessAllowed
from common.audit import AuditMixin
from common.authorization import authorized_students_queryset, requested_lifecycle_status
from academics.models import AcademicYear, Enrollment, GradeLevel, Section
from .models import Student
from .serializers import StudentSerializer


class StudentViewSet(AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Student.objects.prefetch_related('enrollments__grade_level', 'enrollments__section', 'enrollments__academic_year').order_by('last_name', 'first_name')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAccessAllowed]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['lrn', 'first_name', 'last_name']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsRegistrarOrSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsStudentAccessAllowed()]

    def get_queryset(self):
        qs = super().get_queryset()
        status = requested_lifecycle_status(self.request, self.request.query_params.get('include_archived') == 'true')
        include_archived = status != 'active'
        if status == 'active':
            qs = qs.filter(student_status='active')
        elif status == 'archived':
            qs = qs.exclude(student_status='active')
        elif self.request.query_params.get('student_status'):
            qs = qs.filter(student_status=self.request.query_params['student_status'])

        if self.action == 'list':
            requested_context_filters = any(
                self.request.query_params.get(key)
                for key in ('academic_year', 'grade_level', 'section')
            )
            enrollment_filters = {}
            if requested_context_filters and not include_archived:
                enrollment_filters = {
                    'enrollment_status': 'active',
                    'academic_year__is_active': True,
                    'section__is_active': True,
                    'section__academic_year__is_active': True,
                    'section__grade_level__is_active': True,
                }

                grade_level_id = self.request.query_params.get('grade_level')
                if grade_level_id:
                    enrollment_filters['grade_level_id'] = grade_level_id

                section_id = self.request.query_params.get('section')
                if section_id:
                    enrollment_filters['section_id'] = section_id

                academic_year_id = self.request.query_params.get('academic_year')
                if academic_year_id:
                    enrollment_filters['academic_year_id'] = academic_year_id

                if enrollment_filters:
                    student_ids = Enrollment.objects.filter(**enrollment_filters).values_list('student_id', flat=True)
                    qs = qs.filter(id__in=student_ids).distinct()
        return authorized_students_queryset(self.request.user, qs, include_archived=include_archived)

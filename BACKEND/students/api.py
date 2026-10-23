from django.db.models import Exists, OuterRef
from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import ValidationError

from academics.active_academic_year import get_active_academic_year
from academics.models import AcademicYear, Enrollment, GradeLevel, Section
from accounts.permissions import IsAuthorizedStaff, IsRegistrarOrSchoolAdmin, IsStudentAccessAllowed
from common.audit import AuditMixin
from common.authorization import authorized_students_queryset, requested_lifecycle_status
from .models import Student
from .serializers import StudentSerializer
from .bulk_import import StudentImportConfirmView, StudentImportPreviewView, StudentImportTemplateView


class StudentViewSet(AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Student.objects.prefetch_related('enrollments__grade_level', 'enrollments__section', 'enrollments__academic_year', 'enrollments__strand').order_by('last_name', 'first_name')
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
        enrollment_type = self.request.query_params.get('enrollment_type')
        student_ids = self.request.query_params.get('student_ids')

        if self.action == 'list' and student_ids is not None:
            ids = [value.strip() for value in student_ids.split(',') if value.strip()]
            if not ids or any(not value.isdecimal() for value in ids):
                raise ValidationError({'student_ids': 'Provide a comma-separated list of valid student IDs.'})
            qs = qs.filter(pk__in=ids)

        if self.action == 'list' and enrollment_type:
            valid_enrollment_types = {
                'continuing_student',
                'returning_student',
                'new_student',
                'transferee',
            }
            if enrollment_type not in valid_enrollment_types:
                raise ValidationError({
                    'enrollment_type': 'Enrollment type must be continuing_student, returning_student, new_student, or transferee.',
                })

            active_year = get_active_academic_year()
            has_active_year_enrollment = Enrollment.objects.filter(
                student_id=OuterRef('pk'),
                academic_year_id=active_year.pk,
            )
            qs = qs.annotate(
                has_active_year_enrollment=Exists(has_active_year_enrollment),
            ).filter(has_active_year_enrollment=False)

            if enrollment_type in {'continuing_student', 'returning_student'}:
                preceding_years = AcademicYear.objects.filter(
                    start_date__lt=active_year.start_date,
                ).order_by('-start_date')
                preceding_year = preceding_years.first()
                if preceding_year is None:
                    raise ValidationError({
                        'enrollment_type': 'A preceding academic year is not configured, so prior-year enrollment eligibility cannot be determined.',
                    })
                if (
                    preceding_years.filter(start_date=preceding_year.start_date).count() != 1
                    or preceding_year.end_date >= active_year.start_date
                ):
                    raise ValidationError({
                        'enrollment_type': 'Academic-year dates do not identify one unambiguous preceding year. Ask an administrator to review Academic Year Management.',
                    })

                if enrollment_type == 'continuing_student':
                    eligible_history = Enrollment.objects.filter(
                        student_id=OuterRef('pk'),
                        academic_year_id=preceding_year.pk,
                    )
                else:
                    eligible_history = Enrollment.objects.filter(
                        student_id=OuterRef('pk'),
                        academic_year__start_date__lt=preceding_year.start_date,
                    )
                qs = qs.annotate(
                    has_eligible_history=Exists(eligible_history),
                ).filter(has_eligible_history=True)
            elif enrollment_type == 'new_student':
                has_prior_enrollment = Enrollment.objects.filter(
                    student_id=OuterRef('pk'),
                )
                qs = qs.annotate(
                    has_prior_enrollment=Exists(has_prior_enrollment),
                ).filter(has_prior_enrollment=False)

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
                for key in ('academic_year', 'grade_level', 'section', 'strand')
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

                strand_id = self.request.query_params.get('strand')
                if strand_id:
                    enrollment_filters['strand_id'] = strand_id

                academic_year_id = self.request.query_params.get('academic_year')
                if academic_year_id:
                    enrollment_filters['academic_year_id'] = academic_year_id

                if enrollment_filters:
                    student_ids = Enrollment.objects.filter(**enrollment_filters).values_list('student_id', flat=True)
                    qs = qs.filter(id__in=student_ids).distinct()
        return authorized_students_queryset(self.request.user, qs, include_archived=include_archived)

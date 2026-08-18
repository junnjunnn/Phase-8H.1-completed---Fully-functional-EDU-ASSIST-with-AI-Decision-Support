from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff, IsAcademicReferenceAccessAllowed, IsEnrollmentAccessAllowed, IsRegistrarOrSchoolAdmin, IsSchoolAdmin, IsTeacherOrSchoolAdmin
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Strand, Subject, TeacherAssignment
from .serializers import AcademicRecordSerializer, AcademicYearSerializer, EnrollmentSerializer, GradeLevelSerializer, SectionSerializer, StrandSerializer, SubjectSerializer, TeacherAssignmentSerializer


class AcademicYearViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class GradeLevelViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = GradeLevel.objects.all()
    serializer_class = GradeLevelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class SectionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Section.objects.select_related('grade_level', 'academic_year', 'adviser', 'strand').all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if get_user_scope(self.request.user) == 'teacher':
            assigned_sections = self.request.user.profile.assigned_sections.values_list('pk', flat=True)
            return queryset.filter(pk__in=assigned_sections).distinct()
        return queryset

    def _sync_teacher_assignment(self, section, adviser):
        previous_adviser_id = None
        if section.pk:
            previous_adviser_id = Section.objects.filter(pk=section.pk).values_list('adviser_id', flat=True).first()

        if adviser and getattr(adviser, 'pk', None):
            adviser_profile = getattr(adviser, 'profile', None)
            if adviser_profile:
                adviser_profile.assigned_sections.add(section)

        if previous_adviser_id and adviser and previous_adviser_id != adviser.pk:
            previous_user = get_user_model().objects.filter(pk=previous_adviser_id).first()
            previous_profile = getattr(previous_user, 'profile', None)
            if previous_profile:
                previous_profile.assigned_sections.remove(section)
        elif previous_adviser_id and not adviser:
            previous_user = get_user_model().objects.filter(pk=previous_adviser_id).first()
            previous_profile = getattr(previous_user, 'profile', None)
            if previous_profile:
                previous_profile.assigned_sections.remove(section)

    def perform_create(self, serializer):
        instance = serializer.save()
        self._sync_teacher_assignment(instance, instance.adviser)
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self._sync_teacher_assignment(instance, instance.adviser)
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class StrandViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Strand.objects.all()
    serializer_class = StrandSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]


class SubjectViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Subject.objects.select_related('grade_level', 'strand').all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class TeacherAssignmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = TeacherAssignment.objects.select_related('teacher', 'academic_year', 'grade_level', 'section', 'subject').all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class EnrollmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Enrollment.objects.select_related('student', 'academic_year', 'grade_level', 'section', 'strand').all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrollmentAccessAllowed]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'academic_year', 'grade_level', 'section', 'strand', 'enrollment_status']
    search_fields = ['student__first_name', 'student__last_name', 'student__lrn']
    ordering_fields = ['enrollment_date', 'created_at']
    ordering = ['-enrollment_date']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsRegistrarOrSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsEnrollmentAccessAllowed()]

    def get_queryset(self):
        return get_authorized_enrollment_queryset(self.request.user, super().get_queryset())

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )


class AcademicRecordViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicRecord.objects.select_related('enrollment', 'subject', 'academic_year', 'encoded_by').all()
    serializer_class = AcademicRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment', 'enrollment__student', 'academic_year', 'subject', 'grading_period_type', 'quarter', 'semester']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'subject__name']
    ordering_fields = ['created_at', 'grade']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsTeacherOrSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]

    def _teacher_assignment_matches(self, payload=None, instance=None):
        user = self.request.user
        if get_user_scope(user) != 'teacher':
            return True

        target_enrollment = payload.get('enrollment') if payload else getattr(instance, 'enrollment', None)
        target_subject = payload.get('subject') if payload else getattr(instance, 'subject', None)

        if not target_enrollment or not target_subject:
            return False

        return TeacherAssignment.objects.filter(
            teacher=user,
            academic_year=target_enrollment.academic_year,
            grade_level=target_enrollment.grade_level,
            section=target_enrollment.section,
            subject=target_subject,
            is_active=True,
        ).exists()

    def get_queryset(self):
        qs = get_authorized_enrollment_queryset(self.request.user, super().get_queryset(), enrollment_field='enrollment')
        scope = get_user_scope(self.request.user)
        if scope == 'teacher':
            assigned_sections = self.request.user.profile.assigned_sections.values_list('pk', flat=True)
            qs = qs.filter(enrollment__section__in=assigned_sections)

            assigned_subjects = TeacherAssignment.objects.filter(
                teacher=self.request.user,
                is_active=True,
            ).values_list('subject_id', flat=True)
            if assigned_subjects:
                qs = qs.filter(subject__in=assigned_subjects)
        return qs

    def perform_create(self, serializer):
        if not self._teacher_assignment_matches(payload=serializer.validated_data):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You can only encode grades for your assigned subject and section.')

        instance = serializer.save(encoded_by=self.request.user)
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        if not self._teacher_assignment_matches(payload=serializer.validated_data, instance=serializer.instance):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You can only edit grades for your assigned subject and section.')

        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

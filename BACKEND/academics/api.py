from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.auth import get_user_model

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff, IsAcademicReferenceAccessAllowed, IsEnrollmentAccessAllowed, IsRegistrarOrSchoolAdmin, IsSchoolAdmin, IsTeacherOrSchoolAdmin
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from common.authorization import teacher_assignment_queryset, teacher_section_queryset
from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Strand, Subject, TeacherAssignment
from .academic_divisions import ACADEMIC_DIVISIONS, grade_levels_for_division
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

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset

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
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True, grade_level__is_active=True, academic_year__is_active=True)
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
    queryset = Subject.objects.select_related('grade_level', 'strand').prefetch_related('grade_levels').all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    @action(detail=False, methods=['get'], url_path='academic-divisions')
    def academic_divisions(self, request):
        return Response([
            {
                'value': division,
                'label': label,
                'grade_levels': [
                    {'id': grade.id, 'name': grade.name, 'school_level': grade.school_level}
                    for grade in grade_levels_for_division(division)
                ],
            }
            for division, label in ACADEMIC_DIVISIONS.items()
        ])

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

    def get_queryset(self):
        queryset = super().get_queryset()
        if get_user_scope(self.request.user) == 'teacher':
            return queryset.filter(teacher=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        payload = request.data.copy()
        subjects = payload.pop('subjects', None)
        if subjects is None:
            return super().create(request, *args, **kwargs)
        if not isinstance(subjects, list) or not subjects:
            raise ValidationError({'subjects': 'Select at least one subject.'})
        if payload.get('assignment_type', 'SUBJECT') != 'SUBJECT':
            raise ValidationError({'subjects': 'Class Adviser assignments cannot include subjects.'})

        created = []
        with transaction.atomic():
            for subject_id in subjects:
                subject_payload = payload.copy()
                subject_payload['subject'] = subject_id
                serializer = self.get_serializer(data=subject_payload)
                serializer.is_valid(raise_exception=True)
                created.append(serializer.save())

        response_serializer = self.get_serializer(created, many=True)
        return Response(response_serializer.data, status=201)

    @action(detail=False, methods=['get'], url_path='my-context')
    def my_context(self, request):
        if get_user_scope(request.user) != 'teacher':
            return Response({'detail': 'This context is available to teachers.'}, status=403)

        assignments = list(self.get_queryset().filter(is_active=True))
        adviser_assignment_sections = TeacherAssignment.objects.filter(
            teacher=request.user, assignment_type='ADVISER', is_active=True,
        ).values('section_id')
        advisory_sections = Section.objects.select_related('grade_level', 'academic_year', 'adviser').filter(
            Q(adviser=request.user) | Q(pk__in=adviser_assignment_sections)
        ).distinct().order_by('academic_year__start_date', 'grade_level__order', 'name')
        subject_assignments = self.get_serializer(assignments, many=True).data
        advisory = []
        for section in advisory_sections:
            advisory.append({
                'section': section.id,
                'section_name': section.name,
                'grade_level': section.grade_level_id,
                'grade_level_name': section.grade_level.name,
                'academic_year': section.academic_year_id,
                'academic_year_name': section.academic_year.name,
                'student_count': section.enrollments.filter(enrollment_status='active').count(),
                'role': 'Adviser',
            })
        return Response({
            'advisory_classes': advisory,
            'subject_assignments': subject_assignments,
        })

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

    def create(self, request, *args, **kwargs):
        students = request.data.get('students')
        if students is None:
            return super().create(request, *args, **kwargs)
        if not isinstance(students, list) or not students:
            raise ValidationError({'students': 'Select at least one student.'})
        payload = request.data.copy()
        payload.pop('students', None)
        created = []
        with transaction.atomic():
            for student_id in students:
                student_payload = payload.copy()
                student_payload['student'] = student_id
                serializer = self.get_serializer(data=student_payload)
                serializer.is_valid(raise_exception=True)
                created.append(serializer.save())
        return Response(self.get_serializer(created, many=True).data, status=201)

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
            active_assignments = teacher_assignment_queryset(self.request.user)
            if active_assignments.exists():
                matching_assignment = active_assignments.filter(
                    academic_year_id=OuterRef('academic_year_id'),
                    grade_level_id=OuterRef('enrollment__grade_level_id'),
                    section_id=OuterRef('enrollment__section_id'),
                    subject_id=OuterRef('subject_id'),
                )
                qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment)).filter(has_teacher_assignment=True)
        return qs

    def perform_create(self, serializer):
        if not self._teacher_assignment_matches(payload=serializer.validated_data):
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
            raise PermissionDenied('You can only edit grades for your assigned subject and section.')

        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_create_or_update(self, request):
        payload = request.data
        if not isinstance(payload, list):
            raise ValidationError({'detail': 'Bulk grade payload must be a list of records.'})

        if not payload:
            return Response({'results': [], 'count': 0}, status=201)

        results = []
        with transaction.atomic():
            for index, item in enumerate(payload):
                if not isinstance(item, dict):
                    raise ValidationError({'detail': f'Record at index {index} must be an object.'})

                record_id = item.get('id')
                existing_record = None
                if not record_id:
                    enrollment_id = item.get('enrollment')
                    subject_id = item.get('subject')
                    academic_year_id = item.get('academic_year')
                    grading_period_type = item.get('grading_period_type')
                    quarter = item.get('quarter')
                    semester = item.get('semester')

                    if enrollment_id and subject_id and academic_year_id and grading_period_type:
                        matching_qs = AcademicRecord.objects.filter(
                            enrollment_id=enrollment_id,
                            subject_id=subject_id,
                            academic_year_id=academic_year_id,
                            grading_period_type=grading_period_type,
                        )
                        if quarter is not None:
                            matching_qs = matching_qs.filter(quarter=quarter)
                        if semester is not None:
                            matching_qs = matching_qs.filter(semester=semester)
                        existing_record = matching_qs.order_by('-created_at').first()

                if record_id:
                    try:
                        instance = AcademicRecord.objects.select_related('enrollment', 'subject', 'academic_year').get(pk=record_id)
                    except AcademicRecord.DoesNotExist:
                        raise ValidationError({'detail': f'Academic record {record_id} was not found.'})
                    serializer = self.get_serializer(instance, data=item, partial=True, context={'request': request})
                elif existing_record:
                    serializer = self.get_serializer(existing_record, data=item, partial=True, context={'request': request})
                else:
                    serializer = self.get_serializer(data=item, context={'request': request})

                serializer.is_valid(raise_exception=True)
                if not self._teacher_assignment_matches(payload=serializer.validated_data, instance=getattr(serializer, 'instance', None)):
                    raise ValidationError({'detail': 'You can only save grades for your assigned subject and section.'})

                created_or_updated = serializer.save(encoded_by=request.user if request.user.is_authenticated else None)
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='UPDATE' if record_id or existing_record else 'CREATE',
                    module=self.serializer_class.Meta.model._meta.app_label,
                    object_type=self.serializer_class.Meta.model.__name__,
                    object_id=str(created_or_updated.pk),
                )
                results.append(created_or_updated)

        serialized = self.get_serializer(results, many=True).data
        return Response({'results': serialized, 'count': len(serialized)}, status=201)

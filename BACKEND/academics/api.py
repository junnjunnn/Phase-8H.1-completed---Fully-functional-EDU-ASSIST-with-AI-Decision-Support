from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff, IsAcademicReferenceAccessAllowed, IsEnrollmentAccessAllowed, IsRegistrarOrSchoolAdmin, IsSchoolAdmin, IsTeacherOrSchoolAdmin
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from common.authorization import active_enrollment_queryset, archived_enrollment_queryset, filter_lifecycle_queryset, requested_lifecycle_status, teacher_assignment_queryset, teacher_section_queryset
from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Specialization, Strand, Subject, TeacherAssignment
from .academic_divisions import ACADEMIC_DIVISIONS, grade_levels_for_division
from .adviser_assignments import assign_section_adviser, remove_section_adviser
from .serializers import AcademicRecordSerializer, AcademicYearSerializer, EnrollmentSerializer, GradeLevelSerializer, SectionSerializer, SpecializationSerializer, StrandSerializer, SubjectSerializer, TeacherAssignmentSerializer


class AcademicYearViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.method in ['PUT', 'PATCH']:
            return queryset
        status = requested_lifecycle_status(self.request, self.request.query_params.get('include_archived') == 'true')
        return filter_lifecycle_queryset(queryset, status, lambda qs: qs.filter(is_active=True), lambda qs: qs.filter(is_active=False))

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
        include_archived = self.request.query_params.get('include_archived') == 'true'
        status = requested_lifecycle_status(self.request, include_archived)
        if self.request.query_params.get('active_only') == 'true' and 'status' not in self.request.query_params:
            status = 'active'
        queryset = filter_lifecycle_queryset(queryset, status, lambda qs: qs.filter(is_active=True), lambda qs: qs.filter(is_active=False))

        school_level = self.request.query_params.get('school_level')
        if school_level:
            normalized = str(school_level).strip().lower()
            school_level_map = {
                'all': None,
                'elementary': 'Elementary',
                'junior high school': 'Junior High School',
                'jhs': 'Junior High School',
                'senior high school': 'Senior High School',
                'shs': 'Senior High School',
            }
            canonical = school_level_map.get(normalized)
            if canonical:
                queryset = queryset.filter(school_level=canonical)

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
    queryset = Section.objects.select_related('grade_level', 'academic_year', 'adviser', 'strand', 'specialization').all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAcademicReferenceAccessAllowed()]

    def get_queryset(self):
        queryset = super().get_queryset()
        include_archived = self.request.query_params.get('include_archived') == 'true'
        status = requested_lifecycle_status(self.request, include_archived)
        if self.request.query_params.get('active_only') == 'true' and 'status' not in self.request.query_params:
            status = 'active'
        if self.action not in {'retrieve', 'update', 'partial_update'}:
            queryset = filter_lifecycle_queryset(
                queryset,
                status,
                lambda qs: qs.filter(is_active=True, grade_level__is_active=True, academic_year__is_active=True),
                lambda qs: qs.filter(Q(is_active=False) | Q(grade_level__is_active=False) | Q(academic_year__is_active=False)),
            )

        grade_level = self.request.query_params.get('grade_level')
        if grade_level:
            queryset = queryset.filter(grade_level_id=grade_level)

        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)

        strand = self.request.query_params.get('strand')
        if strand:
            queryset = queryset.filter(strand_id=strand)

        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization_id=specialization)

        if get_user_scope(self.request.user) == 'teacher':
            assigned_sections = self.request.user.profile.assigned_sections.values_list('pk', flat=True)
            return queryset.filter(pk__in=assigned_sections).distinct()
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


class SpecializationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Specialization.objects.select_related('strand').all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAcademicReferenceAccessAllowed]

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True, strand__is_active=True)
        strand = self.request.query_params.get('strand')
        if strand:
            queryset = queryset.filter(strand_id=strand)
        return queryset


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

    def get_queryset(self):
        queryset = super().get_queryset()
        include_archived = self.request.query_params.get('include_archived') == 'true'
        status = requested_lifecycle_status(self.request, include_archived)
        if self.request.query_params.get('active_only') == 'true' and 'status' not in self.request.query_params:
            status = 'active'
        queryset = filter_lifecycle_queryset(queryset, status, lambda qs: qs.filter(is_active=True), lambda qs: qs.filter(is_active=False))
        grade_level = self.request.query_params.get('grade_level')
        if grade_level:
            queryset = queryset.filter(Q(grade_levels__id=grade_level) | Q(grade_level_id=grade_level)).distinct()
        return queryset

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
            if request.data.get('assignment_type', 'SUBJECT') == 'ADVISER':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                instance, created = assign_section_adviser(
                    serializer.validated_data['section'],
                    serializer.validated_data['teacher'],
                )
                serializer.instance = instance
                if created:
                    AuditLog.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        action='CREATE',
                        module=self.serializer_class.Meta.model._meta.app_label,
                        object_type=self.serializer_class.Meta.model.__name__,
                        object_id=str(instance.pk),
                    )
                return Response(serializer.data, status=201 if created else 200)
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        requested_type = request.data.get('assignment_type', instance.assignment_type)

        if requested_type != instance.assignment_type:
            raise ValidationError({
                'assignment_type': 'Create a separate assignment instead of changing an assignment type.',
            })
        if instance.assignment_type != 'ADVISER':
            return super().update(request, partial=partial, **kwargs)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data

        if values.get('is_active', instance.is_active):
            assignment, changed = assign_section_adviser(
                values.get('section', instance.section),
                values.get('teacher', instance.teacher),
                replacing_assignment=instance,
            )
        else:
            removed_assignments = (
                remove_section_adviser(instance.section, teacher_id=instance.teacher_id)
                if instance.is_active else []
            )
            changed = any(item.pk == instance.pk for item in removed_assignments)
            if changed:
                instance.is_active = False
            assignment = instance

        serializer.instance = assignment
        if changed:
            AuditLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='UPDATE',
                module=self.serializer_class.Meta.model._meta.app_label,
                object_type=self.serializer_class.Meta.model.__name__,
                object_id=str(assignment.pk),
            )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-context')
    def my_context(self, request):
        if get_user_scope(request.user) != 'teacher':
            return Response({'detail': 'This context is available to teachers.'}, status=403)

        assignments = list(self.get_queryset().filter(is_active=True, assignment_type='SUBJECT'))
        adviser_assignment_sections = TeacherAssignment.objects.filter(
            teacher=request.user, assignment_type='ADVISER', is_active=True,
        ).values('section_id')
        advisory_sections = Section.objects.select_related('grade_level', 'academic_year', 'adviser').filter(
            is_active=True,
            grade_level__is_active=True,
            academic_year__is_active=True,
        ).filter(
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
        queryset = super().get_queryset()
        include_archived = self.request.query_params.get('include_archived') == 'true'
        status = requested_lifecycle_status(self.request, include_archived)
        if status == 'active':
            queryset = active_enrollment_queryset(queryset)
        elif status == 'archived':
            queryset = archived_enrollment_queryset(queryset)
        elif self.request.query_params.get('enrollment_status'):
            queryset = queryset.filter(enrollment_status=self.request.query_params['enrollment_status'])
        return get_authorized_enrollment_queryset(
            self.request.user, queryset, lifecycle_status=status,
        )

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
        status = requested_lifecycle_status(self.request, self.request.query_params.get('include_archived') == 'true')
        qs = get_authorized_enrollment_queryset(
            self.request.user,
            super().get_queryset(),
            enrollment_field='enrollment',
            lifecycle_status=status,
        )
        if status == 'active':
            qs = qs.filter(enrollment__in=active_enrollment_queryset(Enrollment.objects.all()))
        elif status == 'archived':
            qs = qs.filter(enrollment__in=archived_enrollment_queryset(Enrollment.objects.all()))
        scope = get_user_scope(self.request.user)
        if scope == 'teacher':
            assignment_queryset = teacher_assignment_queryset(self.request.user, active_only=False)
            if status == 'active':
                assignment_queryset = assignment_queryset.filter(is_active=True)
            elif status == 'archived':
                assignment_queryset = assignment_queryset.filter(is_active=False)
            # Check if teacher is a section adviser
            adviser_assignments = assignment_queryset.filter(assignment_type='ADVISER')
            has_adviser_role = adviser_assignments.exists()
            
            # Get the teacher's subject assignments
            active_subject_assignments = assignment_queryset.filter(assignment_type='SUBJECT')
            has_subject_assignments = active_subject_assignments.exists()
            
            # Build the filter based on adviser and subject roles
            if has_adviser_role:
                # Adviser can see all records for students in their advised sections
                advised_section_ids = adviser_assignments.values_list('section_id', flat=True)
                
                if has_subject_assignments:
                    # Teacher with both adviser and subject roles
                    matching_assignment = active_subject_assignments.filter(
                        academic_year_id=OuterRef('academic_year_id'),
                        grade_level_id=OuterRef('enrollment__grade_level_id'),
                        section_id=OuterRef('enrollment__section_id'),
                        subject_id=OuterRef('subject_id'),
                    )
                    qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment))
                    qs = qs.filter(
                        Q(enrollment__section_id__in=advised_section_ids) |
                        Q(has_teacher_assignment=True)
                    )
                else:
                    # Adviser with no subject assignments - just show all records for advised sections
                    qs = qs.filter(enrollment__section_id__in=advised_section_ids)
            elif has_subject_assignments:
                # Teacher without adviser role - only show records for their subject assignments
                matching_assignment = active_subject_assignments.filter(
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

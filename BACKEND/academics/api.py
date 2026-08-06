from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff, IsTeacherOrSchoolAdmin
from accounts.utils import get_authorized_enrollment_queryset
from .models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Strand, Subject
from .serializers import AcademicRecordSerializer, AcademicYearSerializer, EnrollmentSerializer, GradeLevelSerializer, SectionSerializer, StrandSerializer, SubjectSerializer


class AcademicYearViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class GradeLevelViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = GradeLevel.objects.all()
    serializer_class = GradeLevelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class SectionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Section.objects.select_related('grade_level', 'academic_year', 'adviser').all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class StrandViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Strand.objects.all()
    serializer_class = StrandSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class SubjectViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Subject.objects.select_related('grade_level', 'strand').all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class EnrollmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Enrollment.objects.select_related('student', 'academic_year', 'grade_level', 'section', 'strand').all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'academic_year', 'grade_level', 'section', 'strand', 'enrollment_status']
    search_fields = ['student__first_name', 'student__last_name', 'student__lrn']
    ordering_fields = ['enrollment_date', 'created_at']
    ordering = ['-enrollment_date']

    def get_queryset(self):
        return get_authorized_enrollment_queryset(self.request.user, super().get_queryset())


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

    def get_queryset(self):
        return get_authorized_enrollment_queryset(self.request.user, super().get_queryset(), enrollment_field='enrollment')

    def perform_create(self, serializer):
        instance = serializer.save(encoded_by=self.request.user)
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

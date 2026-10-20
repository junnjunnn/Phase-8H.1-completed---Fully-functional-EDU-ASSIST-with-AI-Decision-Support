from typing import Iterable
from django.db import models
from django.db.models import QuerySet


VALID_LIFECYCLE_STATUSES = {'active', 'archived', 'all'}


def requested_lifecycle_status(request, legacy_include_archived=False):
    """Resolve the public lifecycle contract while preserving legacy callers."""
    status = request.query_params.get('status')
    if status:
        status = status.lower()
        if status not in VALID_LIFECYCLE_STATUSES:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'status': 'Status must be active, archived, or all.'})
        return status
    if legacy_include_archived:
        return 'all'
    return 'active'


def filter_lifecycle_queryset(queryset, status, active_filter, archived_filter):
    """Apply an explicit active, archived, or combined queryset filter."""
    if status == 'active':
        return active_filter(queryset)
    if status == 'archived':
        return archived_filter(queryset)
    return queryset


def _get_profile(user):
    try:
        if user is None or not getattr(user, 'is_authenticated', False):
            return None
        if getattr(user, 'pk', None) is None:
            return getattr(user, 'profile', None)
        from accounts.models import UserProfile
        return UserProfile.objects.filter(user_id=user.pk).select_related('user').first() or getattr(user, 'profile', None)
    except Exception:
        return None


def get_user_scope(user: object) -> str:
    """Return a canonical scope string for the provided user.

    Scopes:
      - 'schoolwide' : SUPER_ADMIN or SCHOOL_ADMIN
      - 'registrar' : REGISTRAR
      - 'teacher' : TEACHER
      - 'guidance' : GUIDANCE
      - 'none' : unauthenticated or unknown
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return 'none'
    profile = _get_profile(user)
    role_name = getattr(profile, 'role_name', None)
    if role_name in {'SUPER_ADMIN', 'SCHOOL_ADMIN'}:
        return 'schoolwide'
    if role_name == 'REGISTRAR':
        return 'registrar'
    if role_name == 'TEACHER':
        return 'teacher'
    if role_name == 'GUIDANCE':
        return 'guidance'
    return 'none'


def teacher_assignment_queryset(user: object, active_only: bool = True):
    """Return the teacher's authoritative subject assignments."""
    from academics.models import TeacherAssignment

    queryset = TeacherAssignment.objects.filter(teacher=user)
    if active_only:
        queryset = queryset.filter(is_active=True)
    return queryset


def _lifecycle_status(lifecycle_status='active', include_archived=None):
    if include_archived is not None:
        lifecycle_status = 'all' if include_archived else 'active'
    if lifecycle_status not in VALID_LIFECYCLE_STATUSES:
        raise ValueError('lifecycle_status must be active, archived, or all')
    return lifecycle_status


def get_adviser_sections(user: object, lifecycle_status='active', include_archived=None):
    """Return adviser sections authorized for the requested lifecycle view."""
    from academics.models import Section, TeacherAssignment

    if not user or not getattr(user, 'is_authenticated', False):
        return Section.objects.none()

    if get_user_scope(user) != 'teacher':
        return Section.objects.none()

    lifecycle_status = _lifecycle_status(lifecycle_status, include_archived)
    adviser_assignments = TeacherAssignment.objects.filter(
        teacher=user,
        assignment_type='ADVISER',
    ).values('section_id')
    if lifecycle_status == 'active':
        adviser_assignments = adviser_assignments.filter(is_active=True)
    elif lifecycle_status == 'archived':
        adviser_assignments = adviser_assignments.filter(is_active=False)

    sections = Section.objects.filter(
        models.Q(adviser=user) | models.Q(pk__in=adviser_assignments)
    ).distinct()
    if lifecycle_status == 'active':
        sections = sections.filter(is_active=True, grade_level__is_active=True, academic_year__is_active=True)
    elif lifecycle_status == 'archived':
        sections = sections.filter(
            models.Q(is_active=False) |
            models.Q(grade_level__is_active=False) |
            models.Q(academic_year__is_active=False)
        )
    return sections


def get_adviser_students(user: object, queryset: QuerySet | None = None, include_archived: bool = False) -> QuerySet:
    """Return students in the adviser's sections for the requested legacy scope."""
    from students.models import Student

    if queryset is None:
        queryset = Student.objects.all()

    if not user or not getattr(user, 'is_authenticated', False):
        return queryset.none()

    if get_user_scope(user) != 'teacher':
        return queryset.none()

    sections = get_adviser_sections(user, include_archived=include_archived)
    if not sections.exists():
        return queryset.none()
    if not include_archived:
        queryset = queryset.filter(student_status='active')
    return queryset.filter(enrollments__section__in=sections).distinct()


def teacher_section_queryset(user: object, lifecycle_status='active'):
    """Return sections where the teacher has an assignment in the requested lifecycle."""
    from academics.models import Section

    profile = _get_profile(user)
    lifecycle_status = _lifecycle_status(lifecycle_status)
    assignments = teacher_assignment_queryset(user, active_only=False)
    if lifecycle_status == 'active':
        assignments = assignments.filter(is_active=True)
    elif lifecycle_status == 'archived':
        assignments = assignments.filter(is_active=False)

    assigned_sections = profile.assigned_sections.values('pk') if profile and lifecycle_status != 'archived' else Section.objects.none().values('pk')
    sections = Section.objects.filter(
        models.Q(adviser=user) | models.Q(pk__in=assignments.values('section_id')) | models.Q(pk__in=assigned_sections)
    ).distinct()
    if lifecycle_status == 'active':
        sections = sections.filter(is_active=True, grade_level__is_active=True, academic_year__is_active=True)
    elif lifecycle_status == 'archived':
        sections = sections.filter(
            models.Q(is_active=False) |
            models.Q(grade_level__is_active=False) |
            models.Q(academic_year__is_active=False)
        )
    return sections


def authorized_students_queryset(user: object, queryset: QuerySet, include_archived: bool = False, lifecycle_status=None) -> QuerySet:
    """Return a queryset of Student objects authorized for the given user.

    Teachers see the union of adviser-authorized sections and the sections they
    are assigned as a subject teacher in the requested lifecycle scope.
    """
    from academics.models import Section

    lifecycle_status = _lifecycle_status(lifecycle_status or ('all' if include_archived else 'active'))
    if lifecycle_status == 'active':
        queryset = queryset.filter(student_status='active')
    scope = get_user_scope(user)
    if scope in {'schoolwide', 'registrar'}:
        return queryset
    if scope == 'teacher':
        adviser_sections = get_adviser_sections(user, lifecycle_status=lifecycle_status)
        subject_sections = teacher_section_queryset(user, lifecycle_status=lifecycle_status)
        # Preserve teacher-specific authorization without expanding to the whole school.
        authorized_sections = Section.objects.filter(
            models.Q(pk__in=adviser_sections.values('pk')) |
            models.Q(pk__in=subject_sections.values('pk'))
        ).distinct()
        if not authorized_sections.exists():
            return queryset.none()
        queryset = queryset.filter(enrollments__section__in=authorized_sections)
        if lifecycle_status == 'active':
            queryset = queryset.filter(enrollments__enrollment_status='active')
        return queryset.distinct()
    if scope == 'guidance':
        queryset = queryset.filter(enrollments__isnull=False)
        if not include_archived:
            queryset = queryset.filter(student_status='active')
        return queryset.distinct()
    return queryset.none()


def authorized_enrollment_queryset(user: object, queryset: QuerySet, enrollment_field: str = 'enrollment', lifecycle_status='active') -> QuerySet:
    """Return a queryset filtered by enrollment-related access for the user.

    Teachers receive a simple, scoped union of the sections coming from the
    adviser-level and subject-assignment authorization helpers, without dropping
    the active or archived lifecycle semantics already established elsewhere.
    """
    from academics.models import Section

    scope = get_user_scope(user)
    if scope in {'schoolwide', 'registrar'}:
        return queryset
    if scope == 'teacher':
        lifecycle_status = _lifecycle_status(lifecycle_status)
        adviser_sections = get_adviser_sections(user, lifecycle_status=lifecycle_status)
        subject_sections = teacher_section_queryset(user, lifecycle_status=lifecycle_status)
        sections = Section.objects.filter(
            models.Q(pk__in=adviser_sections.values('pk')) |
            models.Q(pk__in=subject_sections.values('pk'))
        ).distinct()
        if not sections.exists():
            return queryset.none()
        model_fields = {f.name for f in queryset.model._meta.get_fields()}
        if enrollment_field and '__' in enrollment_field:
            root = enrollment_field.split('__', 1)[0]
            if root in model_fields:
                filter_kw = {f'{enrollment_field}__section__in': sections}
            else:
                filter_kw = {'section__in': sections}
        elif enrollment_field and enrollment_field in model_fields:
            filter_kw = {f'{enrollment_field}__section__in': sections}
        else:
            filter_kw = {'section__in': sections}
        return queryset.filter(**filter_kw).distinct()
    if scope == 'guidance':
        return queryset
    return queryset.none()


def active_enrollment_queryset(queryset: QuerySet) -> QuerySet:
    """Return current operational enrollments without removing historical rows."""
    return queryset.filter(
        student__student_status='active',
        enrollment_status='active',
        academic_year__is_active=True,
        grade_level__is_active=True,
        section__is_active=True,
        section__academic_year__is_active=True,
    )


def archived_enrollment_queryset(queryset: QuerySet) -> QuerySet:
    """Return enrollments outside the current operational context for history views."""
    return queryset.exclude(
        student__student_status='active',
        enrollment_status='active',
        academic_year__is_active=True,
        grade_level__is_active=True,
        section__is_active=True,
        section__academic_year__is_active=True,
    )

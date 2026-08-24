from typing import Iterable
from django.db import models
from django.db.models import QuerySet


def _get_profile(user):
    try:
        return getattr(user, 'profile', None)
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


def get_adviser_sections(user: object):
    """Return the active sections assigned to the teacher as a class adviser."""
    from academics.models import Section, TeacherAssignment

    if not user or not getattr(user, 'is_authenticated', False):
        return Section.objects.none()

    if get_user_scope(user) != 'teacher':
        return Section.objects.none()

    adviser_assignments = TeacherAssignment.objects.filter(
        teacher=user,
        assignment_type='ADVISER',
        is_active=True,
    ).values('section_id')

    return Section.objects.filter(
        is_active=True,
        grade_level__is_active=True,
        academic_year__is_active=True,
    ).filter(
        models.Q(adviser=user) | models.Q(pk__in=adviser_assignments)
    ).distinct()


def get_adviser_students(user: object, queryset: QuerySet | None = None) -> QuerySet:
    """Return only students enrolled in active sections assigned to the adviser."""
    from students.models import Student

    if queryset is None:
        queryset = Student.objects.all()

    if not user or not getattr(user, 'is_authenticated', False):
        return queryset.none()

    if get_user_scope(user) != 'teacher':
        return queryset.none()

    sections = get_adviser_sections(user)
    if not sections.exists():
        return queryset.none()
    return queryset.filter(enrollments__section__in=sections).filter(enrollments__enrollment_status='active').distinct()


def teacher_section_queryset(user: object):
    """Return sections where the teacher teaches or is the adviser."""
    from academics.models import Section

    profile = _get_profile(user)
    assigned_sections = profile.assigned_sections.values('pk') if profile else Section.objects.none().values('pk')
    assignments = teacher_assignment_queryset(user).values('section_id')
    return Section.objects.filter(
        models.Q(adviser=user) | models.Q(pk__in=assignments) | models.Q(pk__in=assigned_sections)
    ).distinct()


def authorized_students_queryset(user: object, queryset: QuerySet) -> QuerySet:
    """Return a queryset of Student objects authorized for the given user."""
    scope = get_user_scope(user)
    if scope in {'schoolwide', 'registrar'}:
        return queryset
    if scope == 'teacher':
        adviser_sections = get_adviser_sections(user)
        if adviser_sections.exists():
            return queryset.filter(enrollments__section__in=adviser_sections).filter(enrollments__enrollment_status='active').distinct()

        profile = _get_profile(user)
        if not profile:
            return queryset.none()
        sections = teacher_section_queryset(user)
        return queryset.filter(enrollments__section__in=sections).distinct()
    if scope == 'guidance':
        return queryset.filter(enrollments__isnull=False).distinct()
    return queryset.none()


def authorized_enrollment_queryset(user: object, queryset: QuerySet, enrollment_field: str = 'enrollment') -> QuerySet:
    """Return a queryset filtered by enrollment-related access for the user.

    The function expects `queryset` to be a queryset of objects that either are
    enrollments or reference enrollments via a foreign key. The `enrollment_field`
    parameter controls the lookup prefix (e.g. 'enrollment' or 'prediction__enrollment').
    """
    scope = get_user_scope(user)
    if scope in {'schoolwide', 'registrar'}:
        return queryset
    if scope == 'teacher':
        adviser_sections = get_adviser_sections(user)
        sections = adviser_sections if adviser_sections.exists() else teacher_section_queryset(user)
        # Determine if the queryset is already Enrollment-like (has 'section' field)
        model_fields = {f.name for f in queryset.model._meta.get_fields()}
        # If enrollment_field refers to a related lookup like 'prediction__enrollment',
        # check whether the root relation exists on the model (e.g., 'prediction').
        if enrollment_field and '__' in enrollment_field:
            root = enrollment_field.split('__', 1)[0]
            if root in model_fields:
                filter_kw = {f'{enrollment_field}__section__in': sections}
            else:
                filter_kw = {'section__in': sections}
        elif enrollment_field and enrollment_field in model_fields:
            filter_kw = {f'{enrollment_field}__section__in': sections}
        else:
            # Assume the queryset refers to Enrollment or has direct 'section' FK
            filter_kw = {'section__in': sections}
        return queryset.filter(**filter_kw).distinct()
    if scope == 'guidance':
        return queryset
    return queryset.none()

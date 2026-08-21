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
        profile = _get_profile(user)
        if not profile:
            return queryset.none()
        sections = teacher_section_queryset(user)
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

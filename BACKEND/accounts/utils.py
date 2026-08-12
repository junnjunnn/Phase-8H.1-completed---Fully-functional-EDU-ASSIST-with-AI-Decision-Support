"""Compatibility wrappers that forward to centralized authorization helpers.

This module preserves the original function names expected by other apps
but delegates implementation to `common.authorization` for a single source
of truth. Maintain API compatibility while improving testability.
"""

from common.authorization import (
    get_user_scope as _get_user_scope,
    authorized_students_queryset as _authorized_students_queryset,
    authorized_enrollment_queryset as _authorized_enrollment_queryset,
)


def get_user_scope(user):
    return _get_user_scope(user)


def get_authorized_student_queryset(user, queryset):
    return _authorized_students_queryset(user, queryset)


def get_authorized_enrollment_queryset(user, queryset, enrollment_field='enrollment'):
    return _authorized_enrollment_queryset(user, queryset, enrollment_field=enrollment_field)

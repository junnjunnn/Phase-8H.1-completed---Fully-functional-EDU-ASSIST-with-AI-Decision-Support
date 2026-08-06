def get_user_scope(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return 'none'
    try:
        profile = user.profile
    except Exception:
        return 'none'
    role_name = profile.role_name if profile else 'NONE'
    if role_name in {'SUPER_ADMIN', 'SCHOOL_ADMIN'}:
        return 'schoolwide'
    if role_name == 'TEACHER':
        return 'teacher'
    if role_name == 'GUIDANCE':
        return 'guidance'
    return 'none'


def get_authorized_student_queryset(user, queryset):
    scope = get_user_scope(user)
    if scope == 'schoolwide':
        return queryset
    if scope == 'teacher':
        try:
            sections = user.profile.assigned_sections.all()
        except Exception:
            return queryset.none()
        return queryset.filter(enrollments__section__in=sections).distinct()
    if scope == 'guidance':
        return queryset.filter(enrollments__isnull=False).distinct()
    return queryset.none()


def get_authorized_enrollment_queryset(user, queryset, enrollment_field='enrollment'):
    scope = get_user_scope(user)
    if scope == 'schoolwide':
        return queryset
    if scope == 'teacher':
        try:
            sections = user.profile.assigned_sections.all()
        except Exception:
            return queryset.none()
        if hasattr(queryset.model, 'section'):
            return queryset.filter(section__in=sections).distinct()
        filter_kw = {f'{enrollment_field}__section__in': sections}
        return queryset.filter(**filter_kw).distinct()
    if scope == 'guidance':
        return queryset
    return queryset.none()

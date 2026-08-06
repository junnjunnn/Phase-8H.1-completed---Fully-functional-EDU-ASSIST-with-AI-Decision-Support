from rest_framework.permissions import BasePermission


def _get_role_name(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return user.profile.role_name
    except Exception:
        return None


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) == 'SUPER_ADMIN'


class IsSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN'}


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) == 'TEACHER'


class IsGuidancePersonnel(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) == 'GUIDANCE'


class IsTeacherOrSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER'}


class IsAuthorizedStaff(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'}

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


class IsRegistrar(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) == 'REGISTRAR'


class IsTeacherOrSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER'}


class IsRegistrarOrSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'REGISTRAR'}


class IsAuthorizedStaff(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'}


class IsAcademicReferenceAccessAllowed(BasePermission):
    """Permission for reading academic reference data (years, grades, strands, sections, subjects).
    
    Allows registrar to READ reference data for enrollment wizard, but not CREATE/UPDATE/DELETE.
    """
    def has_permission(self, request, view):
        role = _get_role_name(request.user)
        # All staff can read reference data
        if role in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE', 'REGISTRAR'}:
            return True
        return False


class IsStudentAccessAllowed(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE', 'REGISTRAR'}


class IsEnrollmentAccessAllowed(BasePermission):
    def has_permission(self, request, view):
        return _get_role_name(request.user) in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE', 'REGISTRAR'}

from rest_framework.filters import BaseFilterBackend

from .authorization import authorized_enrollment_queryset, authorized_students_queryset


class RoleScopedFilterBackend(BaseFilterBackend):
    """DRF filter backend that applies role-based scoping.

    Views may set `scope_for_model = 'students'` or `scope_field = 'enrollment'`.
    If neither is set, the backend is a no-op.
    """

    def filter_queryset(self, request, queryset, view):
        scope_field = getattr(view, 'scope_field', None)
        scope_for_model = getattr(view, 'scope_for_model', None)

        # Students model convenience
        if scope_for_model == 'students':
            return authorized_students_queryset(request.user, queryset)

        if scope_field:
            return authorized_enrollment_queryset(request.user, queryset, enrollment_field=scope_field)

        return queryset


class RoleScopedViewsetMixin:
    """Mixin for viewsets to apply scoping via attribute `scope_field`.

    Example:
      class MyViewSet(RoleScopedViewsetMixin, viewsets.ModelViewSet):
          scope_field = 'enrollment'
    """

    scope_field = None

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.scope_field:
            return qs
        return authorized_enrollment_queryset(self.request.user, qs, enrollment_field=self.scope_field)

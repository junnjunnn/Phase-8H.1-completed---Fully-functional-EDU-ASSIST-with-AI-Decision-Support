from audit.models import AuditLog


class AuditMixin:
    """Mixin to standardize audit log creation for DRF viewsets.

    Inherit this mixin in viewsets to automatically emit audit records for
    create/update/destroy operations. The mixin expects the view's
    `serializer_class.Meta.model` to be present to compute `module` and
    `object_type` metadata similar to existing code.
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        try:
            AuditLog.objects.create(
                user=self.request.user if getattr(self.request, 'user', None) and self.request.user.is_authenticated else None,
                action='CREATE',
                module=self.serializer_class.Meta.model._meta.app_label,
                object_type=self.serializer_class.Meta.model.__name__,
                object_id=str(instance.pk),
            )
        except Exception:
            # Audit logging must never break the main flow.
            pass

    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            AuditLog.objects.create(
                user=self.request.user if getattr(self.request, 'user', None) and self.request.user.is_authenticated else None,
                action='UPDATE',
                module=self.serializer_class.Meta.model._meta.app_label,
                object_type=self.serializer_class.Meta.model.__name__,
                object_id=str(instance.pk),
            )
        except Exception:
            pass

    def perform_destroy(self, instance):
        try:
            AuditLog.objects.create(
                user=self.request.user if getattr(self.request, 'user', None) and self.request.user.is_authenticated else None,
                action='DELETE',
                module=self.serializer_class.Meta.model._meta.app_label,
                object_type=self.serializer_class.Meta.model.__name__,
                object_id=str(instance.pk),
            )
        except Exception:
            pass
        instance.delete()

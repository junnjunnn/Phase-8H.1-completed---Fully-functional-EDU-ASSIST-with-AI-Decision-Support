from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, response, viewsets
from rest_framework.decorators import action

from .models import Notification
from .serializers import NotificationSerializer
from .services import generate_notifications_for_user


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()
        return Notification.objects.filter(
            recipient=self.request.user,
            scheduled_for__lte=now,
            calendar_entry__status__in=['PENDING_APPROVAL', 'APPROVED', 'PUBLISHED'],
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
        ).select_related('calendar_entry', 'recurring_event')

    def list(self, request, *args, **kwargs):
        generate_notifications_for_user(request.user)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.read_at:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])
        return response.Response(self.get_serializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return response.Response({'updated': updated})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        generate_notifications_for_user(request.user)
        return response.Response({'count': self.get_queryset().filter(read_at__isnull=True).count()})
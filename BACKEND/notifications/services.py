from datetime import datetime, time, timedelta

from django.db import IntegrityError
from django.utils import timezone

from common.authorization import teacher_section_queryset
from attendance.models import SchoolCalendarDay

from .models import Notification


PUBLISHED_STATUSES = {'APPROVED', 'PUBLISHED'}
SUPPRESSED_STATUSES = {'CANCELLED', 'REJECTED', 'ARCHIVED'}


def _scheduled_for(event_date, now):
    reminder_date = event_date - timedelta(days=1)
    reminder = timezone.make_aware(datetime.combine(reminder_date, time(9, 0)))
    return min(reminder, now) if reminder <= now else reminder


def _is_authorized_for_event(user, event):
    role = getattr(getattr(user, 'profile', None), 'role_name', None)
    if role in {'SUPER_ADMIN', 'SCHOOL_ADMIN', 'REGISTRAR', 'GUIDANCE'}:
        return True
    if role != 'TEACHER' or event.status != 'PUBLISHED':
        return False
    if event.instructor_id == user.id:
        return True
    sections = teacher_section_queryset(user)
    if event.scope_type == 'SCHOOL_WIDE':
        return True
    if event.scope_type == 'SECTION_SPECIFIC':
        return sections.filter(pk=event.section_id).exists()
    if event.scope_type == 'GRADE_LEVEL':
        return sections.filter(grade_level_id=event.affected_grade_level_id).exists()
    if event.scope_type == 'DEPARTMENT':
        return getattr(user.profile, 'department', '').strip().casefold() == event.affected_department.strip().casefold()
    return False


def _notification_type(event):
    if event.day_type == 'EXAMINATION':
        return 'EXAMINATION'
    if event.day_type == 'ENROLLMENT' and event.event_type in {'ENROLLMENT_DEADLINE', 'LATE_ENROLLMENT'}:
        return 'ENROLLMENT_DEADLINE'
    if event.day_type == 'ACADEMIC_DEADLINE':
        return 'ACADEMIC_DEADLINE'
    if event.day_type == 'SUSPENSION' or event.classes_suspended:
        return 'SUSPENSION'
    return 'CALENDAR_EVENT'


def _create_notification(user, event, notification_type, scheduled_for, key, title, message):
    try:
        return Notification.objects.get_or_create(
            idempotency_key=key,
            defaults={
                'recipient': user,
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'calendar_entry': event,
                'recurring_event': event.recurrence,
                'scheduled_for': scheduled_for,
                'expires_at': timezone.make_aware(datetime.combine((event.end_date or event.calendar_date) + timedelta(days=1), time(0))),
            },
        )
    except IntegrityError:
        return Notification.objects.get(idempotency_key=key), False


def generate_notifications_for_user(user, now=None, lookahead_days=7):
    if not user or not user.is_authenticated:
        return 0
    now = now or timezone.now()
    today = timezone.localdate(now)
    horizon = today + timedelta(days=lookahead_days)
    created = 0

    pending = SchoolCalendarDay.objects.filter(status='PENDING_APPROVAL').select_related('recurrence')
    for event in pending:
        if event.created_by_id == user.id:
            continue
        if getattr(getattr(user, 'profile', None), 'role_name', None) not in {'SUPER_ADMIN', 'SCHOOL_ADMIN'}:
            continue
        _, was_created = _create_notification(
            user, event, 'APPROVAL_PENDING', now, f'approval:{user.id}:{event.id}',
            'Calendar event pending approval', f'{event.title} is awaiting approval.',
        )
        created += int(was_created)

    events = SchoolCalendarDay.objects.filter(
        status__in=PUBLISHED_STATUSES,
        calendar_date__gte=today,
        calendar_date__lte=horizon,
    ).exclude(status__in=SUPPRESSED_STATUSES).select_related('recurrence')
    for event in events:
        if not _is_authorized_for_event(user, event):
            continue
        notification_type = _notification_type(event)
        scheduled_for = _scheduled_for(event.calendar_date, now)
        _, was_created = _create_notification(
            user, event, notification_type, scheduled_for,
            f'calendar:{user.id}:{event.id}:{notification_type}',
            f'Upcoming: {event.title}', f'{event.title} is scheduled for {event.calendar_date.strftime("%B %d, %Y")}.',
        )
        created += int(was_created)
    return created
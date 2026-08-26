import calendar
from datetime import date, timedelta

from django.db import transaction

from .models import RecurringSchoolCalendarEvent, SchoolCalendarDay


def _monthly_date(year, month, weekday, week):
    month_days = calendar.monthcalendar(year, month)
    candidates = [days[weekday] for days in month_days if days[weekday]]
    if week == -1:
        return date(year, month, candidates[-1])
    if week <= len(candidates):
        return date(year, month, candidates[week - 1])
    return None


def occurrence_dates(event):
    current = event.start_date
    end = event.recurrence_end_date
    if event.frequency in {'WEEKLY', 'MONTHLY'}:
        while current.weekday() != event.recurrence_weekday:
            current += timedelta(days=1)
            if current > end:
                return

    if event.frequency in {'DAILY', 'CUSTOM'}:
        step = timedelta(days=event.recurrence_interval)
        while current <= end:
            yield current
            current += step
    elif event.frequency == 'WEEKLY':
        step = timedelta(weeks=event.recurrence_interval)
        while current <= end:
            yield current
            current += step
    elif event.frequency == 'MONTHLY':
        cursor = date(current.year, current.month, 1)
        while cursor <= end:
            occurrence = _monthly_date(cursor.year, cursor.month, event.recurrence_weekday, event.recurrence_week)
            if occurrence and event.start_date <= occurrence <= end:
                yield occurrence
            cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)
    elif event.frequency == 'YEARLY':
        for year in range(event.start_date.year, end.year + 1):
            try:
                occurrence = date(year, event.recurrence_month, event.recurrence_month_day)
            except ValueError:
                continue
            if event.start_date <= occurrence <= end:
                yield occurrence


@transaction.atomic
def generate_occurrences(event):
    if not event.active:
        return 0
    created = 0
    for calendar_date in occurrence_dates(event):
        _, was_created = SchoolCalendarDay.objects.get_or_create(
            recurrence=event,
            calendar_date=calendar_date,
            defaults={
                'academic_year': event.academic_year,
                'day_type': event.day_type,
                'title': event.title,
                'remarks': event.remarks,
                'attendance_expected': event.attendance_expected,
                'classes_suspended': event.classes_suspended,
                'scope_type': event.scope_type,
                'section': event.section,
                'affected_grade_level': event.affected_grade_level,
                'affected_department': event.affected_department,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'location': event.location,
                'organizer': event.organizer,
                'target_participants': event.target_participants,
                'created_by': event.created_by,
                'status': 'DRAFT',
            },
        )
        created += int(was_created)
    return created
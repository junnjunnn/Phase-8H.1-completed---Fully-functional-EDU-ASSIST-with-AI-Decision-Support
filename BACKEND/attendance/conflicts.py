from django.db.models import Q

from .models import SchoolCalendarDay


BLOCKING_CONFLICT_TYPES = {'LOCATION_CONFLICT', 'SECTION_CONFLICT', 'SCOPE_CONFLICT'}
IGNORED_STATUSES = {'CANCELLED', 'ARCHIVED'}


def _date_range(event):
    start = event.calendar_date
    end = event.end_date or start
    return start, end


def _times_overlap(candidate, existing):
    if not candidate.start_time or not candidate.end_time or not existing.start_time or not existing.end_time:
        return False
    return candidate.start_time < existing.end_time and existing.start_time < candidate.end_time


def _scope_overlaps(candidate, existing):
    if candidate.scope_type == 'SCHOOL_WIDE' or existing.scope_type == 'SCHOOL_WIDE':
        return True
    if candidate.scope_type == 'SECTION_SPECIFIC' and existing.scope_type == 'SECTION_SPECIFIC':
        return candidate.section_id == existing.section_id
    if candidate.scope_type == 'GRADE_LEVEL' and existing.scope_type == 'GRADE_LEVEL':
        return candidate.affected_grade_level_id == existing.affected_grade_level_id
    if candidate.scope_type == 'DEPARTMENT' and existing.scope_type == 'DEPARTMENT':
        return candidate.affected_department.strip().casefold() == existing.affected_department.strip().casefold()
    if candidate.scope_type == 'TIME_SPECIFIC' and existing.scope_type == 'TIME_SPECIFIC':
        return True
    return False


def _conflict_types(candidate, existing):
    if not _times_overlap(candidate, existing):
        return []

    types = ['TIME_OVERLAP']
    if candidate.location and existing.location and candidate.location.strip().casefold() == existing.location.strip().casefold():
        types.append('LOCATION_CONFLICT')
    if candidate.section_id and existing.section_id and candidate.section_id == existing.section_id:
        types.append('SECTION_CONFLICT')
    if _scope_overlaps(candidate, existing):
        types.append('SCOPE_CONFLICT')
    return types


def detect_conflicts(candidate, queryset=None):
    start_date, end_date = _date_range(candidate)
    if not start_date or not candidate.academic_year:
        return []

    queryset = queryset or SchoolCalendarDay.objects.select_related('section', 'affected_grade_level')
    queryset = queryset.filter(
        academic_year=candidate.academic_year,
        calendar_date__lte=end_date,
    ).filter(
        Q(end_date__gte=start_date)
        | Q(end_date__isnull=True, calendar_date__gte=start_date)
    ).exclude(status__in=IGNORED_STATUSES)
    if getattr(candidate, 'pk', None):
        queryset = queryset.exclude(pk=candidate.pk)

    conflicts = []
    for existing in queryset.order_by('calendar_date', 'start_time', 'id'):
        conflict_types = _conflict_types(candidate, existing)
        if not conflict_types:
            continue
        conflicts.append({
            'event_id': existing.id,
            'title': existing.title,
            'date': existing.calendar_date,
            'end_date': existing.end_date,
            'start_time': existing.start_time,
            'end_time': existing.end_time,
            'location': existing.location,
            'scope_type': existing.scope_type,
            'section': existing.section_id,
            'affected_grade_level': existing.affected_grade_level_id,
            'affected_department': existing.affected_department,
            'conflict_types': conflict_types,
            'severity': 'ERROR' if set(conflict_types) & BLOCKING_CONFLICT_TYPES else 'WARNING',
        })
    return conflicts


def serialize_conflicts(conflicts):
    return [
        {
            **conflict,
            'recurrence_date': conflict['recurrence_date'].isoformat() if conflict.get('recurrence_date') else None,
            'date': conflict['date'].isoformat() if conflict['date'] else None,
            'end_date': conflict['end_date'].isoformat() if conflict['end_date'] else None,
            'start_time': conflict['start_time'].isoformat() if conflict['start_time'] else None,
            'end_time': conflict['end_time'].isoformat() if conflict['end_time'] else None,
        }
        for conflict in conflicts
    ]


def detect_recurring_conflicts(event):
    from types import SimpleNamespace

    from .recurrence import occurrence_dates

    conflicts = []
    for calendar_date in occurrence_dates(event):
        candidate = SimpleNamespace(
            pk=None,
            academic_year=event.academic_year,
            calendar_date=calendar_date,
            end_date=None,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            scope_type=event.scope_type,
            section_id=event.section_id,
            affected_grade_level_id=event.affected_grade_level_id,
            affected_department=event.affected_department,
        )
        for conflict in detect_conflicts(candidate):
            conflict['recurrence_date'] = calendar_date
            conflicts.append(conflict)
    return conflicts
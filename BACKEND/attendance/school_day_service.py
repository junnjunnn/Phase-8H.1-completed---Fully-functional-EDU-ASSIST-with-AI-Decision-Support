from datetime import date

from django.utils import timezone

from academics.models import AcademicYear

from .models import SchoolCalendarDay


def _parse_date(value):
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def get_school_day_summary(academic_year_id=None, reporting_date=None, today=None, include_archived=False):
    academic_years = AcademicYear.objects.all()
    if academic_year_id:
        requested_years = academic_years if include_archived else academic_years.filter(is_active=True)
        academic_year = requested_years.filter(pk=academic_year_id).first()
    else:
        academic_year = academic_years.filter(is_active=True).first()

    if not academic_year:
        return {'school_days': 0, 'academic_year': None, 'calendar_available': False}

    current_date = _parse_date(today) or timezone.localdate()
    requested_date = _parse_date(reporting_date)
    if requested_date:
        end_date = requested_date
    elif academic_year.is_active:
        end_date = min(current_date, academic_year.end_date)
    else:
        end_date = academic_year.end_date

    if end_date < academic_year.start_date:
        school_days = 0
    else:
        school_days = SchoolCalendarDay.get_expected_school_days(
            academic_year,
            start_date=academic_year.start_date,
            end_date=end_date,
        )

    return {
        'school_days': school_days,
        'academic_year': academic_year,
        'calendar_available': SchoolCalendarDay.objects.filter(academic_year=academic_year).exists(),
        'reporting_date': end_date,
    }